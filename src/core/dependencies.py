from typing import Annotated
from fastapi import Depends, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import get_async_session
from core.fastapi_users import current_active_user
from models.user import User, UserRole
from models.team import Team
from models.task import Task
from models.meeting import Meeting
from models.comment import TaskComment
from models.evaluation import Evaluation
from crud import team_crud
from core.exceptions import (
    TeamNotFound, TeamAccessDenied, TeamOwnershipRequired,
    NotInTeam, PermissionDenied, TaskNotFound, TaskAccessDenied,
    MeetingNotFound, MeetingAccessDenied,
    CommentNotFound, CommentAccessDenied, EvaluationNotFound,
    EvaluationAccessDenied, UserNotActive, UserNotVerified
)


async def get_existing_team(
    team_id: Annotated[int, Path(description="ID команды")],
    session: AsyncSession = Depends(get_async_session)
) -> Team:
    """Зависимость для получения существующей команды"""
    team = await team_crud.get(session, team_id, relationships=["members"])
    if not team:
        raise TeamNotFound(team_id)
    return team


async def get_team_with_access_check(
    team: Team = Depends(get_existing_team),
    current_user: User = Depends(current_active_user)
) -> Team:
    """Зависимость для проверки доступа к команде (админ или член команды)"""
    if (
        current_user.role != UserRole.ADMIN and
            current_user.team_id != team.id
    ):
        raise TeamAccessDenied()
    return team


async def get_team_with_owner_check(
    team: Team = Depends(get_existing_team),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
) -> Team:
    """Зависимость для проверки прав владельца команды"""
    if current_user.role != UserRole.ADMIN:
        is_owner = await team_crud.is_owner(session, team.id, current_user.id)
        if not is_owner:
            raise TeamOwnershipRequired()
    return team


async def check_user_in_team(
    team_id: Annotated[int, Path(description="ID команды")],
    current_user: User = Depends(current_active_user)
) -> int:
    """Зависимость для проверки, что пользователь состоит в этой команде"""
    if current_user.team_id != team_id:
        raise NotInTeam(team_id)
    return team_id


class RequireAdmin:
    """Зависимость для проверки прав администратора"""
    def __call__(
        self,
        current_user: User = Depends(current_active_user)
    ) -> User:
        if current_user.role != UserRole.ADMIN:
            raise TeamAccessDenied("Требуются права администратора")
        return current_user


class RequireTeamMember:
    """Зависимость для проверки членства в команде"""
    def __init__(self, allow_admin: bool = True):
        self.allow_admin = allow_admin

    def __call__(
        self,
        team: Team = Depends(get_existing_team),
        current_user: User = Depends(current_active_user),
        session: AsyncSession = Depends(get_async_session)
    ) -> tuple[Team, User]:
        if self.allow_admin and current_user.role == UserRole.ADMIN:
            return team, current_user

        if current_user.team_id != team.id:
            raise TeamAccessDenied()

        return team, current_user


class RequireTeamOwner:
    """Зависимость для проверки прав владельца команды"""
    def __init__(self, allow_admin: bool = True):
        self.allow_admin = allow_admin

    async def __call__(
        self,
        team: Team = Depends(get_existing_team),
        current_user: User = Depends(current_active_user),
        session: AsyncSession = Depends(get_async_session)
    ) -> tuple[Team, User]:
        if self.allow_admin and current_user.role == UserRole.ADMIN:
            return team, current_user

        is_owner = await team_crud.is_owner(session, team.id, current_user.id)
        if not is_owner:
            raise TeamOwnershipRequired()

        return team, current_user


async def require_active_user(
    current_user: User = Depends(current_active_user)
) -> User:
    """Требует активного пользователя"""
    if not current_user.is_active:
        raise UserNotActive()
    return current_user


async def require_verified_user(
        current_user: User = Depends(current_active_user)
) -> User:
    """Требует верифицированного пользователя"""
    if not current_user.is_verified:
        raise UserNotVerified()
    return current_user


