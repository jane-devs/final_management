from typing import Optional, List
import uuid

from pydantic import BaseModel

from .base import TimestampSchema
from .user import UserRead


class TeamBase(BaseModel):
    """Базовые поля команды."""
    name: str
    description: Optional[str] = None
    invite_code: Optional[str] = None


class TeamCreate(TeamBase):
    """Схема для создания команды."""
    pass


class TeamUpdate(BaseModel):
    """Схема для обновления команды."""
    name: Optional[str] = None
    description: Optional[str] = None
    invite_code: Optional[str] = None


class TeamRead(TeamBase, TimestampSchema):
    """Схема для чтения данных команды"""
    owner_id: uuid.UUID
    members: Optional[List[UserRead]] = []


class TeamInvite(BaseModel):
    """Схема для приглашения в команду по коду"""
    invite_code: str
