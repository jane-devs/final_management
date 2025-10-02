import uuid
from typing import Optional
from fastapi import Depends, Request, Response
from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from core.database import get_async_session
from core.config import settings
from core.exceptions import (
    UserAlreadyExists, WeakPassword, UserNotActive
)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """Менеджер пользователей для fastapi-users с кастомными исключениями."""
    reset_password_token_secret = settings.secret_key
    verification_token_secret = settings.secret_key

    async def validate_password(
        self,
        password: str,
        user: User | None = None,
    ) -> None:
        """Валидация пароля с кастомными исключениями"""
        if len(password) < 8:
            raise WeakPassword("минимум 8 символов")

        if password.isdigit() or password.isalpha():
            raise WeakPassword("должен содержать буквы и цифры")

        if user and user.email.lower() in password.lower():
            raise WeakPassword("не должен содержать email")

    async def on_after_register(
            self, user: User,
            request: Request | None = None, response: Response | None = None
    ):
        """Действие после успешной регистрации"""
        print(f"Пользователь {user.email} зарегистрировался. ID: {user.id}")

    async def on_after_login(
            self, user: User,
            request: Request | None = None, response: Response | None = None
    ):
        """Действие после успешного входа"""
        if not user.is_active:
            raise UserNotActive()
        if not user.is_verified:
            print(f"Внимание: пользователь {user.email} не верифицирован")
        print(f"Пользователь {user.email} вошел в систему")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Действие после запроса сброса пароля"""
        print(f"Пользователь {user.email} запросил сброс пароля. Токен: {token}") # noqa

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Действие после запроса верификации"""
        print(f"Верификация запрошена для {user.email}. Токен: {token}")

    async def create(
        self,
        user_create,
        safe: bool = False,
        request: Optional[Request] = None,
    ) -> User:
        """Создание пользователя с кастомной валидацией"""
        existing_user = await self.user_db.get_by_email(user_create.email)
        if existing_user:
            raise UserAlreadyExists(user_create.email)
        await self.validate_password(user_create.password)
        return await super().create(user_create, safe, request)


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    """Получение экземпляра базы данных пользователей"""
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(
        user_db: SQLAlchemyUserDatabase = Depends(get_user_db)
):
    """Получение менеджера пользователей"""
    yield UserManager(user_db)
