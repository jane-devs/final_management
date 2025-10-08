import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from models.user import User
from models.team import Team
from schemas.team import TeamCreate
from crud import team_crud
from utils.validation import validate_team_name, validate_user_is_team_owner


class TeamService:
    """Сервис для управления командами."""

    @staticmethod
    async def create_team_with_owner(
        session: AsyncSession,
        name: str,
        owner_id: uuid.UUID
    ) -> Team:
        """
        Создает команду и автоматически добавляет владельца в members.

        Args:
            session: Сессия базы данных
            name: Название команды
            owner_id: ID владельца

        Returns:
            Team: Созданная команда

        Raises:
            HTTPException: Если произошла ошибка при создании
        """
        name = validate_team_name(name)

        team_data = TeamCreate(name=name)
        team = await team_crud.create(session, team_data, owner_id=owner_id)

        res = await session.execute(select(User).where(User.id == owner_id))
        user_obj = res.scalar_one()

        team_with_members = await team_crud.get(
            session, team.id, relationships=["members"])
        if team_with_members is None:
            await session.rollback()
            raise HTTPException(
                status_code=500, detail="Не удалось создать команду")

        team_with_members.members.append(user_obj)
        session.add(team_with_members)
        await session.commit()

        return team_with_members

    @staticmethod
    async def join_team_by_invite_code(
        session: AsyncSession,
        invite_code: str,
        user_id: uuid.UUID
    ) -> Team:
        """
        Присоединяет пользователя к команде по коду приглашения.

        Args:
            session: Сессия базы данных
            invite_code: Код приглашения
            user_id: ID пользователя

        Returns:
            Team: Команда, к которой присоединился пользователь

        Raises:
            HTTPException: Если код неверный
        """
        team = await team_crud.get_by_invite_code(session, invite_code)
        if not team:
            raise HTTPException(
                status_code=404, detail="Неверный код приглашения")

        await team_crud.add_member(session, team.id, user_id)
        return team

    @staticmethod
    async def update_team_name(
        session: AsyncSession,
        team_id: int,
        name: str,
        user_id: uuid.UUID
    ) -> Team:
        """
        Обновляет название команды (только владелец).

        Args:
            session: Сессия базы данных
            team_id: ID команды
            name: Новое название
            user_id: ID пользователя (должен быть владельцем)

        Returns:
            Team: Обновленная команда

        Raises:
            HTTPException: Если пользователь не владелец
        """
        team = await validate_user_is_team_owner(session, team_id, user_id)

        name = validate_team_name(name)
        team.name = name
        await session.commit()

        return team

    @staticmethod
    async def remove_member(
        session: AsyncSession,
        team_id: int,
        member_id: uuid.UUID,
        requester_id: uuid.UUID
    ) -> None:
        """
        Удаляет участника из команды (только владелец).

        Args:
            session: Сессия базы данных
            team_id: ID команды
            member_id: ID участника для удаления
            requester_id: ID пользователя, запрашивающего удаление

        Raises:
            HTTPException: Если пользователь не владелец
        """
        # Валидация прав
        await validate_user_is_team_owner(session, team_id, requester_id)
        await team_crud.remove_member(session, team_id, member_id)

    @staticmethod
    async def leave_team(
        session: AsyncSession,
        team_id: int,
        user_id: uuid.UUID
    ) -> None:
        """
        Пользователь покидает команду.
        Если пользователь - владелец, команда удаляется полностью.

        Args:
            session: Сессия базы данных
            team_id: ID команды
            user_id: ID пользователя
        """
        user_result = await session.execute(select(User).where(
            User.id == user_id))
        user_obj = user_result.scalar_one()

        team = await team_crud.get(session, team_id, relationships=["members"])
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if team.owner_id == user_obj.id:
            await session.delete(team)
        else:
            if user_obj in team.members:
                team.members.remove(user_obj)

        await session.commit()
