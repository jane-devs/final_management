from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from core.fastapi_users import current_active_user
from core.dependencies import (
    require_manager_or_admin_role, get_task_with_access_check,
    get_evaluation_with_access_check,
    get_evaluation_with_edit_permission, get_evaluation_with_delete_permission,
    get_existing_task
)
from core.exceptions import (
    ValidationError, EvaluationAccessDenied, PermissionDenied
)
from models.user import User, UserRole
from models.task import Task, TaskStatus
from models.evaluation import Evaluation
from schemas.evaluation import (
    EvaluationCreate, EvaluationRead, EvaluationUpdate
)
from crud import evaluation_crud

router = APIRouter(prefix="/evaluations", tags=["Оценки"])


@router.post(
    "/",
    response_model=EvaluationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать оценку",
    description="Создание оценки выполненной задачи (только менеджер/админ)"
)
async def create_evaluation(
    evaluation_data: EvaluationCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_manager_or_admin_role)
):
    task = await get_existing_task(evaluation_data.task_id, session)

    if task.status != TaskStatus.COMPLETED:
        raise ValidationError(
            "Можно оценить только завершенную задачу",
            field="task_id"
        )
    if task.team_id != current_user.team_id and current_user.role != UserRole.ADMIN:
        raise EvaluationAccessDenied("создание оценки для этой задачи")
    if evaluation_data.user_id == current_user.id:
        raise ValidationError(
            "Вы не можете оценивать самого себя",
            field="user_id"
        )
    existing = await evaluation_crud.check_existing_evaluation(
        session,
        evaluation_data.task_id,
        evaluation_data.user_id
    )
    if existing:
        raise EvaluationAccessDenied("оценка для этой задачи и пользователя уже существует")

    evaluation = await evaluation_crud.create_evaluation(
        session,
        evaluation_data,
        evaluator_id=current_user.id
    )
    return evaluation


@router.get(
    "/task/{task_id}",
    response_model=List[EvaluationRead],
    summary="Оценки задачи",
    description="Получение оценок задачи"
)
async def get_task_evaluations(
    task: Task = Depends(get_task_with_access_check),
    session: AsyncSession = Depends(get_async_session)
):
    evaluations = await evaluation_crud.get_by_task(session, task.id)
    return evaluations


@router.get(
    "/user/{user_id}",
    response_model=List[EvaluationRead],
    summary="Оценки пользователя",
    description="Получение оценок пользователя"
)
async def get_user_evaluations(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    if (
        str(current_user.id) != user_id and
            current_user.role not in [UserRole.MANAGER, UserRole.ADMIN]
    ):
        raise PermissionDenied("просматривать чужие оценки")
    evaluations = await evaluation_crud.get_by_user(
        session,
        user_id=user_id,
        skip=skip,
        limit=limit
    )
    return evaluations


@router.get(
    "/my",
    response_model=List[EvaluationRead],
    summary="Мои оценки",
    description="Получение оценок текущего пользователя"
)
async def get_my_evaluations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    evaluations = await evaluation_crud.get_by_user(
        session,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return evaluations


@router.get(
    "/my-given",
    response_model=List[EvaluationRead],
    summary="Выставленные оценки",
    description="Получение оценок, выставленных текущим пользователем"
)
async def get_my_given_evaluations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_manager_or_admin_role)
):
    evaluations = await evaluation_crud.get_by_evaluator(
        session,
        evaluator_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return evaluations


@router.get(
    "/user/{user_id}/statistics",
    summary="Статистика оценок пользователя",
    description="Получение статистики оценок пользователя"
)
async def get_user_evaluation_statistics(
    user_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    if (
        str(current_user.id) != user_id and
            current_user.role not in [UserRole.MANAGER, UserRole.ADMIN]
    ):
        raise PermissionDenied("просматривать чужую статистику")
    stats = await evaluation_crud.get_user_statistics(session, user_id)
    return {
        "user_id": user_id,
        "statistics": stats
    }


@router.get(
    "/my/statistics",
    summary="Моя статистика оценок",
    description="Получение статистики оценок текущего пользователя"
)
async def get_my_statistics(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    stats = await evaluation_crud.get_user_statistics(session, current_user.id)
    return {
        "user_id": str(current_user.id),
        "statistics": stats
    }


@router.get(
    "/user/{user_id}/average",
    summary="Средняя оценка пользователя",
    description="Получение средней оценки пользователя"
)
async def get_user_average_score(
    user_id: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    if (
        str(current_user.id) != user_id and
            current_user.role not in [UserRole.MANAGER, UserRole.ADMIN]
    ):
        raise PermissionDenied("просматривать чужие оценки")
    average = await evaluation_crud.get_user_average_score(session, user_id)
    return {
        "user_id": user_id,
        "average_score": round(average, 2) if average else 0
    }


@router.get(
    "/{evaluation_id}",
    response_model=EvaluationRead,
    summary="Получить оценку",
    description="Получение конкретной оценки"
)
async def get_evaluation(
    evaluation: Evaluation = Depends(get_evaluation_with_access_check)
):
    return evaluation


@router.patch(
    "/{evaluation_id}",
    response_model=EvaluationRead,
    summary="Обновить оценку",
    description="Обновление оценки (только менеджер/админ)"
)
async def update_evaluation(
    evaluation_data: EvaluationUpdate,
    evaluation: Evaluation = Depends(get_evaluation_with_edit_permission),
    session: AsyncSession = Depends(get_async_session)
):
    updated_evaluation = await evaluation_crud.update(
        session,
        db_obj=evaluation,
        obj_in=evaluation_data
    )
    return await evaluation_crud.get(
        session,
        updated_evaluation.id,
        relationships=["user", "evaluator", "task"]
    )


@router.delete(
    "/{evaluation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить оценку",
    description="Удаление оценки (только менеджер/админ)"
)
async def delete_evaluation(
    evaluation: Evaluation = Depends(get_evaluation_with_delete_permission),
    session: AsyncSession = Depends(get_async_session)
):
    await evaluation_crud.delete(session, id=evaluation.id)


@router.get(
    "/user/{user_id}/average-by-period",
    summary="Средняя оценка за период",
    description="Получение средней оценки пользователя за период"
)
async def get_user_average_by_period(
    user_id: str,
    start_date: Optional[datetime] = Query(None, description="Начало периода (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Конец периода (ISO format)"),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    import uuid as uuid_lib

    if (
        str(current_user.id) != user_id and
            current_user.role not in [UserRole.MANAGER, UserRole.ADMIN]
    ):
        raise PermissionDenied("просматривать чужие оценки")

    try:
        user_uuid = uuid_lib.UUID(user_id)
    except ValueError:
        from core.exceptions import UserNotFound
        raise UserNotFound(user_id)

    average = await evaluation_crud.get_average_score_by_period(
        session,
        user_uuid,
        start_date=start_date,
        end_date=end_date
    )

    return {
        "user_id": user_id,
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "average_score": round(average, 2) if average else 0
    }


@router.get(
    "/my/average-by-period",
    summary="Моя средняя оценка за период",
    description="Получение средней оценки текущего пользователя за период"
)
async def get_my_average_by_period(
    start_date: Optional[datetime] = Query(None, description="Начало периода (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Конец периода (ISO format)"),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    average = await evaluation_crud.get_average_score_by_period(
        session,
        current_user.id,
        start_date=start_date,
        end_date=end_date
    )

    return {
        "user_id": str(current_user.id),
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "average_score": round(average, 2) if average else 0
    }
