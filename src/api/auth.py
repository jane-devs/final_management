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

router = APIRouter(prefix="/auth", tags=["Аутентификация"])

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


@router.get(
    "/me",
    response_model=UserRead,
    summary="Текущий пользователь",
    description="Получить информацию о текущем пользователе (только верифицированные)"
)
async def get_current_user(
    current_user: User = Depends(require_verified_user)
):
    return current_user


@router.get(
    "/users",
    response_model=list[UserRead],
    summary="Список пользователей",
    description="Получить список всех пользователей (только админы)"
)
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    admin_user: User = Depends(require_admin_only),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(User).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.patch(
    "/users/{user_id}/activate",
    summary="Активировать пользователя",
    description="Активировать пользователя (только админы)"
)
async def activate_user(
    user_id: str,
    admin_user: User = Depends(require_admin_only),
    session: AsyncSession = Depends(get_async_session)
):
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


@router.patch(
    "/users/{user_id}/deactivate",
    summary="Деактивировать пользователя",
    description="Деактивировать пользователя (только админы)"
)
async def deactivate_user(
    user_id: str,
    admin_user: User = Depends(require_admin_only),
    session: AsyncSession = Depends(get_async_session)
):
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

    if user.id == admin_user.id:
        raise PermissionDenied("Нельзя деактивировать самого себя")

    user.is_active = False
    await session.commit()

    return {"message": f"Пользователь {user.email} деактивирован"}


@router.get(
    "/profile",
    response_model=UserRead,
    summary="Профиль пользователя",
    description="Получить расширенный профиль пользователя"
)
async def get_user_profile(
    current_user: User = Depends(require_verified_user)
):
    return current_user
