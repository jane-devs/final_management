from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from core.config import settings
from core.exceptions import (
    TeamException, AppException, ValidationError,
    NotFoundError, ForbiddenError, UnauthorizedError,
    AuthException, TaskException, MeetingException,
    CommentException, EvaluationException
)
from core.exception_handlers import (
    team_exception_handler, app_exception_handler, validation_error_handler,
    not_found_error_handler, forbidden_error_handler,
    unauthorized_error_handler, auth_exception_handler,
    task_exception_handler, meeting_exception_handler,
    comment_exception_handler, evaluation_exception_handler,
    http_exception_handler, request_validation_exception_handler,
    general_exception_handler
)
from api import auth, users, teams, tasks, meetings, comments, evaluations

app = FastAPI(
    title="Система управления командой",
    description="MVP для управления командами, задачами и встречами",
    version="0.1.0",
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

EXCEPTION_HANDLERS = [
    (TeamException, team_exception_handler),
    (AuthException, auth_exception_handler),
    (TaskException, task_exception_handler),
    (MeetingException, meeting_exception_handler),
    (CommentException, comment_exception_handler),
    (EvaluationException, evaluation_exception_handler),
    (AppException, app_exception_handler),
    (ValidationError, validation_error_handler),
    (NotFoundError, not_found_error_handler),
    (ForbiddenError, forbidden_error_handler),
    (UnauthorizedError, unauthorized_error_handler),
    (HTTPException, http_exception_handler),
    (RequestValidationError, request_validation_exception_handler),
    (Exception, general_exception_handler),
]

for exception_class, handler in EXCEPTION_HANDLERS:
    app.add_exception_handler(exception_class, handler)


ROUTERS = [
    auth.router,
    users.router,
    teams.router,
    tasks.router,
    meetings.router,
    comments.router,
    evaluations.router,
]

for router in ROUTERS:
    app.include_router(router)


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "Team Management System API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Проверка состояния приложения"""
    return {
        "status": "ok",
        "environment": settings.environment
    }
