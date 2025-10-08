from datetime import date, datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from core.fastapi_users import current_active_user
from models.user import User
from schemas.calendar import CalendarDay, CalendarMonth
from crud import calendar_crud

router = APIRouter(prefix="/calendar", tags=["Календарь"])


@router.get(
    "/month",
    response_model=CalendarMonth,
    summary="Календарь за месяц",
    description="Получить календарь за месяц с задачами и встречами. Возвращает все дни месяца с задачами (у которых дедлайн в этот день) и встречами (которые начинаются в этот день)."
)
async def get_calendar_month(
    year: int = Query(..., ge=2000, le=2100, description="Год"),
    month: int = Query(..., ge=1, le=12, description="Месяц (1-12)"),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    return await calendar_crud.get_month(
        session,
        user_id=current_user.id,
        year=year,
        month=month
    )


@router.get(
    "/day",
    response_model=CalendarDay,
    summary="Календарь за день",
    description="Получить календарь за день с задачами и встречами. Возвращает задачи с дедлайном в этот день и встречи, начинающиеся в этот день."
)
async def get_calendar_day(
    target_date: date = Query(..., description="Дата (YYYY-MM-DD)"),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    return await calendar_crud.get_day(
        session,
        user_id=current_user.id,
        target_date=target_date
    )


@router.get(
    "/today",
    response_model=CalendarDay,
    summary="Календарь на сегодня",
    description="Получить календарь на сегодня с задачами и встречами. Возвращает задачи с дедлайном сегодня и встречи на сегодня."
)
async def get_calendar_today(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    today = date.today()
    return await calendar_crud.get_day(
        session,
        user_id=current_user.id,
        target_date=today
    )


@router.get(
    "/current-month",
    response_model=CalendarMonth,
    summary="Календарь текущего месяца",
    description="Получить календарь на текущий месяц с задачами и встречами."
)
async def get_current_month_calendar(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    now = datetime.now()
    return await calendar_crud.get_month(
        session,
        user_id=current_user.id,
        year=now.year,
        month=now.month
    )
