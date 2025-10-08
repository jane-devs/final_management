from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from core.database import get_async_session
from models.user import User, UserRole
from .dependencies import templates, require_auth, require_role
from services import TeamService
from utils.form_helpers import render_error


router = APIRouter()


@router.get("/teams", response_class=HTMLResponse)
async def teams_page(
    request: Request,
    current_user: User = Depends(require_auth)
):
    """Список команд пользователя."""
    teams = current_user.teams if getattr(
        current_user, "teams", None) is not None else []

    return templates.TemplateResponse("teams.html", {
        "request": request,
        "user": current_user,
        "teams": teams
    })


@router.get("/teams/new", response_class=HTMLResponse)
async def new_team_page(
    request: Request,
    current_user: User = Depends(require_role(UserRole.MANAGER))
):
    """Страница создания команды."""
    return templates.TemplateResponse("team_form.html", {
        "request": request,
        "user": current_user
    })


@router.post("/teams/new")
async def create_team(
    request: Request,
    name: str = Form(...),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(UserRole.MANAGER))
):
    """Создание новой команды с валидацией."""
    try:
        await TeamService.create_team_with_owner(
            session, name, current_user.id)
        return RedirectResponse(url="/teams", status_code=303)

    except HTTPException as e:
        return render_error(request, "team_form.html", current_user, e.detail, e.status_code)


@router.get("/teams/join", response_class=HTMLResponse)
async def join_team_page(
    request: Request,
    current_user: User = Depends(require_auth)
):
    """Страница присоединения к команде."""
    return templates.TemplateResponse("team_join.html", {
        "request": request,
        "user": current_user
    })


@router.post("/teams/join")
async def join_team(
    request: Request,
    invite_code: str = Form(...),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_auth)
):
    """Присоединение к команде по коду приглашения."""
    try:
        await TeamService.join_team_by_invite_code(
            session, invite_code, current_user.id)
        return RedirectResponse(url="/teams", status_code=303)

    except HTTPException as e:
        return templates.TemplateResponse("team_join.html", {
            "request": request,
            "user": current_user,
            "messages": [{"type": "error", "text": e.detail}]
        })


@router.get("/teams/{team_id}/edit", response_class=HTMLResponse)
async def edit_team_page(
    request: Request,
    team_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(UserRole.MANAGER))
):
    """Страница редактирования команды."""
    from utils.user_teams import get_user_with_teams
    from utils.validation import validate_user_is_team_owner

    user = await get_user_with_teams(session, current_user.id)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    team = await validate_user_is_team_owner(session, team_id, current_user.id)

    return templates.TemplateResponse("team_form.html", {
        "request": request,
        "user": user,
        "team": team
    })


@router.post("/teams/{team_id}/edit")
async def edit_team(
    request: Request,
    team_id: int,
    name: str = Form(...),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(UserRole.MANAGER))
):
    """Редактирование команды с валидацией."""
    try:
        await TeamService.update_team_name(
            session, team_id, name, current_user.id)
        return RedirectResponse(url="/teams", status_code=303)

    except HTTPException as e:
        from utils.user_teams import get_user_with_teams
        user = await get_user_with_teams(session, current_user.id)
        return render_error(
            request, "team_form.html", user, e.detail, e.status_code)


@router.post("/teams/{team_id}/members/{member_id}/remove")
async def remove_member(
    request: Request,
    team_id: int,
    member_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(UserRole.MANAGER))
):
    """Удаление участника из команды."""
    try:
        await TeamService.remove_member(
            session, team_id, uuid.UUID(member_id), current_user.id)
        return RedirectResponse(url="/teams", status_code=303)

    except HTTPException:
        return RedirectResponse(url="/teams", status_code=303)


@router.post("/teams/{team_id}/leave")
async def leave_team(
    request: Request,
    team_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(UserRole.MANAGER))
):
    """Выход из команды."""
    try:
        await TeamService.leave_team(session, team_id, current_user.id)
        return RedirectResponse(url="/teams", status_code=303)

    except HTTPException:
        return RedirectResponse(url="/teams", status_code=303)
