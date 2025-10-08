"""
CRUD операции для работы с базой данных.
"""

from .crud_task import task_crud
from .crud_team import team_crud
from .crud_meeting import meeting_crud
from .crud_comment import comment_crud
from .crud_evaluation import evaluation_crud
from .crud_calendar import calendar_crud

__all__ = [
    "task_crud",
    "team_crud",
    "meeting_crud",
    "comment_crud",
    "evaluation_crud",
    "calendar_crud",
]
