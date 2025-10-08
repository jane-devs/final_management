from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.middleware.sessions import SessionMiddleware
from sqladmin import Admin

from core.config import settings
from core.database import engine
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
from api import (
    auth, users, teams, tasks, meetings,
    comments, evaluations, calendar
)
from api.frontend import router as frontend_router
from utils.init_superuser import create_superuser
from admin.auth import authentication_backend
from admin.views import admin_views


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_superuser()
    yield

app = FastAPI(
    title="Система управления командой",
    description="MVP для управления командами, задачами и встречами",
    version="0.1.0",
    lifespan=lifespan
)


app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="session",
    path="/",
    same_site="lax",
    https_only=False
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


admin = Admin(
    app=app,
    engine=engine,
    authentication_backend=authentication_backend,
    title="Админ-панель - Управление командой",
    base_url="/admin"
)

for view in admin_views:
    admin.add_view(view)

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


app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(frontend_router)

API_ROUTERS = [
    auth.router,
    users.router,
    teams.router,
    tasks.router,
    meetings.router,
    comments.router,
    evaluations.router,
    calendar.router,
]

for router in API_ROUTERS:
    app.include_router(router, prefix="/api")


@app.get("/health")
async def health_check():
    """Проверка состояния приложения"""
    return {
        "status": "ok",
        "environment": settings.environment
    }
