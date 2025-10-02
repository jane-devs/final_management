"""Exception handlers для FastAPI"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from .exceptions import (
    TeamException, AppException, ValidationError,
    NotFoundError, ForbiddenError, UnauthorizedError
)


async def team_exception_handler(request: Request, exc: TeamException) -> JSONResponse:
    """Обработчик исключений команд"""
    status_code = status.HTTP_400_BAD_REQUEST

    from .exceptions import (
        TeamNotFound, TeamAccessDenied, TeamOwnershipRequired,
        InvalidInviteCode, AlreadyInTeam, NotInTeam, OwnerCannotLeaveTeam
    )

    if isinstance(exc, TeamNotFound):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, (TeamAccessDenied, TeamOwnershipRequired)):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, (InvalidInviteCode, AlreadyInTeam, NotInTeam, OwnerCannotLeaveTeam)):
        status_code = status.HTTP_400_BAD_REQUEST

    return JSONResponse(
        status_code=status_code,
        content={
            "error": "team_error",
            "message": exc.message,
            "detail": exc.detail
        }
    )


def create_simple_exception_handler(error_type: str):
    """Создает обработчик для простых исключений AppException"""
    async def handler(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": error_type,
                "message": exc.message
            }
        )
    return handler


app_exception_handler = create_simple_exception_handler("app_error")


async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Обработчик ошибок валидации"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "validation_error",
            "message": exc.message,
            "field": exc.field
        }
    )


async def not_found_error_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """Обработчик ошибок 404"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "not_found",
            "message": exc.message
        }
    )


async def forbidden_error_handler(request: Request, exc: ForbiddenError) -> JSONResponse:
    """Обработчик ошибок 403"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "forbidden",
            "message": exc.message
        }
    )


async def unauthorized_error_handler(request: Request, exc: UnauthorizedError) -> JSONResponse:
    """Обработчик ошибок 401"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "unauthorized",
            "message": exc.message
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Обработчик стандартных HTTP исключений"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": exc.detail
        }
    )


async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Обработчик ошибок валидации запросов Pydantic"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validation_error",
            "message": "Ошибка валидации данных",
            "details": errors
        }
    )


auth_exception_handler = create_simple_exception_handler("auth_error")
task_exception_handler = create_simple_exception_handler("task_error")
meeting_exception_handler = create_simple_exception_handler("meeting_error")
comment_exception_handler = create_simple_exception_handler("comment_error")
evaluation_exception_handler = create_simple_exception_handler("evaluation_error")


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обработчик всех остальных исключений"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_error",
            "message": "Внутренняя ошибка сервера"
        }
    )