"""
Эндпоинт дашборда.
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from models.user import User
from models.task import TaskStatus
from .dependencies import templates, require_auth
from crud import task_crud
from crud import meeting_crud


router = APIRouter()


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_auth)
):
    """Главная страница дашборда."""
    my_tasks = await task_crud.get_by_user(session, current_user.id)
    completed_tasks = [t for t in my_tasks if t.status == TaskStatus.COMPLETED]

    upcoming_meetings = await meeting_crud.get_upcoming(
        session, user_id=current_user.id, limit=5)
    recent_tasks = await task_crud.get_by_user(session, current_user.id)
    recent_tasks = recent_tasks[:5] if recent_tasks else []

    teams = current_user.teams or []
    team_members = 0
    if teams:
        team_members = len(teams[0].members)

    stats = {
        "my_tasks": len(my_tasks),
        "completed_tasks": len(completed_tasks),
        "upcoming_meetings": len(upcoming_meetings),
        "team_members": team_members,
        "teams": teams
    }

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user,
        "stats": stats,
        "recent_tasks": recent_tasks,
        "upcoming_meetings": upcoming_meetings
    })
