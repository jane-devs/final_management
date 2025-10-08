from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from models.user import User
from models.team import Team
from crud.crud_team import team_crud


async def get_user_with_teams(
    session: AsyncSession,
    user_id: uuid.UUID,
    load_team_members: bool = False
) -> Optional[User]:
    """
    Возвращает User с подгруженной связью .teams (и при need -- .teams.members).
    Используй это, если тебе нужен сам User (и его поля).
    """
    opts = []
    if load_team_members:
        opts.append(selectinload(User.teams).selectinload(Team.members))
    else:
        opts.append(selectinload(User.teams))

    stmt = select(User).where(User.id == user_id).options(*opts)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


async def get_user_teams(
    session: AsyncSession,
    user_id: uuid.UUID,
    load_team_members: bool = False
) -> List[Team]:
    """
    Возвращает список Team, в которых состоит пользователь.
    Результат — уже загруженные Team (и members, если load_team_members=True).
    Удобно для передачи в шаблон.
    """
    user = await get_user_with_teams(
        session, user_id, load_team_members=load_team_members)
    if not user:
        return []
    return list(user.teams or [])


async def get_team_members(
    session: AsyncSession,
    team_id: int
) -> List[User]:
    """
    Возвращает список User, которые состоят в команде team_id.
    Гарантированно возвращает пользователей (без lazy-load).
    """
    team = await team_crud.get(session, team_id, relationships=["members"])
    return list(team.members) if team else []
