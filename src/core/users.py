import uuid
from typing import Optional
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from database import get_async_session
from config import settings


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """
    Менеджер пользователей для fastapi-users.
    """
    reset_password_token_secret = settings.secret_key
    verification_token_secret = settings.secret_key

    async def on_after_register(
            self, user: User, request: Optional[Request] = None
        ):
        """Действие после успешной регистрации"""
        print(f"Пользователь {user.email} зарегистрировался. ID: {user.id}")

    async def on_after_login(
            self, user: User, request: Optional[Request] = None
        ):
        """Действие после успешного входа"""
        print(f"Пользователь {user.email} вошел в систему")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Действие после запроса сброса пароля"""
        print(f"Пользователь {user.email} запросил сброс пароля. Токен: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Действие после запроса верификации"""
        print(f"Верификация запрошена для {user.email}. Токен: {token}")


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    """Получение экземпляра базы данных пользователей"""
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(
        user_db: SQLAlchemyUserDatabase = Depends(get_user_db)
):
    """Получение менеджера пользователей"""
    yield UserManager(user_db)
