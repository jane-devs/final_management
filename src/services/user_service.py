import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from fastapi_users.password import PasswordHelper

from models.user import User, UserRole
from utils.validation import (
    validate_email_format,
    validate_email_unique,
    validate_name_field,
    validate_password_strength,
    validate_passwords_match
)


class UserService:
    """Сервис для управления пользователями."""

    @staticmethod
    async def register_user(
        session: AsyncSession,
        email: str,
        password: str,
        password_confirm: str,
        first_name: str,
        last_name: str
    ) -> User:
        """
        Регистрирует нового пользователя с валидацией.

        Args:
            session: Сессия базы данных
            email: Email
            password: Пароль
            password_confirm: Подтверждение пароля
            first_name: Имя
            last_name: Фамилия

        Returns:
            User: Созданный пользователь
        """
        validate_passwords_match(password, password_confirm)
        email = validate_email_format(email)
        await validate_email_unique(session, email)
        password = validate_password_strength(password)
        first_name = validate_name_field(first_name, "Имя")
        last_name = validate_name_field(last_name, "Фамилия")

        password_helper = PasswordHelper()
        hashed_password = password_helper.hash(password)

        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            hashed_password=hashed_password,
            role=UserRole.USER,
            is_active=True,
            is_verified=True
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

        return user

    @staticmethod
    async def update_profile(
        session: AsyncSession,
        user_id: uuid.UUID,
        email: str,
        first_name: str,
        last_name: str
    ) -> User:
        """
        Обновляет профиль пользователя с валидацией.

        Args:
            session: Сессия базы данных
            user_id: ID пользователя
            email: Email
            first_name: Имя
            last_name: Фамилия

        Returns:
            User: Обновленный пользователь
        """
        user_result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one()

        email = validate_email_format(email)
        first_name = validate_name_field(first_name, "Имя")
        last_name = validate_name_field(last_name, "Фамилия")

        if email != user.email:
            await validate_email_unique(
                session, email, exclude_user_id=user.id)

        user.email = email
        user.first_name = first_name
        user.last_name = last_name

        await session.commit()
        return user

    @staticmethod
    async def change_password(
        session: AsyncSession,
        user_id: uuid.UUID,
        current_password: str,
        new_password: str,
        new_password_confirm: str
    ) -> User:
        """
        Изменяет пароль пользователя с валидацией.

        Args:
            session: Сессия базы данных
            user_id: ID пользователя
            current_password: Текущий пароль
            new_password: Новый пароль
            new_password_confirm: Подтверждение нового пароля

        Returns:
            User: Пользователь с обновленным паролем
        """
        user_result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one()

        password_helper = PasswordHelper()

        if not password_helper.verify_and_update(
            current_password, user.hashed_password
        )[0]:
            raise HTTPException(
                status_code=400, detail="Неверный текущий пароль")

        validate_passwords_match(new_password, new_password_confirm)
        new_password = validate_password_strength(new_password)

        user.hashed_password = password_helper.hash(new_password)
        await session.commit()

        return user
