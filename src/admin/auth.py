from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from sqlalchemy import select

from core.config import settings
from core.database import AsyncSessionLocal
from models.user import User, UserRole


class AdminAuthBackend(AuthenticationBackend):
    """Аутентификация админки от sqladmin."""
    async def login(self, request: Request) -> bool:
        form = await request.form()
        email = form.get("username")
        password = form.get("password")
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            if not user or user.role != UserRole.ADMIN:
                return False
            from fastapi_users.password import PasswordHelper
            password_helper = PasswordHelper()
            if not password_helper.verify_and_update(
                password, user.hashed_password
            )[0]:
                return False
            if not user.is_active:
                return False
            request.session.update({"user_id": str(user.id)})
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        user_id = request.session.get("user_id")
        if not user_id:
            return False
        async with AsyncSessionLocal() as session:
            try:
                import uuid
                user_uuid = uuid.UUID(user_id)
            except (ValueError, AttributeError):
                return False
            result = await session.execute(
                select(User).where(User.id == user_uuid)
            )
            user = result.scalar_one_or_none()
            if not user or user.role != UserRole.ADMIN or not user.is_active:
                return False
        return True


authentication_backend = AdminAuthBackend(secret_key=settings.secret_key)
