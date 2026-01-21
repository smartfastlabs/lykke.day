"""FastAPI Users configuration."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import AuthenticationBackend, CookieTransport
from fastapi_users.authentication.strategy import JWTStrategy
from fastapi_users.exceptions import UserAlreadyExists
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from lykke.core.config import settings
from lykke.domain import value_objects
from lykke.domain.entities.day_template import DayTemplateEntity
from lykke.infrastructure.auth.schemas import UserCreate
from lykke.infrastructure.database.tables import User
from lykke.infrastructure.database.utils import get_engine
from lykke.infrastructure.repositories import DayTemplateRepository

# JWT secret - using the same secret as session was using
SECRET = settings.SESSION_SECRET

# Cookie transport configuration
cookie_domain = "lykke.day" if settings.ENVIRONMENT == "production" else None

cookie_transport = CookieTransport(
    cookie_name="lykke_auth",
    cookie_max_age=3600 * 24 * 30,  # 30 days
    cookie_httponly=True,
    cookie_secure=settings.ENVIRONMENT == "production",
    cookie_samesite="lax",
    cookie_domain=cookie_domain,
)


def get_jwt_strategy() -> JWTStrategy[User, UUID]:
    """Get JWT strategy for authentication."""
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600 * 24 * 30)  # 30 days


# Authentication backend
auth_backend = AuthenticationBackend(
    name="cookie",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    engine = get_engine()
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session_maker() as session:
        yield session


async def get_user_db(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> AsyncGenerator[SQLAlchemyUserDatabase[User, UUID], None]:
    """Get SQLAlchemy user database."""
    yield SQLAlchemyUserDatabase(session, User)


class UserManager(UUIDIDMixin, BaseUserManager[User, UUID]):
    """User manager for handling user operations."""

    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def create(  # type: ignore[override]
        self,
        user_create: UserCreate,
        safe: bool = False,
        request: Request | None = None,
    ) -> User:
        """Create a new user with custom fields."""
        # Check if user already exists
        existing_user = await self.user_db.get_by_email(user_create.email)
        if existing_user is not None:
            raise UserAlreadyExists()

        # Set custom fields before creation
        user_dict = (
            user_create.create_update_dict()
            if safe
            else user_create.create_update_dict_superuser()
        )

        # Hash password
        password = user_dict.pop("password")
        user_dict["hashed_password"] = self.password_helper.hash(password)

        # Set custom fields
        user_dict["created_at"] = datetime.now(UTC)
        from lykke.core.utils.serialization import dataclass_to_json_dict

        user_dict["settings"] = dataclass_to_json_dict(value_objects.UserSetting())

        # Create user
        user = await self.user_db.create(user_dict)

        await self.on_after_register(user, request)

        return user

    async def on_after_register(
        self,
        user: User,
        request: Request | None = None,
    ) -> None:
        """Called after a user registers."""
        # Create default day templates for new user
        day_template_repo = DayTemplateRepository(user_id=user.id)

        default_templates = [
            DayTemplateEntity(user_id=user.id, slug="default", icon=None),
            DayTemplateEntity(user_id=user.id, slug="workday", icon=None),
            DayTemplateEntity(user_id=user.id, slug="weekday", icon=None),
            DayTemplateEntity(user_id=user.id, slug="weekend", icon=None),
        ]

        # Insert all templates using insert_many for efficiency
        await day_template_repo.insert_many(*default_templates)

    async def on_after_forgot_password(
        self,
        user: User,
        token: str,
        request: Request | None = None,
    ) -> None:
        """Emit a domain event when a password reset is requested."""
        # Local import to avoid circular dependencies at import time
        from lykke.application.events import send_domain_events
        from lykke.domain.events.user_events import UserForgotPasswordEvent

        request_origin = request.headers.get("origin") if request else None
        user_agent = request.headers.get("user-agent") if request else None

        await send_domain_events(
            [
                UserForgotPasswordEvent(
                    user_id=user.id,
                    email=user.email,
                    reset_token=token,
                    request_origin=request_origin,
                    user_agent=user_agent,
                )
            ]
        )


async def get_user_manager(
    user_db: Annotated[SQLAlchemyUserDatabase[User, UUID], Depends(get_user_db)],
) -> AsyncGenerator[UserManager, None]:
    """Get user manager dependency."""
    yield UserManager(user_db)


# FastAPIUsers instance
fastapi_users = FastAPIUsers[User, UUID](
    get_user_manager,
    [auth_backend],
)

# Current user dependencies
current_active_user = fastapi_users.current_user(active=True)
