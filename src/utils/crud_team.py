from typing import Optional, List
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.exceptions import AlreadyInTeam, NotInTeam, InvalidInviteCode
from models.team import Team
from models.user import User
from schemas.team import TeamCreate, TeamUpdate
from .crud_base import CRUDBase


class CRUDTeam(CRUDBase[Team, TeamCreate, TeamUpdate]):
    """CRUD операции для модели Team"""

    async def get_by_owner(
        self,
        session: AsyncSession,
        owner_id: uuid.UUID
    ) -> List[Team]:
        """Получить все команды владельца."""
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
        """Найти команду по коду приглашения."""
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
        """Добавить пользователя в команду."""
        user_result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one()

        # Проверяем, что пользователь еще не состоит в команде
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
        """Удалить пользователя из команды."""
        user_result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one()

        # Проверяем, что пользователь действительно состоит в этой команде
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
        """Получить всех участников команды."""
        result = await session.execute(
            select(User).where(User.team_id == team_id)
        )
        return result.scalars().all()

    async def is_member(
        self,
        session: AsyncSession,
        team_id: int,
        user_id: uuid.UUID
    ) -> bool:
        """Проверить, является ли пользователь членом команды."""
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
        """Проверить, является ли пользователь владельцем команды."""
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
        """Присоединиться к команде по коду приглашения с валидацией."""
        # Получаем команду
        team = await self.get(session, team_id)
        if not team:
            from core.exceptions import TeamNotFound
            raise TeamNotFound(team_id)

        # Проверяем код приглашения
        if team.invite_code != invite_code:
            raise InvalidInviteCode()

        # Добавляем пользователя (включает проверку на уже состоящего в команде)
        return await self.add_member(session, team_id, user_id)


team_crud = CRUDTeam(Team)
