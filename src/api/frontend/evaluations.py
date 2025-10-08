from fastapi import APIRouter, Depends, Request, Form, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import uuid

from core.database import get_async_session
from models.user import User, UserRole
from models.task import Task, TaskStatus
from models.team import Team
from crud import evaluation_crud
from crud import task_crud
from utils.form_helpers import render_template, render_error
from utils.user_teams import get_user_teams
from .dependencies import require_auth, require_role

router = APIRouter(tags=["Frontend - Evaluations"])


@router.get("/evaluations")
async def evaluations_page(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_auth)
):
    """
    Страница с оценками пользователя:
    - Статистика (средний балл, всего оценок, распределение)
    - Список последних 20 оценок
    """
    statistics = await evaluation_crud.get_user_statistics(session, current_user.id)

    evaluations = await evaluation_crud.get_by_user(
        session,
        user_id=current_user.id,
        skip=0,
        limit=20
    )

    for evaluation in evaluations:
        evaluation.score_description = evaluation.get_score_description()

    return render_template(
        request,
        "evaluations.html",
        user=current_user,
        statistics=statistics,
        evaluations=evaluations
    )


@router.get("/evaluations/new")
async def new_evaluation_page(
    request: Request,
    task_id: int = Query(..., description="ID завершенной задачи"),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(UserRole.MANAGER))
):
    """Страница создания оценки для конкретной задачи (только для менеджеров/админов)"""

    task = await task_crud.get(
        session,
        task_id,
        relationships=[
            selectinload(Task.assignee),
            selectinload(Task.team)
        ]
    )
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Можно оценить только завершенную задачу"
        )
    user_teams = await get_user_teams(session, current_user.id)
    user_team_ids = [t.id for t in user_teams]
    if task.team_id not in user_team_ids and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Вы не можете оценивать задачи чужих команд"
        )
    assignee = task.assignee
    if not assignee:
        raise HTTPException(
            status_code=400,
            detail="Задача не назначена никому"
        )
    return render_template(
        request,
        "evaluation_form.html",
        user=current_user,
        task=task,
        assignee=assignee
    )


@router.post("/evaluations/new")
async def create_evaluation(
    request: Request,
    task_id: int = Form(...),
    score: int = Form(...),
    comment: str = Form(None),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role(UserRole.MANAGER))
):
    task = await task_crud.get(
        session,
        task_id,
        relationships=[
            selectinload(Task.assignee),
            selectinload(Task.team)
        ]
    )
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Можно оценить только завершенную задачу")

    user_teams = await get_user_teams(session, current_user.id)
    if task.team_id not in [t.id for t in user_teams] and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Вы не можете оценивать задачи чужих команд")

    assignee = task.assignee
    if not assignee:
        raise HTTPException(status_code=400, detail="Задача не назначена никому")

    if not 1 <= score <= 5:
        raise HTTPException(status_code=400, detail="Оценка должна быть от 1 до 5")

    existing = await evaluation_crud.check_existing_evaluation(session, task_id, assignee.id)
    if existing:
        raise HTTPException(status_code=400, detail="Оценка для этой задачи и пользователя уже существует")

    from schemas.evaluation import EvaluationCreate
    evaluation_data = EvaluationCreate(
        task_id=task_id,
        user_id=assignee.id,
        score=score,
        comment=comment or None
    )
    if assignee.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Вы не можете оценивать задачи, назначенные себе"
        )
    await evaluation_crud.create_evaluation(session, evaluation_data, evaluator_id=current_user.id)

    return RedirectResponse(url=f"/tasks/{task_id}", status_code=303)