class RequireRole:
    """Зависимость для проверки конкретной роли"""
    def __init__(self, required_roles: list[UserRole] | UserRole):
        if isinstance(required_roles, UserRole):
            self.required_roles = [required_roles]
        else:
            self.required_roles = required_roles

    def __call__(
        self, current_user: User = Depends(current_active_user)
    ) -> User:
        if current_user.role not in self.required_roles:
            role_names = [role.value for role in self.required_roles]
            raise PermissionDenied(" или ".join(role_names))
        return current_user


require_admin = RequireAdmin()
require_team_member = RequireTeamMember()
require_team_owner = RequireTeamOwner()
require_team_member_strict = RequireTeamMember(allow_admin=False)
require_team_owner_strict = RequireTeamOwner(allow_admin=False)
require_admin_only = RequireRole(UserRole.ADMIN)
require_manager_only = RequireRole(UserRole.MANAGER)
require_member_only = RequireRole(UserRole.USER)
require_manager_or_admin_role = RequireRole([UserRole.MANAGER, UserRole.ADMIN])


async def require_team_member_for_tasks(
    current_user: User = Depends(current_active_user)
) -> User:
    """Требует, чтобы пользователь состоял в команде для работы с задачами"""
    if not current_user.team_id:
        raise NotInTeam()
    return current_user


async def get_existing_task(
    task_id: Annotated[int, Path(description="ID задачи")],
    session: AsyncSession = Depends(get_async_session)
) -> Task:
    """Зависимость для получения существующей задачи"""
    result = await session.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise TaskNotFound(task_id)
    return task


async def get_task_with_access_check(
    task: Task = Depends(get_existing_task),
    current_user: User = Depends(current_active_user)
) -> Task:
    """Зависимость для проверки доступа к задаче (админ или член команды)"""
    if (
        current_user.role != UserRole.ADMIN and
            task.team_id != current_user.team_id
    ):
        raise TaskAccessDenied()
    return task


class RequireTaskPermission:
    """Зависимость для проверки конкретных прав на задачу"""
    def __init__(self, actions: list[str]):
        self.actions = actions

    async def __call__(
        self,
        task: Task = Depends(get_existing_task),
        current_user: User = Depends(current_active_user)
    ) -> Task:
        if current_user.role == UserRole.ADMIN:
            return task

        if task.team_id != current_user.team_id:
            raise TaskAccessDenied()

        if task.creator_id == current_user.id:
            return task

        if task.assignee_id == current_user.id:
            if "delete" in self.actions:
                raise TaskAccessDenied("удаление")
            return task

        if current_user.role == UserRole.MANAGER:
            return task

        action_str = ", ".join(self.actions)
        raise TaskAccessDenied(action_str)


get_task_with_edit_permission = RequireTaskPermission(["edit"])
get_task_with_delete_permission = RequireTaskPermission(["delete"])
get_task_with_assign_permission = RequireTaskPermission(["assign"])

require_task_read = RequireTaskPermission(["read"])


async def get_existing_meeting(
    meeting_id: Annotated[int, Path(description="ID встречи")],
    session: AsyncSession = Depends(get_async_session)
) -> Meeting:
    """Зависимость для получения существующей встречи"""
    result = await session.execute(
        select(Meeting)
        .options(selectinload(Meeting.creator), selectinload(
            Meeting.participants))
        .where(Meeting.id == meeting_id)
    )
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise MeetingNotFound(meeting_id)
    return meeting


async def get_meeting_with_access_check(
    meeting: Meeting = Depends(get_existing_meeting),
    current_user: User = Depends(current_active_user)
) -> Meeting:
    """Зависимость для проверки доступа к встрече (админ или член команды)"""
    if (
        current_user.role != UserRole.ADMIN and
            meeting.team_id != current_user.team_id
    ):
        raise MeetingAccessDenied()
    return meeting


async def get_meeting_with_edit_permission(
    meeting: Meeting = Depends(get_meeting_with_access_check),
    current_user: User = Depends(current_active_user)
) -> Meeting:
    """Зависимость для проверки прав редактирования встречи"""
    can_edit = (
        meeting.creator_id == current_user.id or
        current_user.role in [UserRole.MANAGER, UserRole.ADMIN]
    )
    if not can_edit:
        raise MeetingAccessDenied("редактирование")
    return meeting


