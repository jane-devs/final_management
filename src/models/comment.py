from sqlalchemy import Column, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.database import Base
from .base import TimestampMixin


class TaskComment(TimestampMixin, Base):
    """
    Модель комментария к задаче.
    Простая система комментирования внутри задач.
    """
    __tablename__ = "task_comments"
    content = Column(
        Text,
        nullable=False,
        comment="Текст комментария"
    )
    task_id = Column(
        Integer,
        ForeignKey("tasks.id"),
        nullable=False,
        comment="ID задачи, к которой относится комментарий"
    )
    author_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="ID автора комментария"
    )
    task = relationship("Task", back_populates="comments")
    author = relationship("User")

    def __repr__(self):
        """Строковое представление комментария для отладки"""
        return f"<TaskComment(id={self.id}, task_id={self.task_id}, author_id={self.author_id})>" # noqa