from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Column, String, Enum, DateTime, func
from sqlalchemy.orm import relationship
from passlib.context import CryptContext
import enum

from core.database import Base
from models.team import team_members

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(enum.Enum):
    """Роли пользователей в системе"""
    USER = "user"
    MANAGER = "manager"
    ADMIN = "admin"


class User(Base, SQLAlchemyBaseUserTableUUID):
    """
    Модель пользователя системы, совместимая с FastAPI Users.
    """
    __tablename__ = "users"

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
    # team_id = Column(
    #     Integer,
    #     ForeignKey("teams.id"),
    #     nullable=True,
    #     comment="ID команды"
    # )
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
    teams = relationship("Team", secondary=team_members, back_populates="members")
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
    hashed_password = Column(String, nullable=False)
    _password = None

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role.value}')>" # noqa

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, plain_password: str):
        self._password = plain_password
        self.hashed_password = pwd_context.hash(plain_password)

    def has_permission(self, required_role: UserRole) -> bool:
        role_hierarchy = {
            UserRole.USER: 1,
            UserRole.MANAGER: 2,
            UserRole.ADMIN: 3
        }
        return role_hierarchy[self.role] >= role_hierarchy[required_role]
