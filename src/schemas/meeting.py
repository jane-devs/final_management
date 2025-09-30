from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
import uuid
from .base import TimestampSchema
from .user import UserRead


class MeetingBase(BaseModel):
    """Базовые поля встречи"""
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None


class MeetingCreate(MeetingBase):
    """Схема для создания встречи"""
    team_id: int
    participant_ids: Optional[List[uuid.UUID]] = []


class MeetingUpdate(BaseModel):
    """Схема для обновления встречи"""
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    participant_ids: Optional[List[uuid.UUID]] = []


class MeetingRead(MeetingBase, TimestampSchema):
    """Схема для чтения данных встречи"""
    creator_id: uuid.UUID
    team_id: int
    creator: Optional[UserRead] = None
    participants: Optional[List[UserRead]] = []

    @validator('end_time')
    def end_time_must_be_after_start_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError(
                'Время окончания не должно быть раньше времени начала встречи.'
            )
        return v
