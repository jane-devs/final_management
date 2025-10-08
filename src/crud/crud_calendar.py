import uuid
from datetime import datetime, date, timedelta
from calendar import monthrange
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from models.task import Task
from models.meeting import Meeting, meeting_participants
from schemas.calendar import CalendarDay, CalendarMonth


class CRUDCalendar:
    async def get_day(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        target_date: date
    ) -> CalendarDay:
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        tasks_result = await session.execute(
            select(Task).where(
                and_(
                    or_(
                        Task.creator_id == user_id,
                        Task.assignee_id == user_id
                    ),
                    Task.deadline >= start_of_day,
                    Task.deadline <= end_of_day
                )
            ).order_by(Task.deadline)
        )
        tasks = tasks_result.scalars().all()
        meetings_result = await session.execute(
            select(Meeting).outerjoin(
                meeting_participants
            ).where(
                and_(
                    or_(
                        meeting_participants.c.user_id == user_id,
                        Meeting.creator_id == user_id
                    ),
                    Meeting.start_time >= start_of_day,
                    Meeting.start_time <= end_of_day
                )
            ).order_by(Meeting.start_time)
        )
        meetings = meetings_result.scalars().unique().all()
        return CalendarDay(
            date=target_date,
            tasks=tasks,
            meetings=meetings
        )

    async def get_month(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        year: int,
        month: int
    ) -> CalendarMonth:
        first_day = date(year, month, 1)
        last_day_num = monthrange(year, month)[1]
        last_day = date(year, month, last_day_num)
        start_of_month = datetime.combine(first_day, datetime.min.time())
        end_of_month = datetime.combine(last_day, datetime.max.time())
        tasks_result = await session.execute(
            select(Task).where(
                and_(
                    or_(
                        Task.creator_id == user_id,
                        Task.assignee_id == user_id
                    ),
                    Task.deadline >= start_of_month,
                    Task.deadline <= end_of_month
                )
            ).order_by(Task.deadline)
        )
        tasks = tasks_result.scalars().all()
        meetings_result = await session.execute(
            select(Meeting).outerjoin(
                meeting_participants
            ).where(
                and_(
                    or_(
                        meeting_participants.c.user_id == user_id,
                        Meeting.creator_id == user_id
                    ),
                    Meeting.start_time >= start_of_month,
                    Meeting.start_time <= end_of_month
                )
            ).order_by(Meeting.start_time)
        )
        meetings = meetings_result.scalars().unique().all()
        days_data = []
        current_date = first_day
        while current_date <= last_day:
            start_of_day = datetime.combine(current_date, datetime.min.time())
            end_of_day = datetime.combine(current_date, datetime.max.time())
            day_tasks = [
                task for task in tasks
                if task.deadline and start_of_day <= task.deadline <= end_of_day
            ]
            day_meetings = [
                meeting for meeting in meetings
                if start_of_day <= meeting.start_time <= end_of_day
            ]
            days_data.append(CalendarDay(
                date=current_date,
                tasks=day_tasks,
                meetings=day_meetings
            ))
            current_date += timedelta(days=1)
        return CalendarMonth(
            year=year,
            month=month,
            days=days_data
        )


calendar_crud = CRUDCalendar()
