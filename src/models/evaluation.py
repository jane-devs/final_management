from sqlalchemy import Column, Integer, Text, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.database import Base
from .base import TimestampMixin


class Evaluation(TimestampMixin, Base):
    """
    Модель оценки выполненной задачи.
    Позволяет руководителям оценивать качество работы сотрудников.
    """
    __tablename__ = "evaluations"
    score = Column(
        Integer,
        nullable=False,
        comment="Оценка от 1 до 5 баллов"
    )
    comment = Column(
        Text,
        nullable=True,
        comment="Комментарий к оценке от руководителя"
    )
    task_id = Column(
        Integer,
        ForeignKey("tasks.id"),
        nullable=False,
        comment="ID оцениваемой задачи"
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="ID оцениваемого пользователя"
    )
    evaluator_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="ID того, кто ставит оценку"
    )
    task = relationship(
        "Task",
        back_populates="evaluations"
    )
    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="evaluations"
    )
    evaluator = relationship(
        "User",
        foreign_keys=[evaluator_id]
    )
    __table_args__ = (
        CheckConstraint(
            'score >= 1 AND score <= 5', name='valid_score_range'),
        CheckConstraint(
            'user_id != evaluator_id', name='cannot_evaluate_self'),
    )

    def __repr__(self):
        """Строковое представление оценки для отладки"""
        return f"<Evaluation(id={self.id}, task_id={self.task_id}, score={self.score})>" # noqa

    def get_score_description(self) -> str:
        """Возвращает текстовое описание оценки"""
        descriptions = {
            1: "Неудовлетворительно",
            2: "Удовлетворительно",
            3: "Хорошо",
            4: "Очень хорошо",
            5: "Отлично"
        }
        return descriptions.get(self.score, "Неизвестная оценка")
