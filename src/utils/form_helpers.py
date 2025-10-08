from typing import Any, Callable
from functools import wraps
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="frontend_templates")


def render_error(
    request: Request,
    template: str,
    user: Any,
    error_msg: str,
    status_code: int = 400,
    **extra_context
) -> Any:
    """
    Универсальная функция для отображения ошибок в шаблоне.

    Args:
        request: FastAPI Request
        template: Путь к шаблону
        user: Текущий пользователь
        error_msg: Сообщение об ошибке
        status_code: HTTP статус код
        **extra_context: Дополнительные данные для шаблона

    Returns:
        TemplateResponse с ошибкой
    """
    context = {
        "request": request,
        "user": user,
        "error": error_msg,
        **extra_context
    }
    return templates.TemplateResponse(template, context, status_code=status_code)


def render_success(
    request: Request,
    template: str,
    user: Any,
    success_msg: str,
    **extra_context
) -> Any:
    """
    Универсальная функция для отображения успешных сообщений в шаблоне.

    Args:
        request: FastAPI Request
        template: Путь к шаблону
        user: Текущий пользователь
        success_msg: Сообщение об успехе
        **extra_context: Дополнительные данные для шаблона

    Returns:
        TemplateResponse с сообщением об успехе
    """
    context = {
        "request": request,
        "user": user,
        "messages": [{"type": "success", "text": success_msg}],
        **extra_context
    }
    return templates.TemplateResponse(template, context)


def render_template(
    request: Request,
    template: str,
    **context
) -> Any:
    """
    Универсальная функция для рендеринга шаблона.

    Args:
        request: FastAPI Request
        template: Путь к шаблону
        **context: Данные для шаблона

    Returns:
        TemplateResponse
    """
    context["request"] = request
    return templates.TemplateResponse(template, context)


def handle_form_errors(
    template: str,
    redirect_on_success: str = None,
    get_extra_context: Callable = None
):
    """
    Декоратор для унифицированной обработки ошибок в формах.

    Args:
        template: Шаблон для отображения ошибок
        redirect_on_success: URL для редиректа при успехе
        get_extra_context: Функция для получения дополнительного контекста при ошибке
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request") or args[0]
            current_user = kwargs.get("current_user")

            try:
                result = await func(*args, **kwargs)

                if redirect_on_success:
                    return RedirectResponse(url=redirect_on_success, status_code=303)

                return result

            except HTTPException as e:
                extra_context = {}
                if get_extra_context:
                    extra_context = await get_extra_context(*args, **kwargs)

                return render_error(
                    request,
                    template,
                    current_user,
                    e.detail,
                    status_code=e.status_code,
                    **extra_context
                )

            except Exception as e:
                extra_context = {}
                if get_extra_context:
                    extra_context = await get_extra_context(*args, **kwargs)

                error_msg = str(e.detail if hasattr(e, 'detail') else str(e))
                return render_error(
                    request,
                    template,
                    current_user,
                    error_msg,
                    **extra_context
                )

        return wrapper
    return decorator


class FormResponse:
    """
    Класс для унифицированного формирования ответов от форм.
    """

    @staticmethod
    def error(
        request: Request,
        template: str,
        user: Any,
        error: str,
        status_code: int = 400,
        **context
    ):
        """Ответ с ошибкой."""
        return render_error(
            request, template, user, error, status_code, **context)

    @staticmethod
    def success_redirect(url: str):
        """Редирект при успехе."""
        return RedirectResponse(url=url, status_code=303)

    @staticmethod
    def render(request: Request, template: str, **context):
        """Простой рендеринг шаблона."""
        return render_template(request, template, **context)


def extract_error_message(exception: Exception) -> str:
    """
    Извлекает человекочитаемое сообщение об ошибке из исключения.
    """
    if isinstance(exception, HTTPException):
        return exception.detail
    elif hasattr(exception, 'detail'):
        return str(exception.detail)
    else:
        return str(exception)
