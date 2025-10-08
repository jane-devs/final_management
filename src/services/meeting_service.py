import uuid
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from models.meeting import Meeting
from models.user import User
from schemas.meeting import MeetingCreate
from crud import meeting_crud
from utils.meeting_validation import validate_team_and_participants
from utils.validation import (
    validate_title_field,
    validate_content_length,
    validate_datetime_range,
    parse_datetime_safe,
    parse_uuid_list,
    validate_and_parse_team_id
)


class MeetingService:
    """Сервис для управления встречами."""

    @staticmethod
    async def create_meeting(
        session: AsyncSession,
        title: str,
        start_time: str,
        end_time: str,
        creator_id: uuid.UUID,
        description: Optional[str] = None,
        location: Optional[str] = None,
        team_id: Optional[int] = None,
        participant_ids: List[str] = None
    ) -> Meeting:
        """
        Создает новую встречу с валидацией.

        Args:
            session: Сессия базы данных
            title: Название встречи
            start_time: Время начала (ISO формат)
            end_time: Время окончания (ISO формат)
            creator_id: ID создателя
            description: Описание (опционально)
            location: Место проведения (опционально)
            team_id: ID команды (опционально)
            participant_ids: Список ID участников (опционально)

        Returns:
            Meeting: Созданная встреча
        """
        title = validate_title_field(title, "Название встречи")
        if description:
            description = validate_content_length(
                description, "Описание", max_length=2000)
        team_id = await validate_and_parse_team_id(
            session,
            str(team_id) if team_id else None,
            creator_id,
            default_to_user_teams=True
        )

        # Парсинг и валидация времени
        start_dt = parse_datetime_safe(start_time, "Время начала")
        end_dt = parse_datetime_safe(end_time, "Время окончания")

        if not start_dt or not end_dt:
            raise HTTPException(
                status_code=400,
                detail="Необходимо указать время начала и окончания"
            )

        validate_datetime_range(start_dt, end_dt, allow_past=False)
        parsed_participants = parse_uuid_list(participant_ids or [])
        validated_participants = await validate_team_and_participants(
            session, creator_id, team_id, parsed_participants
        )

        meeting_data = MeetingCreate(
            title=title,
            description=description,
            start_time=start_dt,
            end_time=end_dt,
            location=location,
            team_id=team_id,
            participant_ids=validated_participants
        )

        meeting = await meeting_crud.create_with_participants(
            session, meeting_data, creator_id
        )
        return meeting

    @staticmethod
    async def update_meeting(
        session: AsyncSession,
        meeting_id: int,
        title: str,
        start_time: str,
        end_time: str,
        current_user_id: uuid.UUID,
        description: Optional[str] = None,
        location: Optional[str] = None,
        participant_ids: List[str] = None
    ) -> Meeting:
        """
        Обновляет встречу с валидацией.

        Args:
            session: Сессия базы данных
            meeting_id: ID встречи
            title: Название
            start_time: Время начала
            end_time: Время окончания
            current_user_id: ID текущего пользователя
            description: Описание
            location: Место
            participant_ids: Участники

        Returns:
            Meeting: Обновленная встреча
        """
        meeting = await meeting_crud.get(session, meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        title = validate_title_field(title, "Название встречи")
        if description:
            description = validate_content_length(
                description, "Описание", max_length=2000)

        start_dt = parse_datetime_safe(start_time, "Время начала")
        end_dt = parse_datetime_safe(end_time, "Время окончания")

        if start_dt and end_dt:
            validate_datetime_range(start_dt, end_dt, allow_past=True)

        meeting.title = title
        meeting.description = description
        meeting.start_time = start_dt
        meeting.end_time = end_dt
        meeting.location = location

        if participant_ids:
            parsed_participants = parse_uuid_list(participant_ids)

            validated_participants = await validate_team_and_participants(
                session, current_user_id, meeting.team_id, parsed_participants
            )

            participants_result = await session.execute(
                select(User).where(User.id.in_(validated_participants))
            )
            participants = participants_result.scalars().all()
            meeting.participants = participants
        else:
            meeting.participants = []

        await session.commit()
        return meeting
