"""FastAPI Users authentication setup."""

from .config import (
    auth_backend,
    cookie_transport,
    current_active_user,
    fastapi_users,
    get_async_session,
    get_jwt_strategy,
    get_user_db,
    get_user_manager,
)
from .schemas import UserCreate, UserRead, UserUpdate

__all__ = [
    # Core configuration
    "auth_backend",
    "cookie_transport",
    "fastapi_users",
    "get_async_session",
    "get_jwt_strategy",
    "get_user_db",
    "get_user_manager",
    # Dependencies
    "current_active_user",
    # Schemas
    "UserCreate",
    "UserRead",
    "UserUpdate",
]

