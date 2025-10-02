from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from core.fastapi_users import current_active_user
from core.dependencies import (
    require_team_member_for_tasks,
    get_existing_meeting, get_meeting_with_access_check,
    get_meeting_with_edit_permission, get_meeting_with_delete_permission
)
from core.exceptions import (
    MeetingTimeConflict, MeetingTeamMismatch
)
from models.user import User
from models.meeting import Meeting
from schemas.meeting import MeetingCreate, MeetingRead, MeetingUpdate
from utils.crud_meeting import meeting_crud

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.post("/", response_model=MeetingRead, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    meeting_data: MeetingCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_team_member_for_tasks)
):
    """Создание новой встречи"""
    if meeting_data.team_id != current_user.team_id:
        raise MeetingTeamMismatch()
    if meeting_data.participant_ids:
        conflicts = await meeting_crud.check_conflicts(
            session,
            meeting_data.start_time,
            meeting_data.end_time,
            meeting_data.participant_ids
        )
        if conflicts:
            raise MeetingTimeConflict(len(conflicts))
    meeting = await meeting_crud.create_with_participants(
        session,
        meeting_data,
        creator_id=current_user.id
    )
    return meeting


@router.get("/", response_model=List[MeetingRead])
async def get_meetings(
    start_date: Optional[datetime] = Query(None, description="Начало периода"),
    end_date: Optional[datetime] = Query(None, description="Конец периода"),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_team_member_for_tasks)
):
    """Получение списка встреч команды"""
    meetings = await meeting_crud.get_by_team(
        session,
        team_id=current_user.team_id,
        start_date=start_date,
        end_date=end_date
    )
    return meetings


@router.get("/my", response_model=List[MeetingRead])
async def get_my_meetings(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    """Получение встреч текущего пользователя"""
    meetings = await meeting_crud.get_by_user(
        session,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        include_created=True
    )
    return meetings


@router.get("/today", response_model=List[MeetingRead])
async def get_today_meetings(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    """Получение встреч на сегодня"""
    meetings = await meeting_crud.get_today(
        session,
        user_id=current_user.id
    )
    return meetings


@router.get("/upcoming", response_model=List[MeetingRead])
async def get_upcoming_meetings(
    limit: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    """Получение предстоящих встреч"""
    meetings = await meeting_crud.get_upcoming(
        session,
        user_id=current_user.id,
        limit=limit
    )
    return meetings


@router.get("/{meeting_id}", response_model=MeetingRead)
async def get_meeting(
    meeting: Meeting = Depends(get_meeting_with_access_check)
):
    """Получение конкретной встречи"""
    return meeting


@router.patch("/{meeting_id}", response_model=MeetingRead)
async def update_meeting(
    meeting_data: MeetingUpdate,
    meeting: Meeting = Depends(get_meeting_with_edit_permission),
    session: AsyncSession = Depends(get_async_session)
):
    """Обновление встречи"""
    update_data = meeting_data.model_dump(exclude_unset=True)
    if "start_time" in update_data or "end_time" in update_data:
        new_start = update_data.get("start_time", meeting.start_time)
        new_end = update_data.get("end_time", meeting.end_time)
        participant_ids = update_data.get("participant_ids", [p.id for p in meeting.participants])
        conflicts = await meeting_crud.check_conflicts(
            session,
            new_start,
            new_end,
            participant_ids,
            exclude_meeting_id=meeting.id
        )
        if conflicts:
            raise MeetingTimeConflict(len(conflicts))
    if "participant_ids" in update_data:
        meeting.participants = []
        await session.flush()
        for user_id in update_data["participant_ids"]:
            await meeting_crud.add_participant(session, meeting.id, user_id)
        del update_data["participant_ids"]
    updated_meeting = await meeting_crud.update(
        session,
        db_obj=meeting,
        obj_in=update_data
    )
    return await meeting_crud.get(
        session,
        updated_meeting.id,
        relationships=["creator", "participants"]
    )


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(
    meeting: Meeting = Depends(get_meeting_with_delete_permission),
    session: AsyncSession = Depends(get_async_session)
):
    """Удаление встречи"""
    await meeting_crud.delete(session, id=meeting.id)


@router.post("/{meeting_id}/participants/{user_id}", response_model=MeetingRead)
async def add_participant(
    user_id: str,
    meeting: Meeting = Depends(get_existing_meeting),
    session: AsyncSession = Depends(get_async_session)
):
    """Добавить участника к встрече"""
    updated_meeting = await meeting_crud.add_participant(session, meeting.id, user_id)
    return updated_meeting


@router.delete("/{meeting_id}/participants/{user_id}", response_model=MeetingRead)
async def remove_participant(
    user_id: str,
    meeting: Meeting = Depends(get_existing_meeting),
    session: AsyncSession = Depends(get_async_session)
):
    """Удалить участника из встречи"""
    updated_meeting = await meeting_crud.remove_participant(session, meeting.id, user_id)
    return updated_meeting
