from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from core.database import get_async_session
from models.user import User, UserRole
from models.task import Task, TaskStatus, TaskPriority
from .dependencies import templates, require_auth, require_role
from services import TaskService
from crud import task_crud
from crud import comment_crud
from utils.user_teams import get_user_teams, get_user_with_teams
from utils.form_helpers import render_error
from crud.crud_team import team_crud


router = APIRouter()


@router.get("/tasks", response_class=HTMLResponse)
async def tasks_page(
    request: Request,
    status: str = None,
    priority: str = None,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_auth)
):
    """Список задач."""
    teams = await get_user_teams(
        session, current_user.id, load_team_members=False)

    if not teams:
        tasks = []
    else:
        tasks = []
        for t in teams:
            t_tasks = await task_crud.get_by_team(
                session,
                t.id,
                status=TaskStatus(status) if status else None,
                priority=TaskPriority(priority) if priority else None
            )
            if t_tasks:
                tasks.extend(t_tasks)

    return templates.TemplateResponse("tasks.html", {
        "request": request,
        "user": current_user,
        "tasks": tasks,
        "status": status,
        "priority": priority
    })


@router.get("/tasks/new", response_class=HTMLResponse)
async def new_task_page(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(UserRole.MANAGER))
):
    """Страница создания задачи."""
    teams = await get_user_teams(
        session, current_user.id, load_team_members=True)
    team_members: List[User] = teams[0].members if teams else []
    selected_team_id = request.query_params.get("team_id")
    selected_team = None
    if selected_team_id:
        selected_team = await team_crud.get(session, int(selected_team_id))
    team_members = selected_team.members if selected_team else []

    return templates.TemplateResponse("task_form.html", {
        "request": request,
        "user": current_user,
        "teams": teams,
        "team_members": team_members,
        "selected_team": selected_team
    })


@router.post("/tasks/new")
async def create_task(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    status: str = Form(...),
    priority: str = Form(...),
    team_id: int = Form(...),
    assignee_id: str | None = Form(None),
    deadline: str | None = Form(None),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(UserRole.MANAGER))
):
    """Создание новой задачи с валидацией."""
    try:
        await TaskService.create_task(
            session, title, description, status, priority,
            team_id, current_user.id, assignee_id, deadline
        )
        return RedirectResponse(url="/tasks", status_code=303)

    except HTTPException as e:
        teams = await get_user_teams(
            session, current_user.id, load_team_members=True)
        return render_error(
            request, "task_form.html", current_user, e.detail, e.status_code,
            teams=teams, team_members=teams[0].members if teams else []
        )


@router.get("/tasks/{task_id}", response_class=HTMLResponse)
async def task_detail(
    request: Request,
    task_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_auth)
):
    """Детальная информация о задаче."""
    user = await get_user_with_teams(session, current_user.id)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    task_res = await session.execute(
        select(Task)
        .options(selectinload(Task.creator), selectinload(Task.assignee))
        .where(Task.id == task_id)
    )
    task = task_res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    comments = await comment_crud.get_by_task(session, task_id)

    # Получаем оценки задачи
    from crud import evaluation_crud
    evaluations = await evaluation_crud.get_by_task(session, task_id)
    for evaluation in evaluations:
        evaluation.score_description = evaluation.get_score_description()

    return templates.TemplateResponse("task_detail.html", {
        "request": request,
        "user": user,
        "task": task,
        "comments": comments,
        "evaluations": evaluations
    })


@router.post("/tasks/{task_id}/complete")
async def complete_task(
    request: Request,
    task_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_auth)
):
    """Завершение задачи."""
    await TaskService.complete_task(session, task_id)
    return RedirectResponse(url=f"/tasks/{task_id}", status_code=303)


@router.get("/tasks/{task_id}/edit", response_class=HTMLResponse)
async def edit_task_page(
    request: Request,
    task_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(UserRole.MANAGER))
):
    """Страница редактирования задачи."""
    user = await get_user_with_teams(
        session, current_user.id, load_team_members=True)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    task_result = await session.execute(
        select(Task)
        .options(selectinload(Task.creator), selectinload(Task.assignee))
        .where(Task.id == task_id)
    )
    task = task_result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    teams = user.teams or []
    team_members = teams[0].members if teams else []

    return templates.TemplateResponse("task_form.html", {
        "request": request,
        "user": user,
        "task": task,
        "teams": teams,
        "team_members": team_members
    })


@router.post("/tasks/{task_id}/edit")
async def edit_task(
    request: Request,
    task_id: int,
    title: str = Form(...),
    description: str = Form(...),
    status: str = Form(...),
    priority: str = Form(...),
    assignee_id: str = Form(None),
    deadline: str = Form(None),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(UserRole.MANAGER))
):
    """Редактирование задачи с валидацией."""
    try:
        task = await TaskService.update_task(
            session,
            task_id,
            title,
            description,
            status,
            priority,
            assignee_id,
            deadline
        )
        return RedirectResponse(url=f"/tasks/{task_id}", status_code=303)

    except HTTPException as e:
        user = await get_user_with_teams(
            session, current_user.id, load_team_members=True)
        task = await task_crud.get(session, task_id)
        return render_error(
            request,
            "task_form.html",
            user,
            e.detail,
            e.status_code,
            task=task
        )


@router.post("/tasks/{task_id}/comments")
async def add_comment(
    task_id: int,
    content: str = Form(...),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_auth)
):
    """Добавление комментария к задаче."""
    try:
        await TaskService.add_comment(
            session, task_id, content, current_user.id)
        return RedirectResponse(url=f"/tasks/{task_id}", status_code=303)

    except HTTPException:
        return RedirectResponse(url=f"/tasks/{task_id}", status_code=303)
