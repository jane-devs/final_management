from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, Integer, Table
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.database import Base
from .base import TimestampMixin


meeting_participants = Table(
    'meeting_participants',
    Base.metadata,
    Column(
        'meeting_id',
        Integer,
        ForeignKey('meetings.id'),
        primary_key=True,
        comment="ID встречи"
    ),
    Column(
        'user_id',
        UUID(as_uuid=True),
        ForeignKey('users.id'),
        primary_key=True,
        comment="ID участника"
    ),
    comment="Связь между встречами и их участниками"
)


class Meeting(TimestampMixin, Base):
    """
    Модель встречи/мероприятия.
    """
    __tablename__ = "meetings"
    title = Column(
        String(200),
        nullable=False,
        comment="Название встречи"
    )
    description = Column(
        Text,
        nullable=True,
        comment="Описание встречи, повестка дня"
    )
    start_time = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="Дата и время начала встречи"
    )
    end_time = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="Дата и время окончания встречи"
    )
    location = Column(
        String(255),
        nullable=True,
        comment="Место проведения встречи или ссылка на видеоконференцию"
    )
    creator_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="ID создателя встречи"
    )
    team_id = Column(
        Integer,
        ForeignKey("teams.id"),
        nullable=False,
        comment="ID команды"
    )
    creator = relationship("User", back_populates="created_meetings")
    team = relationship("Team", back_populates="meetings")
    participants = relationship("User", secondary=meeting_participants)

    def __repr__(self):
        """Строковое представление встречи для отладки"""
        return f"<Meeting(id={self.id}, title='{self.title}')>"

    def get_duration_minutes(self) -> int:
        """Возвращает продолжительность встречи в минутах"""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() / 60)
        return 0

    def is_participant(self, user_id) -> bool:
        """Проверяет, является ли пользователь участником встречи"""
        return any(
            participant.id == user_id for participant in self.participants)

    def has_time_conflict(self, other_start_time, other_end_time) -> bool:
        """Проверяет, пересекается ли встреча по времени с другим событием"""
        return (
            self.start_time < other_end_time and
            self.end_time > other_start_time
        )
