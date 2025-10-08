from fastapi import Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, Callable
import uuid

from core.database import get_async_session
from models.user import User, UserRole
from models.team import Team
from models.task import Task
from utils.user_teams import get_user_with_teams


templates = Jinja2Templates(directory="frontend_templates")


async def get_session_user_id(request: Request) -> uuid.UUID | None:
    """Получает user_id из сессии."""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    try:
        return uuid.UUID(str(user_id))
    except (ValueError, TypeError):
        return None


def current_user_factory():
    """
    Универсальная зависимость для получения текущего
    пользователя с подгрузкой связей.
    Возвращает User | None.
    """
    async def _dep(
        session: AsyncSession = Depends(get_async_session),
        user_id: Optional[uuid.UUID] = Depends(get_session_user_id),
    ) -> User | None:
        if not user_id:
            return None

        opts = [
            selectinload(User.teams).selectinload(Team.members),
            selectinload(User.created_tasks).selectinload(Task.assignee),
            selectinload(User.created_tasks).selectinload(Task.creator),
            selectinload(User.assigned_tasks).selectinload(Task.assignee),
            selectinload(User.assigned_tasks).selectinload(Task.creator),
            selectinload(User.created_meetings),
            selectinload(User.evaluations)
        ]

        stmt = select(User).where(User.id == user_id)
        if opts:
            stmt = stmt.options(*opts)

        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
        return user

    return _dep


async def require_auth(
    current_user: User | None = Depends(current_user_factory())
) -> User:
    """
    Требует авторизации. Если пользователь не авторизован - редирект на login.
    """
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    return current_user


_ROLE_ORDER = {
    UserRole.USER: 1,
    UserRole.MANAGER: 2,
    UserRole.ADMIN: 3,
}


def require_role(min_role: UserRole, action: str = "выполнить это действие") -> Callable[..., User]:
    """
    Зависимость, требующая минимум роль min_role.
    При недостаточном уровне бросает HTTPException с информативным текстом.
    """
    def _dep(current_user: Optional[User] = Depends(current_user_factory())) -> User:
        if not current_user:
            raise HTTPException(status_code=401, detail="Требуется авторизация")
        current_role = getattr(current_user, "role", None)
        if isinstance(current_role, str):
            try:
                current_role = UserRole(current_role)
            except ValueError:
                current_role = None
        current_level = _ROLE_ORDER.get(current_role, 0)
        required_level = _ROLE_ORDER.get(min_role, 0)
        if current_level < required_level:
            raise HTTPException(
                status_code=403,
                detail=f"Только {min_role.value} может {action}"
            )
        return current_user
    return _dep


async def get_authenticated_user_with_teams(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_auth),
    load_members: bool = False
) -> User:
    """
    Получает авторизованного пользователя с командами.
    """
    user = await get_user_with_teams(
        session, current_user.id, load_team_members=load_members)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return user
