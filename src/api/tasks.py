import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from core.fastapi_users import current_active_user
from core.dependencies import (
    require_team_member_for_tasks, get_task_with_access_check,
    get_task_with_edit_permission, get_task_with_delete_permission,
    get_task_with_assign_permission
)
from models.user import User
from models.task import Task, TaskStatus, TaskPriority
from schemas.task import TaskCreate, TaskRead, TaskUpdate
from utils.crud_task import task_crud

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_team_member_for_tasks)
):
    """Создание новой задачи"""
    return await task_crud.create_task_with_validation(
        session, task_data, current_user.id, current_user.team_id
    )


@router.get("/", response_model=List[TaskRead])
async def get_tasks(
    status_filter: Optional[TaskStatus] = Query(None),
    priority_filter: Optional[TaskPriority] = Query(None),
    assignee_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_team_member_for_tasks)
):
    """Получение списка задач с фильтрами"""
    return await task_crud.get_by_team(
        session,
        current_user.team_id,
        status=status_filter,
        priority=priority_filter,
        assignee_id=assignee_id
    )


@router.get("/my", response_model=List[TaskRead])
async def get_my_tasks(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    """Получение задач текущего пользователя"""
    return await task_crud.get_by_user(session, current_user.id)


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task: Task = Depends(get_task_with_access_check)
):
    """Получение конкретной задачи"""
    return task


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_data: TaskUpdate,
    task: Task = Depends(get_task_with_edit_permission),
    session: AsyncSession = Depends(get_async_session)
):
    """Обновление задачи"""
    return await task_crud.update_task_with_validation(
        session, task, task_data
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task: Task = Depends(get_task_with_delete_permission),
    session: AsyncSession = Depends(get_async_session)
):
    """Удаление задачи"""
    await session.delete(task)
    await session.commit()


@router.post("/{task_id}/assign/{user_id}", response_model=TaskRead)
async def assign_task(
    user_id: str,
    task: Task = Depends(get_task_with_assign_permission),
    session: AsyncSession = Depends(get_async_session)
):
    """Назначение задачи пользователю"""
    import uuid
    return await task_crud.assign_task_with_validation(
        session, task, uuid.UUID(user_id)
    )


@router.post("/{task_id}/complete", response_model=TaskRead)
async def complete_task(
    task: Task = Depends(get_task_with_edit_permission),
    session: AsyncSession = Depends(get_async_session)
):
    """Отметить задачу как выполненную"""
    return await task_crud.complete_task_with_validation(session, task)


@router.get("/overdue", response_model=List[TaskRead])
async def get_overdue_tasks(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_team_member_for_tasks)
):
    """Получить просроченные задачи команды"""
    return await task_crud.get_overdue(session, current_user.team_id)


@router.get("/statistics")
async def get_team_statistics(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_team_member_for_tasks)
):
    """Получить статистику по задачам команды"""
    return await task_crud.get_statistics(session, current_user.team_id)
