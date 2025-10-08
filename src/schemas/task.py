from typing import Optional
from datetime import datetime
import uuid

from pydantic import BaseModel

from models.task import TaskStatus, TaskPriority
from .base import TimestampSchema


class TaskBase(BaseModel):
    """Базовые поля задачи"""
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.OPEN
    priority: TaskPriority = TaskPriority.MEDIUM
    deadline: Optional[datetime] = None


class TaskCreate(TaskBase):
    """Схема для создания задачи"""
    assignee_id: Optional[uuid.UUID] = None
    team_id: int


class TaskUpdate(BaseModel):
    """Схема для обновления задачи"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    deadline: Optional[datetime] = None
    assignee_id: Optional[uuid.UUID] = None


class TaskRead(TaskBase, TimestampSchema):
    """Схема для чтения данных задачи"""
    creator_id: uuid.UUID
    assignee_id: Optional[uuid.UUID] = None
    team_id: int
    completed_at: Optional[datetime] = None
