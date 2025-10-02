from typing import Optional
import uuid
from pydantic import BaseModel

from .base import TimestampSchema
from .user import UserRead


class CommentBase(BaseModel):
    """Базовые поля комментария"""
    content: str


class CommentCreate(CommentBase):
    """Схема для создания комментария"""
    task_id: int


class CommentUpdate(BaseModel):
    """Схема для обновления комментария"""
    content: str


class CommentRead(CommentBase, TimestampSchema):
    """Схема для чтения данных комментария"""
    task_id: int
    author_id: uuid.UUID
    author: Optional[UserRead] = None
