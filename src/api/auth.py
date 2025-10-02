import uuid
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from core.dependencies import require_verified_user, require_admin_only
from core.exceptions import UserNotFound, PermissionDenied
from core.fastapi_users import fastapi_users, auth_backend
from schemas.user import UserRead, UserCreate
from models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

# Стандартные роутеры fastapi-users
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
)

router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/jwt",
)

router.include_router(
    fastapi_users.get_reset_password_router(),
)

router.include_router(
    fastapi_users.get_verify_router(UserRead),
)


# Кастомные эндпоинты с улучшенной валидацией
@router.get("/me", response_model=UserRead)
async def get_current_user(
    current_user: User = Depends(require_verified_user)
):
    """Получить информацию о текущем пользователе (только верифицированные)"""
    return current_user


@router.get("/users", response_model=list[UserRead])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    admin_user: User = Depends(require_admin_only),
    session: AsyncSession = Depends(get_async_session)
):
    """Получить список всех пользователей (только админы)"""
    result = await session.execute(
        select(User).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.patch("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    admin_user: User = Depends(require_admin_only),
    session: AsyncSession = Depends(get_async_session)
):
    """Активировать пользователя (только админы)"""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise UserNotFound(user_id)

    result = await session.execute(
        select(User).where(User.id == user_uuid)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise UserNotFound(user_id)

    user.is_active = True
    await session.commit()

    return {"message": f"Пользователь {user.email} активирован"}


@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    admin_user: User = Depends(require_admin_only),
    session: AsyncSession = Depends(get_async_session)
):
    """Деактивировать пользователя (только админы)"""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise UserNotFound(user_id)

    result = await session.execute(
        select(User).where(User.id == user_uuid)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise UserNotFound(user_id)

    # Не позволяем деактивировать самого себя
    if user.id == admin_user.id:
        raise PermissionDenied("Нельзя деактивировать самого себя")

    user.is_active = False
    await session.commit()

    return {"message": f"Пользователь {user.email} деактивирован"}


@router.get("/profile", response_model=UserRead)
async def get_user_profile(
    current_user: User = Depends(require_verified_user)
):
    """Получить расширенный профиль пользователя"""
    return current_user
