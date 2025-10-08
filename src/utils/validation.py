from typing import Optional, List
from datetime import datetime
import uuid
import re
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.user import User
from models.team import Team
from models.task import Task
from models.meeting import Meeting


def validate_email_format(email: str) -> str:
    """
    Проверяет формат email адреса.
    """
    email = email.strip().lower()
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(pattern, email):
        raise HTTPException(status_code=400, detail="Некорректный формат email")

    if len(email) > 255:
        raise HTTPException(
            status_code=400, detail="Email слишком длинный (максимум 255 символов)")

    return email


async def validate_email_unique(
    session: AsyncSession,
    email: str,
    exclude_user_id: Optional[uuid.UUID] = None
) -> None:
    """
    Проверяет уникальность email в базе данных.
    """
    stmt = select(User).where(User.email == email)
    if exclude_user_id:
        stmt = stmt.where(User.id != exclude_user_id)

    result = await session.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email уже используется")


def validate_password_strength(password: str) -> str:
    """
    Проверяет надежность пароля.
    """
    if len(password) < 6:
        raise HTTPException(
            status_code=400, detail="Пароль должен быть не менее 6 символов")

    if len(password) > 128:
        raise HTTPException(
            status_code=400, detail="Пароль слишком длинный (максимум 128 символов)")

    return password


def validate_passwords_match(password: str, password_confirm: str) -> None:
    """
    Проверяет совпадение паролей.
    """
    if password != password_confirm:
        raise HTTPException(status_code=400, detail="Пароли не совпадают")


def validate_name_field(
    name: str,
    field_name: str = "Имя",
    min_length: int = 1,
    max_length: int = 100
) -> str:
    """
    Проверяет поле с именем (имя, фамилия и т.д.).
    """
    name = name.strip()

    if len(name) < min_length:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} должно содержать минимум {min_length} символ(ов)"
        )

    if len(name) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} слишком длинное (максимум {max_length} символов)"
        )

    return name


def validate_team_name(name: str) -> str:
    """
    Проверяет название команды.
    """
    return validate_name_field(name, field_name="Название команды", min_length=2, max_length=100)


def validate_title_field(title: str, field_name: str = "Заголовок") -> str:
    """
    Проверяет заголовок (задачи, встречи и т.д.).
    """
    return validate_name_field(
        title, field_name=field_name, min_length=3, max_length=255)


def parse_uuid_safe(
    uuid_str: Optional[str],
    field_name: str = "UUID"
) -> Optional[uuid.UUID]:
    """
    Безопасно парсит UUID строку.
    """
    if not uuid_str or not uuid_str.strip():
        return None

    try:
        return uuid.UUID(uuid_str.strip())
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=400, detail=f"Некорректный формат {field_name}")


def parse_datetime_safe(dt_str: Optional[str], field_name: str = "Дата/время") -> Optional[datetime]:
    """
    Безопасно парсит datetime строку.
    """
    if not dt_str or not dt_str.strip():
        return None

    try:
        return datetime.fromisoformat(dt_str.strip())
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=400, detail=f"Некорректный формат {field_name}")


def validate_datetime_range(
    start_time: datetime,
    end_time: datetime,
    allow_past: bool = False
) -> None:
    """
    Проверяет корректность временного диапазона.
    """
    if start_time >= end_time:
        raise HTTPException(
            status_code=400,
            detail="Время начала должно быть раньше времени окончания"
        )

    if not allow_past and start_time < datetime.now():
        raise HTTPException(
            status_code=400, detail="Время начала не может быть в прошлом")


def validate_deadline(deadline: datetime, allow_past: bool = False) -> None:
    """
    Проверяет корректность дедлайна.
    """
    if not allow_past and deadline < datetime.now():
        raise HTTPException(
            status_code=400, detail="Дедлайн не может быть в прошлом")


def parse_uuid_list(uuid_strings: List[str]) -> List[uuid.UUID]:
    """
    Парсит список UUID строк.
    """
    result = []
    for uuid_str in uuid_strings:
        if not uuid_str or not uuid_str.strip():
            continue

        parsed = parse_uuid_safe(uuid_str, field_name="идентификатор участника")
        if parsed:
            result.append(parsed)

    return result


