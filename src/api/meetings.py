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
from crud import meeting_crud

router = APIRouter(prefix="/meetings", tags=["Встречи"])


@router.post(
    "/",
    response_model=MeetingRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать встречу",
    description="Создание новой встречи (только менеджер или админ)"
)
async def create_meeting(
    meeting_data: MeetingCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_team_member_for_tasks)
):
    from models.user import UserRole
    from core.exceptions import PermissionDenied

    if current_user.role not in [UserRole.MANAGER, UserRole.ADMIN]:
        raise PermissionDenied("Только менеджеры и администраторы могут создавать встречи")

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


@router.get(
    "/",
    response_model=List[MeetingRead],
    summary="Список встреч",
    description="Получение списка встреч команды"
)
async def get_meetings(
    start_date: Optional[datetime] = Query(None, description="Начало периода"),
    end_date: Optional[datetime] = Query(None, description="Конец периода"),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_team_member_for_tasks)
):
    meetings = await meeting_crud.get_by_team(
        session,
        team_id=current_user.team_id,
        start_date=start_date,
        end_date=end_date
    )
    return meetings


@router.get(
    "/my",
    response_model=List[MeetingRead],
    summary="Мои встречи",
    description="Получение встреч текущего пользователя"
)
async def get_my_meetings(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    meetings = await meeting_crud.get_by_user(
        session,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        include_created=True
    )
    return meetings


@router.get(
    "/user/{user_id}",
    response_model=List[MeetingRead],
    summary="Встречи пользователя",
    description="Получение встреч пользователя по ID (только админ или менеджер)"
)
async def get_user_meetings(
    user_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    import uuid as uuid_lib
    from models.user import UserRole
    from core.exceptions import PermissionDenied, UserNotFound

    if str(current_user.id) != user_id and current_user.role not in [UserRole.MANAGER, UserRole.ADMIN]:
        raise PermissionDenied("просматривать встречи других пользователей")

    try:
        user_uuid = uuid_lib.UUID(user_id)
    except ValueError:
        raise UserNotFound(user_id)

    meetings = await meeting_crud.get_by_user(
        session,
        user_id=user_uuid,
        start_date=start_date,
        end_date=end_date,
        include_created=True
    )
    return meetings


@router.get(
    "/today",
    response_model=List[MeetingRead],
    summary="Встречи на сегодня",
    description="Получение встреч на сегодня"
)
async def get_today_meetings(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    meetings = await meeting_crud.get_today(
        session,
        user_id=current_user.id
    )
    return meetings


@router.get(
    "/upcoming",
    response_model=List[MeetingRead],
    summary="Предстоящие встречи",
    description="Получение предстоящих встреч"
)
async def get_upcoming_meetings(
    limit: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    meetings = await meeting_crud.get_upcoming(
        session,
        user_id=current_user.id,
        limit=limit
    )
    return meetings


@router.get(
    "/{meeting_id}",
    response_model=MeetingRead,
    summary="Получить встречу",
    description="Получение конкретной встречи"
)
async def get_meeting(
    meeting: Meeting = Depends(get_meeting_with_access_check)
):
    return meeting


@router.patch(
    "/{meeting_id}",
    response_model=MeetingRead,
    summary="Обновить встречу",
    description="Обновление встречи"
)
async def update_meeting(
    meeting_data: MeetingUpdate,
    meeting: Meeting = Depends(get_meeting_with_edit_permission),
    session: AsyncSession = Depends(get_async_session)
):
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


@router.delete(
    "/{meeting_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить встречу",
    description="Удаление встречи"
)
async def delete_meeting(
    meeting: Meeting = Depends(get_meeting_with_delete_permission),
    session: AsyncSession = Depends(get_async_session)
):
    await meeting_crud.delete(session, id=meeting.id)


@router.post(
    "/{meeting_id}/participants/{user_id}",
    response_model=MeetingRead,
    summary="Добавить участника",
    description="Добавить участника к встрече"
)
async def add_participant(
    user_id: str,
    meeting: Meeting = Depends(get_existing_meeting),
    session: AsyncSession = Depends(get_async_session)
):
    updated_meeting = await meeting_crud.add_participant(
        session, meeting.id, user_id)
    return updated_meeting


@router.delete(
    "/{meeting_id}/participants/{user_id}",
    response_model=MeetingRead,
    summary="Удалить участника",
    description="Удалить участника из встречи"
)
async def remove_participant(
    user_id: str,
    meeting: Meeting = Depends(get_existing_meeting),
    session: AsyncSession = Depends(get_async_session)
):
    updated_meeting = await meeting_crud.remove_participant(session, meeting.id, user_id)
    return updated_meeting
