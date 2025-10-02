from typing import Optional, List
from datetime import datetime, timedelta
import uuid
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.meeting import Meeting, meeting_participants
from models.user import User
from schemas.meeting import MeetingCreate, MeetingUpdate
from .crud_base import CRUDBase


class CRUDMeeting(CRUDBase[Meeting, MeetingCreate, MeetingUpdate]):
    """CRUD операции для модели Meeting"""

    async def create_with_participants(
        self,
        session: AsyncSession,
        obj_in: MeetingCreate,
        creator_id: uuid.UUID
    ) -> Meeting:
        """Создать встречу с участниками."""
        meeting_data = obj_in.model_dump(exclude={"participant_ids"})
        participant_ids = obj_in.participant_ids or []
        meeting = Meeting(**meeting_data, creator_id=creator_id)
        session.add(meeting)
        await session.flush()
        if participant_ids:
            participants_result = await session.execute(
                select(User).where(User.id.in_(participant_ids))
            )
            participants = participants_result.scalars().all()
            meeting.participants = participants
        await session.commit()
        await session.refresh(meeting, ["creator", "participants"])
        return meeting

    async def get_by_team(
        self,
        session: AsyncSession,
        team_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Meeting]:
        """Получить встречи команды за период."""
        query = select(Meeting).options(
            selectinload(Meeting.creator),
            selectinload(Meeting.participants)
        ).where(Meeting.team_id == team_id)
        if start_date:
            query = query.where(Meeting.start_time >= start_date)
        if end_date:
            query = query.where(Meeting.end_time <= end_date)
        query = query.order_by(Meeting.start_time)
        result = await session.execute(query)
        return result.scalars().all()

    async def get_by_user(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_created: bool = True
    ) -> List[Meeting]:
        """Получить встречи пользователя."""
        query = select(Meeting).options(
            selectinload(Meeting.creator),
            selectinload(Meeting.participants)
        ).join(
            meeting_participants
        ).where(
            meeting_participants.c.user_id == user_id
        )
        if include_created:
            query = query.union(
                select(Meeting).options(
                    selectinload(Meeting.creator),
                    selectinload(Meeting.participants)
                ).where(Meeting.creator_id == user_id)
            )
        if start_date:
            query = query.where(Meeting.start_time >= start_date)
        if end_date:
            query = query.where(Meeting.end_time <= end_date)
        query = query.order_by(Meeting.start_time)
        result = await session.execute(query)
        return result.scalars().all()

    async def get_upcoming(
        self,
        session: AsyncSession,
        team_id: Optional[int] = None,
        user_id: Optional[uuid.UUID] = None,
        limit: int = 10
    ) -> List[Meeting]:
        """Получить предстоящие встречи."""
        now = datetime.now()
        query = select(Meeting).options(
            selectinload(Meeting.creator),
            selectinload(Meeting.participants)
        ).where(Meeting.start_time >= now)
        if team_id:
            query = query.where(Meeting.team_id == team_id)
        if user_id:
            query = query.join(
                meeting_participants
            ).where(
                or_(
                    meeting_participants.c.user_id == user_id,
                    Meeting.creator_id == user_id
                )
            )
        query = query.order_by(Meeting.start_time).limit(limit)
        result = await session.execute(query)
        return result.scalars().all()

    async def get_today(
        self,
        session: AsyncSession,
        team_id: Optional[int] = None,
        user_id: Optional[uuid.UUID] = None
    ) -> List[Meeting]:
        """Получить встречи на сегодня."""
        now = datetime.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        query = select(Meeting).options(
            selectinload(Meeting.creator),
            selectinload(Meeting.participants)
        ).where(
            and_(
                Meeting.start_time >= start_of_day,
                Meeting.start_time < end_of_day
            )
        )
        if team_id:
            query = query.where(Meeting.team_id == team_id)
        if user_id:
            query = query.join(
                meeting_participants
            ).where(
                or_(
                    meeting_participants.c.user_id == user_id,
                    Meeting.creator_id == user_id
                )
            )
        query = query.order_by(Meeting.start_time)
        result = await session.execute(query)
        return result.scalars().all()

    async def add_participant(
        self,
        session: AsyncSession,
        meeting_id: int,
        user_id: uuid.UUID
    ) -> Meeting:
        """Добавить участника к встрече."""
        meeting = await self.get(
            session, meeting_id, relationships=["participants"]
        )
        if meeting:
            user_result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if user and user not in meeting.participants:
                meeting.participants.append(user)
                await session.commit()
                await session.refresh(meeting, ["participants"])
        return meeting

    async def remove_participant(
        self,
        session: AsyncSession,
        meeting_id: int,
        user_id: uuid.UUID
    ) -> Meeting:
        """Удалить участника из встречи."""
        meeting = await self.get(
            session, meeting_id, relationships=["participants"]
        )
        if meeting:
            meeting.participants = [
                p for p in meeting.participants if p.id != user_id
            ]
            await session.commit()
            await session.refresh(meeting, ["participants"])
        return meeting

    async def check_conflicts(
        self,
        session: AsyncSession,
        start_time: datetime,
        end_time: datetime,
        user_ids: List[uuid.UUID],
        exclude_meeting_id: Optional[int] = None
    ) -> List[Meeting]:
        """Проверить конфликты по времени для участников."""
        query = select(Meeting).options(
            selectinload(Meeting.participants)
        ).join(
            meeting_participants
        ).where(
            and_(
                meeting_participants.c.user_id.in_(user_ids),
                or_(
                    and_(
                        Meeting.start_time < end_time,
                        Meeting.end_time > start_time
                    )
                )
            )
        )
        if exclude_meeting_id:
            query = query.where(Meeting.id != exclude_meeting_id)
        result = await session.execute(query)
        return result.scalars().all()


meeting_crud = CRUDMeeting(Meeting)
