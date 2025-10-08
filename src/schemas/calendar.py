from pydantic import BaseModel
from typing import List
from datetime import date

from .task import TaskRead
from .meeting import MeetingRead


class CalendarDay(BaseModel):
    """Данные календаря за один день"""
    date: date
    tasks: List[TaskRead] = []
    meetings: List[MeetingRead] = []

    class Config:
        from_attributes = True


class CalendarMonth(BaseModel):
    """Данные календаря за месяц"""
    year: int
    month: int
    days: List[CalendarDay] = []

    class Config:
        from_attributes = True
