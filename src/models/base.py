from sqlalchemy import Column, Integer, DateTime, func


class TimestampMixin:
    """
    Миксин для добавления базовых полей id, created_at, updated_at.
    Используется всеми моделями КРОМЕ User
    (у User эти поля есть в fastapi-users).
    """
    id = Column(
        Integer,
        primary_key=True,
        index=True,
        comment="Уникальный идентификатор записи"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата создания записи"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Дата последнего обновления"
    )
