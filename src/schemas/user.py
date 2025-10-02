from fastapi_users import schemas
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
import uuid
from models.user import UserRole


class UserRead(schemas.BaseUser[uuid.UUID]):
    """Схема чтения пользователя."""
    first_name: str
    last_name: str
    role: UserRole
    team_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class UserCreate(schemas.BaseUserCreate):
    """Схема создания пользователя."""
    first_name: str
    last_name: str


class UserUpdate(schemas.BaseUserUpdate):
    """Схема обновления пользователя."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None
    team_id: Optional[int] = None


class UserLogin(BaseModel):
    """Схема для авторизации."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Схема для JWT токена."""
    access_token: str
    token_type: str = "bearer"
