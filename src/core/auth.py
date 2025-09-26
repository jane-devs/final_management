from typing import Optional
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, IntegerIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTAuthentication,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.orm import Session

from app.models.user import User
from app.database import get_db
from app.config import settings

SECRET = settings.secret_key


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    """
    Менеджер пользователей для fastapi-users с Integer ID.
    Управляет регистрацией, аутентификацией и другими операциями с пользователями.
    """
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """Вызывается после успешной регистрации пользователя"""
        print(f"Пользователь {user.email} зарегистрировался.")

    async def on_after_login(self, user: User, request: Optional[Request] = None):
        """Вызывается после успешного входа пользователя"""
        print(f"Пользователь {user.email} вошел в систему.")


def get_user_db(session: Session = Depends(get_db)):
    """Получение экземпляра базы данных пользователей"""
    yield SQLAlchemyUserDatabase(session, User)


def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    """Получение менеджера пользователей"""
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

jwt_authentication = JWTAuthentication(
    secret=SECRET,
    lifetime_seconds=3600,  # Токен живет 1 час
)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=lambda: jwt_authentication,
)

fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
