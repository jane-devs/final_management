from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from core.fastapi_users import current_active_user
from core.dependencies import (
    get_team_with_access_check, get_team_with_owner_check,
    check_user_in_team, require_admin
)
from core.exceptions import OwnerCannotLeaveTeam
from models.user import User, UserRole
from models.team import Team
from schemas.team import TeamCreate, TeamRead, TeamUpdate, TeamInvite
from crud import team_crud

router = APIRouter(prefix="/teams", tags=["Команды"])


@router.post(
    "/",
    response_model=TeamRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать команду",
    description="Создание новой команды (только для администраторов)"
)
async def create_team(
    team_data: TeamCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_admin)
):
    team = await team_crud.create(
        session,
        team_data,
        owner_id=current_user.id
    )
    await team_crud.add_member(session, team.id, current_user.id)
    return await team_crud.get(session, team.id, relationships=["members"])


@router.get(
    "/",
    response_model=List[TeamRead],
    summary="Список команд",
    description="Получение списка команд"
)
async def get_teams(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    if current_user.role == UserRole.ADMIN:
        return await team_crud.get_multi(
            session,
            skip=skip,
            limit=limit,
            relationships=["members"]
        )

    if current_user.team_id:
        team = await team_crud.get(
            session,
            current_user.team_id,
            relationships=["members"]
        )
        return [team] if team else []

    return []


@router.get(
    "/{team_id}",
    response_model=TeamRead,
    summary="Получить команду",
    description="Получение информации о команде"
)
async def get_team(
    team: Team = Depends(get_team_with_access_check)
):
    return team


@router.patch(
    "/{team_id}",
    response_model=TeamRead,
    summary="Обновить команду",
    description="Обновление команды"
)
async def update_team(
    team_data: TeamUpdate,
    team: Team = Depends(get_team_with_owner_check),
    session: AsyncSession = Depends(get_async_session)
):
    updated_team = await team_crud.update(session, db_obj=team, obj_in=team_data)
    return await team_crud.get(session, updated_team.id, relationships=["members"])


@router.delete(
    "/{team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить команду",
    description="Удаление команды"
)
async def delete_team(
    team: Team = Depends(get_team_with_owner_check),
    session: AsyncSession = Depends(get_async_session)
):
    await team_crud.delete(session, id=team.id)


@router.post(
    "/{team_id}/join",
    response_model=TeamRead,
    summary="Присоединиться к команде",
    description="Присоединение к команде по коду приглашения"
)
async def join_team(
    team_id: int,
    invite_data: TeamInvite,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    return await team_crud.join_team_with_invite(
        session, team_id, invite_data.invite_code, current_user.id
    )


@router.post(
    "/{team_id}/leave",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Выйти из команды",
    description="Выход из команды"
)
async def leave_team(
    team_id: int = Depends(check_user_in_team),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    is_owner = await team_crud.is_owner(session, team_id, current_user.id)
    if is_owner:
        raise OwnerCannotLeaveTeam()

    await team_crud.remove_member(session, team_id, current_user.id)


@router.get(
    "/{team_id}/members",
    response_model=List,
    summary="Участники команды",
    description="Получить список участников команды (админ или члены команды)"
)
async def get_team_members(
    team: Team = Depends(get_team_with_access_check),
    session: AsyncSession = Depends(get_async_session)
):
    return await team_crud.get_members(session, team.id)


@router.get(
    "/{team_id}/invite-code",
    summary="Инвайт-код команды",
    description="Получить инвайт-код команды (только админ или владелец)"
)
async def get_team_invite_code(
    team: Team = Depends(get_team_with_access_check),
    current_user: User = Depends(current_active_user)
):
    if current_user.role != UserRole.ADMIN and team.owner_id != current_user.id:
        from core.exceptions import PermissionDenied
        raise PermissionDenied("Только администратор или владелец команды может получить инвайт-код")

    return {"invite_code": team.invite_code}


@router.delete(
    "/{team_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить участника",
    description="Удалить пользователя из команды (только админ)"
)
async def remove_team_member(
    team_id: int,
    user_id: str,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    import uuid as uuid_lib
    from core.exceptions import UserNotFound, PermissionDenied

    if current_user.role != UserRole.ADMIN:
        raise PermissionDenied("Только администратор может удалять пользователей из команды")

    try:
        user_uuid = uuid_lib.UUID(user_id)
    except ValueError:
        raise UserNotFound(user_id)

    await team_crud.remove_member(session, team_id, user_uuid)
