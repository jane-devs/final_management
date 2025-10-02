from fastapi import APIRouter
from schemas.user import UserRead, UserUpdate
from core.fastapi_users import fastapi_users

router = APIRouter(prefix="/users", tags=["users"])

router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
)