async def get_meeting_with_delete_permission(
    meeting: Meeting = Depends(get_meeting_with_access_check),
    current_user: User = Depends(current_active_user)
) -> Meeting:
    """Зависимость для проверки прав удаления встречи"""
    can_delete = (
        meeting.creator_id == current_user.id or
        current_user.role in [UserRole.MANAGER, UserRole.ADMIN]
    )
    if not can_delete:
        raise MeetingAccessDenied("удаление")
    return meeting


async def get_existing_comment(
    comment_id: Annotated[int, Path(description="ID комментария")],
    session: AsyncSession = Depends(get_async_session)
) -> TaskComment:
    """Зависимость для получения существующего комментария"""
    result = await session.execute(
        select(TaskComment)
        .options(selectinload(TaskComment.author), selectinload(
            TaskComment.task))
        .where(TaskComment.id == comment_id)
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise CommentNotFound(comment_id)
    return comment


async def get_comment_with_access_check(
    comment: TaskComment = Depends(get_existing_comment),
    current_user: User = Depends(current_active_user)
) -> TaskComment:
    """Зависимость для проверки доступа к комментарию (через задачу)"""
    if (current_user.role != UserRole.ADMIN and
            comment.task.team_id != current_user.team_id):
        raise CommentAccessDenied()
    return comment


async def get_comment_with_edit_permission(
    comment: TaskComment = Depends(get_comment_with_access_check),
    current_user: User = Depends(current_active_user)
) -> TaskComment:
    """Зависимость для проверки прав редактирования комментария"""
    can_edit = (
        comment.author_id == current_user.id or
        current_user.role == UserRole.ADMIN
    )
    if not can_edit:
        raise CommentAccessDenied("редактирование")
    return comment


async def get_comment_with_delete_permission(
    comment: TaskComment = Depends(get_comment_with_access_check),
    current_user: User = Depends(current_active_user)
) -> TaskComment:
    """Зависимость для проверки прав удаления комментария"""
    can_delete = (
        comment.author_id == current_user.id or
        current_user.role in [UserRole.MANAGER, UserRole.ADMIN]
    )
    if not can_delete:
        raise CommentAccessDenied("удаление")
    return comment


async def get_existing_evaluation(
    evaluation_id: Annotated[int, Path(description="ID оценки")],
    session: AsyncSession = Depends(get_async_session)
) -> Evaluation:
    """Зависимость для получения существующей оценки"""
    result = await session.execute(
        select(Evaluation)
        .options(selectinload(Evaluation.evaluator), selectinload(
            Evaluation.user), selectinload(Evaluation.task))
        .where(Evaluation.id == evaluation_id)
    )
    evaluation = result.scalar_one_or_none()
    if not evaluation:
        raise EvaluationNotFound(evaluation_id)
    return evaluation


async def get_evaluation_with_access_check(
    evaluation: Evaluation = Depends(get_existing_evaluation),
    current_user: User = Depends(current_active_user)
) -> Evaluation:
    """Зависимость для проверки доступа к оценке (через задачу)"""
    if (current_user.role not in [UserRole.MANAGER, UserRole.ADMIN] and
            evaluation.user_id != current_user.id):
        raise EvaluationAccessDenied()
    return evaluation


async def get_evaluation_with_edit_permission(
    evaluation: Evaluation = Depends(get_evaluation_with_access_check),
    current_user: User = Depends(current_active_user)
) -> Evaluation:
    """Зависимость для проверки прав редактирования оценки"""
    can_edit = (
        evaluation.evaluator_id == current_user.id or
        current_user.role in [UserRole.MANAGER, UserRole.ADMIN]
    )
    if not can_edit:
        raise EvaluationAccessDenied("редактирование")
    return evaluation


async def get_evaluation_with_delete_permission(
    evaluation: Evaluation = Depends(get_evaluation_with_access_check),
    current_user: User = Depends(current_active_user)
) -> Evaluation:
    """Зависимость для проверки прав удаления оценки"""
    can_delete = (
        evaluation.evaluator_id == current_user.id or
        current_user.role in [UserRole.MANAGER, UserRole.ADMIN]
    )
    if not can_delete:
        raise EvaluationAccessDenied("удаление")
    return evaluation
