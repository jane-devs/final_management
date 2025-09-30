from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTAuthentication,
)
from config import settings

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

jwt_authentication = JWTAuthentication(
    secret=settings.secret_key,
    lifetime_seconds=settings.access_token_expire_minutes * 60,
)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=lambda: jwt_authentication,
)
