from fastapi import HTTPException
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Iterable


async def validate_team_and_participants(
    session: AsyncSession,
    user_id: uuid.UUID,
    team_id: int,
    participant_ids: Iterable[uuid.UUID]
) -> list[uuid.UUID]:
    """
    Проверяет:
      - что user_id состоит в team_id
      - что participant_ids являются участниками team_id
    Возвращает список валидных UUID участников.
    Бросает HTTPException(400/403) при ошибках.
    """
    from crud import team_crud

    team = await team_crud.get(session, team_id, relationships=["members"])
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    member_ids = {m.id for m in team.members}
    if user_id not in member_ids:
        raise HTTPException(
            status_code=403, detail="Вы не состоите в выбранной команде")

    validated = []
    for pid in participant_ids:
        if pid not in member_ids:
            raise HTTPException(status_code=400, detail=f"Пользователь {pid} не в команде")
        validated.append(pid)
    return validated
