import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from core.fastapi_users import current_active_user
from core.dependencies import require_admin
from core.exceptions import UserNotFound, PermissionDenied
from models.user import User, UserRole
from schemas.user import UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["Пользователи"])


@router.get(
    "/me",
    response_model=UserRead,
    summary="Мой профиль",
    description="Получить свой профиль"
)
async def get_me(
    current_user: User = Depends(current_active_user)
):
    return current_user


@router.patch(
    "/me",
    response_model=UserRead,
    summary="Обновить профиль",
    description="Обновить свой профиль (нельзя менять роль и команду)"
)
async def update_me(
    user_update: UserUpdate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    if user_update.role is not None and current_user.role != UserRole.ADMIN:
        raise PermissionDenied("Вы не можете изменить свою роль")

    if user_update.team_id is not None and current_user.role != UserRole.ADMIN:
        raise PermissionDenied("Вы не можете изменить свою команду напрямую")

    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)

    await session.commit()
    await session.refresh(current_user)
    return current_user


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Получить пользователя",
    description="Получить пользователя по ID"
)
async def get_user(
    user_id: str,
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

    return user


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    summary="Обновить пользователя",
    description="Обновить пользователя (только сам пользователь или админ)"
)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(current_active_user),
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

    if user.id != current_user.id and current_user.role != UserRole.ADMIN:
        raise PermissionDenied("Вы можете редактировать только свой профиль")

    if current_user.role != UserRole.ADMIN:
        if user_update.role is not None:
            raise PermissionDenied("Вы не можете изменить роль пользователя")
        if user_update.team_id is not None:
            raise PermissionDenied("Вы не можете изменить команду пользователя")

    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await session.commit()
    await session.refresh(user)
    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить пользователя",
    description="Удалить пользователя (только админы)"
)
async def delete_user(
    user_id: str,
    admin_user: User = Depends(require_admin),
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
        raise PermissionDenied("Вы не можете удалить самого себя")

    await session.delete(user)
    await session.commit()


@router.patch(
    "/{user_id}/role",
    response_model=UserRead,
    summary="Назначить роль",
    description="Назначить роль пользователю (только админы, менеджер в команде может быть только один)"
)
async def assign_role(
    user_id: str,
    role_data: dict,
    admin_user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session)
):
    from models.user import UserRole

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

    try:
        new_role = UserRole(role_data.get("role"))
    except (ValueError, KeyError):
        raise PermissionDenied("Неверная роль. Доступные роли: user, manager, admin")

    if new_role == UserRole.MANAGER and user.team_id:
        existing_manager = await session.execute(
            select(User).where(
                User.team_id == user.team_id,
                User.role == UserRole.MANAGER,
                User.id != user_uuid
            )
        )
        if existing_manager.scalar_one_or_none():
            raise PermissionDenied("В команде уже есть менеджер. В команде может быть только один менеджер")

    user.role = new_role
    await session.commit()
    await session.refresh(user)
    return user
