from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from models.user import User
from models.task import TaskStatus
from .dependencies import templates, require_auth
from services import UserService
from crud import task_crud
from crud import meeting_crud
from utils.user_teams import get_user_with_teams


router = APIRouter()


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_auth)
):
    """Страница профиля пользователя."""
    user = await get_user_with_teams(session, current_user.id)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    tasks = await task_crud.get_by_user(session, current_user.id)
    completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
    meetings = await meeting_crud.get_upcoming(
        session,
        user_id=current_user.id,
        limit=100
    )

    stats = {
        "total_tasks": len(tasks),
        "completed_tasks": len(completed),
        "total_meetings": len(meetings),
        "avg_score": None
    }

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user,
        "stats": stats
    })


@router.get("/profile/edit", response_class=HTMLResponse)
async def profile_edit_page(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_auth)
):
    """Страница редактирования профиля."""
    user = await get_user_with_teams(session, current_user.id)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse("profile_edit.html", {
        "request": request,
        "user": user
    })


@router.post("/profile/edit")
async def profile_edit(
    request: Request,
    email: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_auth)
):
    """Обработка редактирования профиля с валидацией."""
    try:
        user = await UserService.update_profile(
            session, current_user.id, email, first_name, last_name
        )
        return RedirectResponse(url="/profile", status_code=303)

    except HTTPException as e:
        user = await get_user_with_teams(session, current_user.id)
        return templates.TemplateResponse("profile_edit.html", {
            "request": request,
            "user": user,
            "messages": [{"type": "error", "text": e.detail}]
        })


@router.get("/profile/password", response_class=HTMLResponse)
async def profile_password_page(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_auth)
):
    """Страница изменения пароля."""
    user = await get_user_with_teams(session, current_user.id)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse("profile_password.html", {
        "request": request,
        "user": user
    })


@router.post("/profile/password")
async def profile_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    new_password_confirm: str = Form(...),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_auth)
):
    """Обработка изменения пароля с валидацией."""
    user = await get_user_with_teams(session, current_user.id)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    try:
        await UserService.change_password(
            session,
            current_user.id,
            current_password,
            new_password,
            new_password_confirm
        )
        return RedirectResponse(url="/profile", status_code=303)

    except HTTPException as e:
        return templates.TemplateResponse("profile_password.html", {
            "request": request,
            "user": user,
            "messages": [{"type": "error", "text": e.detail}]
        })
