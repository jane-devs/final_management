from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from core.database import get_async_session
from models.user import User, UserRole
from .dependencies import templates, require_auth, require_role
from services import MeetingService
from crud import meeting_crud
from utils.user_teams import get_user_teams, get_user_with_teams
from utils.form_helpers import render_error


router = APIRouter()


@router.get("/meetings", response_class=HTMLResponse)
async def meetings_page(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_auth)
):
    """Список встреч."""
    meetings = await meeting_crud.get_upcoming(
        session, user_id=current_user.id, limit=20)

    return templates.TemplateResponse("meetings.html", {
        "request": request,
        "user": current_user,
        "meetings": meetings
    })


@router.get("/meetings/new", response_class=HTMLResponse)
async def new_meeting_page(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(UserRole.MANAGER))
):
    """Страница создания встречи."""
    teams = await get_user_teams(
        session, current_user.id, load_team_members=True)
    team_members = teams[0].members if teams else []

    return templates.TemplateResponse("meeting_form.html", {
        "request": request,
        "user": current_user,
        "teams": teams,
        "team_members": team_members
    })


@router.post("/meetings/new")
async def create_meeting(
    request: Request,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    start_time: str = Form(...),
    end_time: str = Form(...),
    location: Optional[str] = Form(None),
    team_id: Optional[int] = Form(None),
    participant_ids: list[str] = Form([]),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(UserRole.MANAGER))
):
    """Создание новой встречи с валидацией."""
    try:
        await MeetingService.create_meeting(
            session, title, start_time, end_time, current_user.id,
            description, location, team_id, participant_ids
        )
        return RedirectResponse(url="/meetings", status_code=303)

    except HTTPException as e:
        teams = await get_user_teams(
            session, current_user.id, load_team_members=True)
        return render_error(
            request, "meeting_form.html",
            current_user,
            e.detail,
            e.status_code,
            teams=teams,
            team_members=teams[0].members if teams else []
        )


@router.get("/meetings/{meeting_id}", response_class=HTMLResponse)
async def meeting_detail(
    request: Request,
    meeting_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_auth)
):
    """Детальная информация о встрече."""
    meeting = await meeting_crud.get(
        session,
        meeting_id,
        relationships=["creator", "participants"]
    )
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    return templates.TemplateResponse("meeting_detail.html", {
        "request": request,
        "user": current_user,
        "meeting": meeting
    })


@router.get("/meetings/{meeting_id}/edit", response_class=HTMLResponse)
async def edit_meeting_page(
    request: Request,
    meeting_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(UserRole.MANAGER))
):
    """Страница редактирования встречи."""
    user = await get_user_with_teams(
        session, current_user.id, load_team_members=True)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    meeting = await meeting_crud.get(
        session,
        meeting_id,
        relationships=["creator", "participants"]
    )
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    teams = user.teams or []
    team_members = teams[0].members if teams else []

    return templates.TemplateResponse("meeting_form.html", {
        "request": request,
        "user": user,
        "meeting": meeting,
        "teams": teams,
        "team_members": team_members
    })


@router.post("/meetings/{meeting_id}/edit")
async def edit_meeting(
    request: Request,
    meeting_id: int,
    title: str = Form(...),
    description: str = Form(None),
    start_time: str = Form(...),
    end_time: str = Form(...),
    location: str = Form(None),
    participant_ids: list = Form([]),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(UserRole.MANAGER))
):
    """Редактирование встречи с валидацией."""
    try:
        await MeetingService.update_meeting(
            session, meeting_id, title, start_time, end_time, current_user.id,
            description, location, participant_ids
        )
        return RedirectResponse(url=f"/meetings/{meeting_id}", status_code=303)

    except HTTPException as e:
        user = await get_user_with_teams(
            session, current_user.id, load_team_members=True)
        meeting = await meeting_crud.get(
            session,
            meeting_id,
            relationships=["creator", "participants"]
        )
        return render_error(
            request, "meeting_form.html", user, e.detail, e.status_code,
            meeting=meeting
        )
