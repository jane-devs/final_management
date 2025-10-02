from typing import List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from core.fastapi_users import current_active_user
from core.dependencies import (
    get_task_with_access_check, get_existing_comment,
    get_comment_with_access_check, get_comment_with_edit_permission,
    get_comment_with_delete_permission, get_existing_task
)
from core.exceptions import CommentAccessDenied
from models.user import User
from models.task import Task
from models.comment import TaskComment
from schemas.comment import CommentCreate, CommentRead, CommentUpdate
from utils.crud_comment import comment_crud

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("/", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_data: CommentCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    """Создание комментария к задаче"""
    # Проверяем доступ к задаче через зависимость
    task = await get_existing_task(comment_data.task_id, session)
    if task.team_id != current_user.team_id and current_user.role.value != "admin":
        raise CommentAccessDenied("создание комментария к этой задаче")

    comment = await comment_crud.create_comment(
        session,
        comment_data,
        author_id=current_user.id
    )
    return comment


@router.get("/task/{task_id}", response_model=List[CommentRead])
async def get_task_comments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    task: Task = Depends(get_task_with_access_check),
    session: AsyncSession = Depends(get_async_session)
):
    """Получение комментариев к задаче"""
    comments = await comment_crud.get_by_task(
        session,
        task_id=task.id,
        skip=skip,
        limit=limit
    )
    return comments


@router.get("/my", response_model=List[CommentRead])
async def get_my_comments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    """Получение комментариев текущего пользователя"""
    comments = await comment_crud.get_by_author(
        session,
        author_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return comments


@router.get("/{comment_id}", response_model=CommentRead)
async def get_comment(
    comment: TaskComment = Depends(get_comment_with_access_check)
):
    """Получение конкретного комментария"""
    return comment


@router.patch("/{comment_id}", response_model=CommentRead)
async def update_comment(
    comment_data: CommentUpdate,
    comment: TaskComment = Depends(get_comment_with_edit_permission),
    session: AsyncSession = Depends(get_async_session)
):
    """Обновление комментария"""
    updated_comment = await comment_crud.update(
        session,
        db_obj=comment,
        obj_in=comment_data
    )
    return await comment_crud.get(
        session,
        updated_comment.id,
        relationships=["author", "task"]
    )


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment: TaskComment = Depends(get_comment_with_delete_permission),
    session: AsyncSession = Depends(get_async_session)
):
    """Удаление комментария"""
    await comment_crud.delete(session, id=comment.id)


@router.get("/task/{task_id}/count")
async def get_comments_count(
    task: Task = Depends(get_task_with_access_check),
    session: AsyncSession = Depends(get_async_session)
):
    """Получение количества комментариев к задаче"""
    count = await comment_crud.count_by_task(session, task.id)
    return {"task_id": task.id, "comments_count": count}
