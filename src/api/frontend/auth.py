"""
Эндпоинты аутентификации: login, logout, register.
"""

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext

from core.database import get_async_session
from models.user import User
from .dependencies import templates, current_user_factory
from services import UserService


router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root(
    current_user: User | None = Depends(current_user_factory())
):
    """Главная страница - редирект на dashboard или login."""
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=303)
    return RedirectResponse(url="/login", status_code=303)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница входа."""
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_async_session)
):
    """Обработка входа."""
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Неверный email или пароль"
        })

    request.session["user_id"] = str(user.id)
    return RedirectResponse("/dashboard", status_code=303)


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Страница регистрации."""
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
async def register(
    request: Request,
    email: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    session: AsyncSession = Depends(get_async_session)
):
    """Обработка регистрации с валидацией."""
    try:
        user = await UserService.register_user(
            session, email, password, password_confirm, first_name, last_name
        )
        request.session["user_id"] = str(user.id)
        return RedirectResponse(url="/dashboard", status_code=303)

    except Exception as e:
        error_msg = str(e.detail if hasattr(e, 'detail') else str(e))
        return templates.TemplateResponse("register.html", {
            "request": request,
            "messages": [{"type": "error", "text": error_msg}]
        })


@router.post("/logout")
async def logout(request: Request):
    """Выход из системы."""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)
