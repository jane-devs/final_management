import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from models.task import Task, TaskStatus, TaskPriority
from schemas.task import TaskCreate, TaskUpdate
from schemas.comment import CommentCreate
from crud import task_crud
from crud import comment_crud
from utils.validation import (
    validate_title_field,
    validate_content_length,
    validate_user_in_team,
    parse_uuid_safe,
    parse_datetime_safe,
    validate_deadline
)


class TaskService:
    """Сервис для управления задачами."""

    @staticmethod
    async def create_task(
        session: AsyncSession,
        title: str,
        description: str,
        status: str,
        priority: str,
        team_id: int,
        creator_id: uuid.UUID,
        assignee_id: Optional[str] = None,
        deadline: Optional[str] = None
    ) -> Task:
        """
        Создает новую задачу с валидацией.

        Args:
            session: Сессия базы данных
            title: Заголовок задачи
            description: Описание
            status: Статус (строка)
            priority: Приоритет (строка)
            team_id: ID команды
            creator_id: ID создателя
            assignee_id: ID исполнителя (опционально)
            deadline: Дедлайн (опционально)

        Returns:
            Task: Созданная задача
        """
        title = validate_title_field(title, "Заголовок задачи")
        description = validate_content_length(description, "Описание", max_length=5000)
        await validate_user_in_team(session, team_id, creator_id)

        assignee_uuid = parse_uuid_safe(assignee_id, "ID исполнителя")
        deadline_dt = parse_datetime_safe(deadline, "Дедлайн")

        if deadline_dt:
            validate_deadline(deadline_dt, allow_past=True)

        task_data = TaskCreate(
            title=title,
            description=description,
            status=TaskStatus(status),
            priority=TaskPriority(priority),
            assignee_id=assignee_uuid,
            deadline=deadline_dt,
            team_id=team_id
        )

        task = await task_crud.create_task_with_validation(
            session, task_data, creator_id, team_id
        )
        return task

    @staticmethod
    async def update_task(
        session: AsyncSession,
        task_id: int,
        title: str,
        description: str,
        status: str,
        priority: str,
        assignee_id: Optional[str] = None,
        deadline: Optional[str] = None
    ) -> Task:
        """
        Обновляет задачу с валидацией.

        Args:
            session: Сессия базы данных
            task_id: ID задачи
            title: Заголовок
            description: Описание
            status: Статус
            priority: Приоритет
            assignee_id: ID исполнителя
            deadline: Дедлайн

        Returns:
            Task: Обновленная задача
        """
        task = await task_crud.get(session, task_id)
        if not task:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Task not found")

        title = validate_title_field(title, "Заголовок задачи")
        description = validate_content_length(
            description, "Описание", max_length=5000)
        assignee_uuid = parse_uuid_safe(assignee_id, "ID исполнителя")
        deadline_dt = parse_datetime_safe(deadline, "Дедлайн")

        if deadline_dt:
            validate_deadline(deadline_dt, allow_past=True)

        update_data = TaskUpdate(
            title=title,
            description=description,
            status=TaskStatus(status),
            priority=TaskPriority(priority),
            assignee_id=assignee_uuid,
            deadline=deadline_dt
        )

        await task_crud.update_task_with_validation(session, task, update_data)
        return task

    @staticmethod
    async def complete_task(
        session: AsyncSession,
        task_id: int
    ) -> Optional[Task]:
        """
        Завершает задачу.

        Args:
            session: Сессия базы данных
            task_id: ID задачи

        Returns:
            Optional[Task]: Завершенная задача или None
        """
        task = await task_crud.get(session, task_id)
        if task:
            await task_crud.complete_task_with_validation(session, task)
        return task

    @staticmethod
    async def add_comment(
        session: AsyncSession,
        task_id: int,
        content: str,
        author_id: uuid.UUID
    ) -> None:
        """
        Добавляет комментарий к задаче.

        Args:
            session: Сессия базы данных
            task_id: ID задачи
            content: Текст комментария
            author_id: ID автора
        """
        content = validate_content_length(
            content, "Комментарий", max_length=2000)
        comment_data = CommentCreate(task_id=task_id, content=content)
        await comment_crud.create_comment(session, comment_data, author_id)
