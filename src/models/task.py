from sqlalchemy import (
    Column, String, Text, DateTime, Enum, ForeignKey, Integer
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from core.database import Base
from .base import TimestampMixin


class TaskStatus(enum.Enum):
    """
    Статусы выполнения задач.
    """
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskPriority(enum.Enum):
    """
    Приоритеты задач.
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task(TimestampMixin, Base):
    """
    Модель задачи.
    """
    __tablename__ = "tasks"
    title = Column(
        String(200),
        nullable=False,
        comment="Заголовок задачи"
    )
    description = Column(
        Text,
        nullable=True,
        comment="Подробное описание задачи"
    )
    status = Column(
        Enum(TaskStatus),
        default=TaskStatus.OPEN,
        comment="Текущий статус задачи"
    )
    priority = Column(
        Enum(TaskPriority),
        default=TaskPriority.MEDIUM,
        comment="Приоритет задачи"
    )

    # Временные рамки
    deadline = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Крайний срок выполнения задачи"
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Дата и время завершения задачи"
    )
    creator_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="ID создателя задачи"
    )
    assignee_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        comment="ID исполнителя задачи"
    )
    team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False,
        comment="ID команды, к которой относится задача"
    )
    creator = relationship(
        "User",
        foreign_keys=[creator_id],
        back_populates="created_tasks"
    )
    assignee = relationship(
        "User",
        foreign_keys=[assignee_id],
        back_populates="assigned_tasks"
    )
    team = relationship("Team", back_populates="tasks")
    evaluations = relationship("Evaluation", back_populates="task")
    comments = relationship("TaskComment", back_populates="task")

    def __repr__(self):
        """Строковое представление задачи для отладки"""
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status.value}')>" # noqa

    def is_overdue(self) -> bool:
        """Проверяет, просрочена ли задача"""
        if not self.deadline or self.status == TaskStatus.COMPLETED:
            return False
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) > self.deadline

    def can_be_completed(self) -> bool:
        """Проверяет, может ли задача быть завершена (есть ли исполнитель)"""
        return self.assignee_id is not None
