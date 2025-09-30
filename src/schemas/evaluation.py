from pydantic import BaseModel, validator
from typing import Optional
import uuid
from .base import TimestampSchema
from .user import UserRead
from .task import TaskRead


class EvaluationBase(BaseModel):
    """Базовые поля оценки"""
    score: int
    comment: Optional[str] = None


class EvaluationCreate(EvaluationBase):
    """Схема для создания оценки"""
    task_id: int
    user_id: uuid.UUID


class EvaluationUpdate(BaseModel):
    """Схема для обновления оценки"""
    score: Optional[int] = None
    comment: Optional[str] = None


class EvaluationRead(EvaluationBase, TimestampSchema):
    """Схема для чтения данных оценки"""
    task_id: int
    user_id: uuid.UUID
    evaluator_id: uuid.UUID
    user: Optional[UserRead] = None
    evaluator: Optional[UserRead] = None
    task: Optional[TaskRead] = None

    @validator('score')
    def score_must_be_valid(cls, v):
        if not 1 <= v <= 5:
            raise ValueError(
                f'Допустимая оценка от 1 до 5. Текущая оценка: {v}.'
            )
        return v
