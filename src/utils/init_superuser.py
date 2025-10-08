import logging
from sqlalchemy import select
from models.user import User, UserRole
from core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def create_superuser():
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(User).where(User.email == "a@a.a")
            )
            existing_user = result.scalar_one_or_none()
            if existing_user:
                if existing_user.role != UserRole.ADMIN or not existing_user.is_superuser:
                    existing_user.role = UserRole.ADMIN
                    existing_user.is_superuser = True
                    existing_user.is_active = True
                    existing_user.is_verified = True
                    await session.commit()
                    logger.info("Суперпользователь обновлен до роли ADMIN: a@a.a")
                else:
                    logger.info("Суперпользователь уже существует с ролью ADMIN: a@a.a")
                return
            from fastapi_users.password import PasswordHelper
            password_helper = PasswordHelper()
            hashed_password = password_helper.hash("admin")
            superuser = User(
                email="a@a.a",
                hashed_password=hashed_password,
                first_name="admin",
                last_name="admin",
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
                is_superuser=True,
                team_id=None
            )
            session.add(superuser)
            await session.commit()
            logger.info("Суперпользователь успешно создан: a@a.a")
        except Exception as e:
            logger.error(f"Ошибка при создании суперпользователя: {e}")
            await session.rollback()
