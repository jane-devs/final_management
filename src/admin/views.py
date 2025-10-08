from sqladmin import ModelView

from models.user import User
from models.team import Team
from models.task import Task
from models.meeting import Meeting
from models.evaluation import Evaluation
from models.comment import TaskComment


class UserAdmin(ModelView, model=User):
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"
    column_list = [
        User.id,
        User.email,
        User.first_name,
        User.last_name,
        User.role,
        User.is_active,
        User.is_verified,
        User.created_at
    ]
    column_searchable_list = [User.email, User.first_name, User.last_name]
    column_filters = [User.role, User.is_active]
    column_default_sort = [(User.created_at, True)]
    column_details_exclude_list = [User.hashed_password]
    form_excluded_columns = [User.created_at, User.updated_at]
    page_size = 50


class TeamAdmin(ModelView, model=Team):
    name = "Команда"
    name_plural = "Команды"
    icon = "fa-solid fa-users"
    column_list = [
        Team.id,
        Team.name,
        Team.owner_id,
        Team.invite_code,
        Team.created_at
    ]
    column_searchable_list = [Team.name, Team.invite_code]
    column_filters = [Team.owner_id]
    column_default_sort = [(Team.created_at, True)]
    form_excluded_columns = [Team.created_at, Team.updated_at]
    page_size = 50


class TaskAdmin(ModelView, model=Task):
    name = "Задача"
    name_plural = "Задачи"
    icon = "fa-solid fa-tasks"
    column_list = [
        Task.id,
        Task.title,
        Task.status,
        Task.priority,
        Task.creator_id,
        Task.assignee_id,
        Task.team_id,
        Task.deadline,
        Task.created_at
    ]
    column_searchable_list = [Task.title, Task.description]
    column_filters = [
        Task.status,
        Task.priority,
        Task.team_id,
        Task.creator_id,
        Task.assignee_id
    ]
    column_default_sort = [(Task.created_at, True)]
    form_excluded_columns = [Task.created_at, Task.updated_at, Task.completed_at]
    page_size = 50


class MeetingAdmin(ModelView, model=Meeting):
    name = "Встреча"
    name_plural = "Встречи"
    icon = "fa-solid fa-calendar"
    column_list = [
        Meeting.id,
        Meeting.title,
        Meeting.start_time,
        Meeting.end_time,
        Meeting.creator_id,
        Meeting.team_id,
        Meeting.created_at
    ]
    column_searchable_list = [Meeting.title, Meeting.description, Meeting.location]
    column_filters = [Meeting.team_id, Meeting.creator_id, Meeting.start_time]
    column_default_sort = [(Meeting.start_time, False)]
    form_excluded_columns = [Meeting.created_at, Meeting.updated_at]
    page_size = 50


class EvaluationAdmin(ModelView, model=Evaluation):
    name = "Оценка"
    name_plural = "Оценки"
    icon = "fa-solid fa-star"
    column_list = [
        Evaluation.id,
        Evaluation.score,
        Evaluation.task_id,
        Evaluation.user_id,
        Evaluation.evaluator_id,
        Evaluation.created_at
    ]
    column_searchable_list = [Evaluation.comment]
    column_filters = [
        Evaluation.score,
        Evaluation.user_id,
        Evaluation.evaluator_id,
        Evaluation.task_id
    ]
    column_default_sort = [(Evaluation.created_at, True)]
    form_excluded_columns = [Evaluation.created_at, Evaluation.updated_at]
    page_size = 50


class CommentAdmin(ModelView, model=TaskComment):
    name = "Комментарий"
    name_plural = "Комментарии"
    icon = "fa-solid fa-comment"
    column_list = [
        TaskComment.id,
        TaskComment.content,
        TaskComment.task_id,
        TaskComment.author_id,
        TaskComment.created_at
    ]
    column_searchable_list = [TaskComment.content]
    column_filters = [TaskComment.task_id, TaskComment.author_id]
    column_default_sort = [(TaskComment.created_at, True)]
    form_excluded_columns = [TaskComment.created_at, TaskComment.updated_at]
    page_size = 50


admin_views = [
    UserAdmin,
    TeamAdmin,
    TaskAdmin,
    MeetingAdmin,
    EvaluationAdmin,
    CommentAdmin,
]
