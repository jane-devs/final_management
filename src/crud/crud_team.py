from typing import Optional, List
import uuid
import secrets
import string
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from core.exceptions import AlreadyInTeam, NotInTeam, InvalidInviteCode
from models.team import Team
from models.user import User
from schemas.team import TeamCreate, TeamUpdate
from .crud_base import CRUDBase


def generate_invite_code(length: int = 8) -> str:
    """Генерация кода приглашения в группу."""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class CRUDTeam(CRUDBase[Team, TeamCreate, TeamUpdate]):
    async def create(
        self,
        session: AsyncSession,
        obj_in: TeamCreate,
        **kwargs
    ) -> Team:
        invite_code = generate_invite_code()
        while await self.get_by_invite_code(session, invite_code):
            invite_code = generate_invite_code()
        kwargs['invite_code'] = invite_code
        return await super().create(session, obj_in, **kwargs)

    async def get_by_owner(
        self,
        session: AsyncSession,
        owner_id: uuid.UUID
    ) -> List[Team]:
        result = await session.execute(
            select(Team)
            .options(selectinload(Team.members))
            .where(Team.owner_id == owner_id)
        )
        return result.scalars().all()

    async def get_by_invite_code(
        self,
        session: AsyncSession,
        invite_code: str
    ) -> Optional[Team]:
        result = await session.execute(
            select(Team)
            .options(selectinload(Team.members))
            .where(Team.invite_code == invite_code)
        )
        return result.scalar_one_or_none()

    async def add_member(
        self,
        session: AsyncSession,
        team_id: int,
        user_id: uuid.UUID
    ) -> Team:
        user_result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one()
        if user.team_id is not None:
            raise AlreadyInTeam()
        user.team_id = team_id
        await session.commit()
        return await self.get(session, team_id, relationships=["members"])

    async def remove_member(
        self,
        session: AsyncSession,
        team_id: int,
        user_id: uuid.UUID
    ) -> Team:
        user_result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one()
        if user.team_id != team_id:
            raise NotInTeam(team_id)
        user.team_id = None
        await session.commit()
        return await self.get(session, team_id, relationships=["members"])

    async def get_members(
        self,
        session: AsyncSession,
        team_id: int
    ) -> List[User]:
        result = await session.execute(
            select(User).join(Team.members).where(Team.id == team_id)
        )
        return result.scalars().all()

    async def is_member(
        self,
        session: AsyncSession,
        team_id: int,
        user_id: uuid.UUID
    ) -> bool:
        result = await session.execute(
            select(User).where(
                User.id == user_id,
                User.team_id == team_id
            )
        )
        return result.scalar_one_or_none() is not None

    async def is_owner(
        self,
        session: AsyncSession,
        team_id: int,
        user_id: uuid.UUID
    ) -> bool:
        result = await session.execute(
            select(Team).where(
                Team.id == team_id,
                Team.owner_id == user_id
            )
        )
        return result.scalar_one_or_none() is not None

    async def join_team_with_invite(
        self,
        session: AsyncSession,
        team_id: int,
        invite_code: str,
        user_id: uuid.UUID
    ) -> Team:
        team = await self.get(session, team_id)
        if not team:
            from core.exceptions import TeamNotFound
            raise TeamNotFound(team_id)
        if team.invite_code != invite_code:
            raise InvalidInviteCode()
        return await self.add_member(session, team_id, user_id)


team_crud = CRUDTeam(Team)
