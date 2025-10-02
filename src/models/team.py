from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.database import Base
from .base import TimestampMixin


class Team(TimestampMixin, Base):
    """Модель команды/компании"""
    __tablename__ = "teams"
    name = Column(
        String(200),
        nullable=False,
        comment="Название команды"
    )
    description = Column(
        Text,
        nullable=True,
        comment="Описание команды"
    )
    invite_code = Column(
        String(50),
        unique=True,
        nullable=True,
        comment="Код приглашения"
    )
    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        comment="ID владельца"
    )
    owner = relationship("User", foreign_keys=[owner_id])
    members = relationship(
        "User",
        foreign_keys="User.team_id",
        back_populates="team"
    )
    tasks = relationship("Task", back_populates="team")
    meetings = relationship("Meeting", back_populates="team")

    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}')>"

    def get_members_count(self) -> int:
        return len(self.members) if self.members else 0

    def is_member(self, user_id) -> bool:
        return any(
            member.id == user_id for member in self.members
        ) if self.members else False
