from datetime import datetime
import uuid

from pydantic import BaseModel


class BaseSchema(BaseModel):
    """Базовая схема с общими полями"""

    class Config:
        from_attributes = True


class TimestampSchema(BaseSchema):
    """Схема с временными метками для моделей с Integer ID"""
    id: int
    created_at: datetime
    updated_at: datetime


class UserTimestampSchema(BaseSchema):
    """Схема с временными метками для User модели"""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
