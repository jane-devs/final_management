from typing import List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from core.fastapi_users import current_active_user
from core.dependencies import (
    get_task_with_access_check, get_comment_with_access_check,
    get_comment_with_edit_permission,
    get_comment_with_delete_permission, get_existing_task
)
from core.exceptions import CommentAccessDenied
from models.user import User
from models.task import Task
from models.comment import TaskComment
from schemas.comment import CommentCreate, CommentRead, CommentUpdate
from crud import comment_crud

router = APIRouter(prefix="/comments", tags=["Комментарии"])


@router.post(
    "/",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать комментарий",
    description="Создание комментария к задаче (только админ, постановщик или исполнитель)"
)
async def create_comment(
    comment_data: CommentCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    from models.user import UserRole

    task = await get_existing_task(comment_data.task_id, session)

    has_access = (
        current_user.role == UserRole.ADMIN or
        task.creator_id == current_user.id or
        task.assignee_id == current_user.id
    )
    if not has_access:
        raise CommentAccessDenied("комментировать могут только админ, постановщик задачи или исполнитель")

    comment = await comment_crud.create_comment(
        session,
        comment_data,
        author_id=current_user.id
    )
    return comment


@router.get(
    "/task/{task_id}",
    response_model=List[CommentRead],
    summary="Комментарии к задаче",
    description="Получение комментариев к задаче (только админ, постановщик или исполнитель)"
)
async def get_task_comments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    task: Task = Depends(get_task_with_access_check),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    from models.user import UserRole

    has_access = (
        current_user.role == UserRole.ADMIN or
        task.creator_id == current_user.id or
        task.assignee_id == current_user.id
    )

    if not has_access:
        raise CommentAccessDenied("просматривать комментарии могут только админ, постановщик задачи или исполнитель")

    comments = await comment_crud.get_by_task(
        session,
        task_id=task.id,
        skip=skip,
        limit=limit
    )
    return comments


@router.get(
    "/my",
    response_model=List[CommentRead],
    summary="Мои комментарии",
    description="Получение комментариев текущего пользователя"
)
async def get_my_comments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    comments = await comment_crud.get_by_author(
        session,
        author_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return comments


@router.get(
    "/{comment_id}",
    response_model=CommentRead,
    summary="Получить комментарий",
    description="Получение конкретного комментария"
)
async def get_comment(
    comment: TaskComment = Depends(get_comment_with_access_check)
):
    return comment


@router.patch(
    "/{comment_id}",
    response_model=CommentRead,
    summary="Обновить комментарий",
    description="Обновление комментария"
)
async def update_comment(
    comment_data: CommentUpdate,
    comment: TaskComment = Depends(get_comment_with_edit_permission),
    session: AsyncSession = Depends(get_async_session)
):
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


@router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить комментарий",
    description="Удаление комментария"
)
async def delete_comment(
    comment: TaskComment = Depends(get_comment_with_delete_permission),
    session: AsyncSession = Depends(get_async_session)
):
    await comment_crud.delete(session, id=comment.id)


@router.get(
    "/task/{task_id}/count",
    summary="Количество комментариев",
    description="Получение количества комментариев к задаче"
)
async def get_comments_count(
    task: Task = Depends(get_task_with_access_check),
    session: AsyncSession = Depends(get_async_session)
):
    count = await comment_crud.count_by_task(session, task.id)
    return {"task_id": task.id, "comments_count": count}
