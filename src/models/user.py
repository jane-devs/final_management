from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Column, String, Enum, ForeignKey, Integer, DateTime, func, MetaData
from sqlalchemy.orm import relationship
import enum

from core.database import Base


class UserRole(enum.Enum):
    """Роли пользователей в системе"""
    USER = "user"
    MANAGER = "manager"
    ADMIN = "admin"


class User(Base, SQLAlchemyBaseUserTableUUID):
    """
    Модель пользователя системы, совместимая с FastAPI Users.
    Наследуется от SQLAlchemyBaseUserTable для интеграции с FastAPI Users.
    """
    __tablename__ = "users"

    # Дополнительные поля (базовые поля id, email, hashed_password, is_active, is_superuser, is_verified наследуются от SQLAlchemyBaseUserTable)
    first_name = Column(
        String(100),
        nullable=False,
        comment="Имя пользователя"
    )
    last_name = Column(
        String(100),
        nullable=False,
        comment="Фамилия пользователя"
    )
    role = Column(
        Enum(UserRole),
        default=UserRole.USER,
        comment="Роль пользователя"
    )
    team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=True,
        comment="ID команды"
    )

    # Временные метки (добавляем вручную, так как SQLAlchemyBaseUserTable их не включает)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата создания"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Дата обновления"
    )

    team = relationship("Team", back_populates="members")
    created_tasks = relationship(
        "Task",
        foreign_keys="Task.creator_id",
        back_populates="creator"
    )
    assigned_tasks = relationship(
        "Task",
        foreign_keys="Task.assignee_id",
        back_populates="assignee"
    )
    evaluations = relationship(
        "Evaluation",
        foreign_keys="Evaluation.user_id",
        back_populates="user"
    )
    created_meetings = relationship("Meeting", back_populates="creator")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role.value}')>" # noqa

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def has_permission(self, required_role: UserRole) -> bool:
        role_hierarchy = {
            UserRole.USER: 1,
            UserRole.MANAGER: 2,
            UserRole.ADMIN: 3
        }
        return role_hierarchy[self.role] >= role_hierarchy[required_role]
