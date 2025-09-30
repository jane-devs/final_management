import uuid
from fastapi_users import FastAPIUsers
from models.user import User
from core.users import get_user_manager
from core.auth import auth_backend

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

current_user = fastapi_users.current_user()
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
current_verified_user = fastapi_users.current_user(active=True, verified=True)

optional_current_user = fastapi_users.current_user(optional=True)