async def validate_user_is_team_owner(
    session: AsyncSession,
    team_id: int,
    user_id: uuid.UUID
) -> Team:
    """
    Проверяет, что пользователь является владельцем команды.
    """
    from crud import team_crud

    team = await team_crud.get(session, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Команда не найдена")

    if team.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Только владелец команды может выполнить это действие")

    return team


async def validate_user_in_team(
    session: AsyncSession,
    team_id: int,
    user_id: uuid.UUID
) -> Team:
    """
    Проверяет, что пользователь состоит в команде.
    """
    from crud import team_crud

    team = await team_crud.get(session, team_id, relationships=["members"])
    if not team:
        raise HTTPException(status_code=404, detail="Команда не найдена")

    member_ids = {m.id for m in team.members}
    if user_id not in member_ids:
        raise HTTPException(status_code=403, detail="Вы не состоите в этой команде")

    return team


async def validate_user_has_teams(session: AsyncSession, user_id: uuid.UUID) -> List[Team]:
    """
    Проверяет, что пользователь состоит хотя бы в одной команде.
    """
    from utils.user_teams import get_user_teams

    teams = await get_user_teams(session, user_id)
    if not teams:
        raise HTTPException(status_code=400, detail="Вы не состоите ни в одной команде")

    return teams


async def validate_task_access(
    session: AsyncSession,
    task_id: int,
    user_id: uuid.UUID
) -> Task:
    """
    Проверяет доступ пользователя к задаче (должен быть в команде задачи).
    """
    from crud import task_crud

    task = await task_crud.get(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    await validate_user_in_team(session, task.team_id, user_id)

    return task


async def validate_meeting_access(
    session: AsyncSession,
    meeting_id: int,
    user_id: uuid.UUID
) -> Meeting:
    """
    Проверяет доступ пользователя к встрече (должен быть создателем или участником).
    """
    from crud import meeting_crud

    meeting = await meeting_crud.get(session, meeting_id, relationships=["participants"])
    if not meeting:
        raise HTTPException(status_code=404, detail="Встреча не найдена")

    participant_ids = {p.id for p in meeting.participants}
    if meeting.creator_id != user_id and user_id not in participant_ids:
        raise HTTPException(status_code=403, detail="У вас нет доступа к этой встрече")

    return meeting


async def validate_assignee_in_team(
    session: AsyncSession,
    assignee_id: Optional[uuid.UUID],
    team_id: int
) -> None:
    """
    Проверяет, что назначенный пользователь (assignee) состоит в команде.
    """
    if assignee_id is None:
        return 

    from crud import team_crud

    team = await team_crud.get(session, team_id, relationships=["members"])
    if not team:
        raise HTTPException(status_code=404, detail="Команда не найдена")

    member_ids = {m.id for m in team.members}
    if assignee_id not in member_ids:
        raise HTTPException(
            status_code=400,
            detail="Назначенный пользователь не состоит в команде задачи"
        )


async def validate_and_parse_team_id(
    session: AsyncSession,
    team_id_str: Optional[str],
    user_id: uuid.UUID,
    default_to_user_teams: bool = True
) -> int:
    """
    Валидирует и парсит team_id. Если не указан - берет первую команду пользователя.
    """
    from utils.user_teams import get_user_teams

    teams = await get_user_teams(session, user_id)
    if not teams:
        raise HTTPException(status_code=400, detail="Вы не состоите ни в одной команде")
    if not team_id_str and default_to_user_teams:
        return teams[0].id

    try:
        team_id = int(team_id_str)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Некорректный идентификатор команды")

    team_ids = {t.id for t in teams}
    if team_id not in team_ids:
        raise HTTPException(status_code=403, detail="Вы не состоите в выбранной команде")

    return team_id


def validate_content_length(content: str, field_name: str = "Содержимое", max_length: int = 5000) -> str:
    """
    Проверяет длину текстового контента.
    """
    content = content.strip()

    if not content:
        raise HTTPException(status_code=400, detail=f"{field_name} не может быть пустым")

    if len(content) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} слишком длинное (максимум {max_length} символов)"
        )

    return content
