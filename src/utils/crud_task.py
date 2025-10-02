"""CRUD операции для задач"""
from typing import Optional, List
from datetime import datetime, timezone
import uuid
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.exceptions import (
    AssigneeNotInTeam, UserNotFound, TaskAlreadyCompleted
)
from models.task import Task, TaskStatus, TaskPriority
from models.user import User
from schemas.task import TaskCreate, TaskUpdate
from .crud_base import CRUDBase


class CRUDTask(CRUDBase[Task, TaskCreate, TaskUpdate]):
    """CRUD операции для модели Task"""

    async def get_by_team(
        self,
        session: AsyncSession,
        team_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assignee_id: Optional[uuid.UUID] = None
    ) -> List[Task]:
        """Получить задачи команды с фильтрами."""
        query = select(Task).options(
            selectinload(Task.creator),
            selectinload(Task.assignee)
        ).where(Task.team_id == team_id)
        if status:
            query = query.where(Task.status == status)
        if priority:
            query = query.where(Task.priority == priority)
        if assignee_id:
            query = query.where(Task.assignee_id == assignee_id)
        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        return result.scalars().all()

    async def get_by_user(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        include_created: bool = True,
        include_assigned: bool = True
    ) -> List[Task]:
        """Получить задачи пользователя."""
        conditions = []
        if include_created:
            conditions.append(Task.creator_id == user_id)
        if include_assigned:
            conditions.append(Task.assignee_id == user_id)
        if not conditions:
            return []
        query = select(Task).options(
            selectinload(Task.creator),
            selectinload(Task.assignee)
        ).where(or_(*conditions))
        result = await session.execute(query)
        return result.scalars().all()

    async def get_overdue(
        self,
        session: AsyncSession,
        team_id: Optional[int] = None
    ) -> List[Task]:
        """Получить просроченные задачи."""
        now = datetime.now(timezone.utc)
        query = select(Task).options(
            selectinload(Task.creator),
            selectinload(Task.assignee)
        ).where(
            and_(
                Task.deadline < now,
                Task.status != TaskStatus.COMPLETED
            )
        )
        if team_id:
            query = query.where(Task.team_id == team_id)
        result = await session.execute(query)
        return result.scalars().all()

    async def get_by_status(
        self,
        session: AsyncSession,
        status: TaskStatus,
        team_id: Optional[int] = None
    ) -> List[Task]:
        """Получить задачи по статусу."""
        query = select(Task).options(
            selectinload(Task.creator),
            selectinload(Task.assignee)
        ).where(Task.status == status)
        if team_id:
            query = query.where(Task.team_id == team_id)
        result = await session.execute(query)
        return result.scalars().all()

    async def assign_to_user(
        self,
        session: AsyncSession,
        task_id: int,
        user_id: uuid.UUID
    ) -> Task:
        """Назначить задачу пользователю."""
        task = await self.get(session, task_id)
        if task:
            task.assignee_id = user_id
            await session.commit()
            await session.refresh(task, ["creator", "assignee"])
        return task

    async def complete_task(
        self,
        session: AsyncSession,
        task_id: int
    ) -> Task:
        """Отметить задачу как выполненную."""
        task = await self.get(session, task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(task, ["creator", "assignee"])
        return task

    async def reopen_task(
        self,
        session: AsyncSession,
        task_id: int
    ) -> Task:
        """Переоткрыть задачу."""
        task = await self.get(session, task_id)
        if task:
            task.status = TaskStatus.OPEN
            task.completed_at = None
            await session.commit()
            await session.refresh(task, ["creator", "assignee"])
        return task

    async def get_statistics(
        self,
        session: AsyncSession,
        team_id: int
    ) -> dict:
        """Получить статистику по задачам команды."""
        all_tasks = await self.get_by_team(session, team_id, limit=1000)
        stats = {
            "total": len(all_tasks),
            "by_status": {
                "open": 0,
                "in_progress": 0,
                "completed": 0
            },
            "by_priority": {
                "low": 0,
                "medium": 0,
                "high": 0,
                "urgent": 0
            },
            "overdue": 0,
            "without_assignee": 0
        }
        now = datetime.now(timezone.utc)
        for task in all_tasks:
            stats["by_status"][task.status.value] += 1
            stats["by_priority"][task.priority.value] += 1
            if task.deadline and task.deadline < now and (
                task.status != TaskStatus.COMPLETED
            ):
                stats["overdue"] += 1
            if not task.assignee_id:
                stats["without_assignee"] += 1
        return stats

    async def create_task_with_validation(
        self,
        session: AsyncSession,
        task_data: TaskCreate,
        creator_id: uuid.UUID,
        creator_team_id: int
    ) -> Task:
        """Создать задачу с валидацией прав и команды."""
        # Если указан assignee, проверяем что он в той же команде
        if task_data.assignee_id:
            assignee_result = await session.execute(
                select(User).where(User.id == task_data.assignee_id)
            )
            assignee = assignee_result.scalar_one_or_none()
            if not assignee:
                raise UserNotFound(str(task_data.assignee_id))
            if assignee.team_id != creator_team_id:
                raise AssigneeNotInTeam()

        # Создаем задачу, team_id берется автоматически из текущего пользователя
        task = Task(
            **task_data.model_dump(),
            creator_id=creator_id,
            team_id=creator_team_id
        )
        session.add(task)
        await session.commit()
        await session.refresh(task, ["creator", "assignee"])
        return task

    async def assign_task_with_validation(
        self,
        session: AsyncSession,
        task: Task,
        assignee_id: uuid.UUID
    ) -> Task:
        """Назначить задачу пользователю с валидацией."""
        # Проверяем, что пользователь существует
        assignee_result = await session.execute(
            select(User).where(User.id == assignee_id)
        )
        assignee = assignee_result.scalar_one_or_none()
        if not assignee:
            raise UserNotFound(str(assignee_id))

        # Проверяем, что пользователь в той же команде
        if assignee.team_id != task.team_id:
            raise AssigneeNotInTeam()

        # Назначаем задачу
        task.assignee_id = assignee_id
        await session.commit()
        await session.refresh(task, ["creator", "assignee"])
        return task

    async def complete_task_with_validation(
        self,
        session: AsyncSession,
        task: Task
    ) -> Task:
        """Отметить задачу как выполненную с валидацией."""
        if task.status == TaskStatus.COMPLETED:
            raise TaskAlreadyCompleted()

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(task, ["creator", "assignee"])
        return task

    async def update_task_with_validation(
        self,
        session: AsyncSession,
        task: Task,
        update_data: TaskUpdate
    ) -> Task:
        """Обновить задачу с валидацией."""
        update_dict = update_data.model_dump(exclude_unset=True)

        # Если меняется assignee, проверяем валидность
        if "assignee_id" in update_dict and update_dict["assignee_id"]:
            assignee_result = await session.execute(
                select(User).where(User.id == update_dict["assignee_id"])
            )
            assignee = assignee_result.scalar_one_or_none()
            if not assignee:
                raise UserNotFound(str(update_dict["assignee_id"]))
            if assignee.team_id != task.team_id:
                raise AssigneeNotInTeam()

        # Если статус меняется на "выполнено", устанавливаем время
        if (update_dict.get("status") == TaskStatus.COMPLETED and
            task.status != TaskStatus.COMPLETED):
            task.completed_at = datetime.now(timezone.utc)

        # Применяем изменения
        for field, value in update_dict.items():
            setattr(task, field, value)

        await session.commit()
        await session.refresh(task, ["creator", "assignee"])
        return task


task_crud = CRUDTask(Task)
