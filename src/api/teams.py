from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from core.fastapi_users import current_active_user
from core.dependencies import (
    get_team_with_access_check, get_team_with_owner_check,
    check_user_in_team
)
from core.exceptions import OwnerCannotLeaveTeam
from models.user import User, UserRole
from models.team import Team
from schemas.team import TeamCreate, TeamRead, TeamUpdate, TeamInvite
from utils.crud_team import team_crud

router = APIRouter(prefix="/teams", tags=["teams"])


@router.post("/", response_model=TeamRead, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    """Создание новой команды"""
    team = await team_crud.create(
        session,
        team_data,
        owner_id=current_user.id
    )
    await team_crud.add_member(session, team.id, current_user.id)
    return await team_crud.get(session, team.id, relationships=["members"])


@router.get("/", response_model=List[TeamRead])
async def get_teams(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    """Получение списка команд"""
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


@router.get("/{team_id}", response_model=TeamRead)
async def get_team(
    team: Team = Depends(get_team_with_access_check)
):
    """Получение информации о команде"""
    return team


@router.patch("/{team_id}", response_model=TeamRead)
async def update_team(
    team_data: TeamUpdate,
    team: Team = Depends(get_team_with_owner_check),
    session: AsyncSession = Depends(get_async_session)
):
    """Обновление команды"""
    updated_team = await team_crud.update(session, db_obj=team, obj_in=team_data)
    return await team_crud.get(session, updated_team.id, relationships=["members"])


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team: Team = Depends(get_team_with_owner_check),
    session: AsyncSession = Depends(get_async_session)
):
    """Удаление команды"""
    await team_crud.delete(session, id=team.id)


@router.post("/{team_id}/join", response_model=TeamRead)
async def join_team(
    team_id: int,
    invite_data: TeamInvite,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Присоединение к команде по коду приглашения"""
    return await team_crud.join_team_with_invite(
        session, team_id, invite_data.invite_code, current_user.id
    )


@router.post("/{team_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_team(
    team_id: int = Depends(check_user_in_team),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Выход из команды"""
    is_owner = await team_crud.is_owner(session, team_id, current_user.id)
    if is_owner:
        raise OwnerCannotLeaveTeam()

    await team_crud.remove_member(session, team_id, current_user.id)


@router.get("/{team_id}/members", response_model=List)
async def get_team_members(
    team: Team = Depends(get_team_with_access_check),
    session: AsyncSession = Depends(get_async_session)
):
    """Получить список участников команды."""
    return await team_crud.get_members(session, team.id)
