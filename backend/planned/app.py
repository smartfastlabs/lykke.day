import asyncio
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Never, cast

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.sessions import SessionMiddleware

from planned.application.repositories import (
    AuthTokenRepositoryProtocol,
    CalendarRepositoryProtocol,
    DayRepositoryProtocol,
    DayTemplateRepositoryProtocol,
    EventRepositoryProtocol,
    MessageRepositoryProtocol,
    PushSubscriptionRepositoryProtocol,
    RoutineRepositoryProtocol,
    TaskDefinitionRepositoryProtocol,
    TaskRepositoryProtocol,
    UserRepositoryProtocol,
)
from planned.application.services import (
    CalendarService,
    DayService,
    PlanningService,
    SheppardService,
)
from planned.core.config import settings
from planned.core.exceptions import BaseError, exceptions
from planned.infrastructure.gateways.adapters import (
    GoogleCalendarGatewayAdapter,
    WebPushGatewayAdapter,
)
from planned.infrastructure.repositories import (
    AuthTokenRepository,
    CalendarRepository,
    DayRepository,
    DayTemplateRepository,
    EventRepository,
    MessageRepository,
    PushSubscriptionRepository,
    RoutineRepository,
    TaskDefinitionRepository,
    TaskRepository,
)
from planned.infrastructure.utils import youtube
from planned.infrastructure.utils.dates import get_current_date
from planned.presentation.api.routers import router
from planned.presentation.middlewares.auth import AuthMiddleware

logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time}</green> <level>{message}</level>",
)


async def create_sheppard_service() -> SheppardService:
    """Create and return a SheppardService instance with all dependencies.

    Note: SheppardService is a background service that currently works with a single system user.
    In the future, this should be refactored to iterate over all users or work per-user.
    """
    from uuid import UUID, uuid4

    from planned.domain.entities import User
    from planned.domain.value_objects.user import UserSetting
    from planned.infrastructure.repositories import UserRepository

    # Create or get system user for background services
    user_repo = UserRepository()
    system_user_email = "system@planned.day"
    system_user = await user_repo.get_by_email(system_user_email)
    if system_user is None:
        # Create system user
        system_user = User(
            id=str(uuid4()),
            email=system_user_email,
            password_hash="",  # System user doesn't need password
            settings=UserSetting(),
        )
        system_user = await user_repo.put(system_user)

    system_user_uuid = UUID(system_user.id)

    # Create repositories scoped to system user
    auth_token_repo: AuthTokenRepositoryProtocol = cast(
        "AuthTokenRepositoryProtocol", AuthTokenRepository(user_uuid=system_user_uuid)
    )
    calendar_repo: CalendarRepositoryProtocol = cast(
        "CalendarRepositoryProtocol", CalendarRepository(user_uuid=system_user_uuid)
    )
    day_repo: DayRepositoryProtocol = cast(
        "DayRepositoryProtocol", DayRepository(user_uuid=system_user_uuid)
    )
    day_template_repo: DayTemplateRepositoryProtocol = cast(
        "DayTemplateRepositoryProtocol",
        DayTemplateRepository(user_uuid=system_user_uuid),
    )
    event_repo: EventRepositoryProtocol = cast(
        "EventRepositoryProtocol", EventRepository(user_uuid=system_user_uuid)
    )
    message_repo: MessageRepositoryProtocol = cast(
        "MessageRepositoryProtocol", MessageRepository(user_uuid=system_user_uuid)
    )
    push_subscription_repo: PushSubscriptionRepositoryProtocol = cast(
        "PushSubscriptionRepositoryProtocol",
        PushSubscriptionRepository(user_uuid=system_user_uuid),
    )
    task_repo: TaskRepositoryProtocol = cast(
        "TaskRepositoryProtocol", TaskRepository(user_uuid=system_user_uuid)
    )

    # Create gateway adapters
    google_gateway = GoogleCalendarGatewayAdapter()
    web_push_gateway = WebPushGatewayAdapter()

    # Create services
    calendar_service = CalendarService(
        auth_token_repo=auth_token_repo,
        calendar_repo=calendar_repo,
        event_repo=event_repo,
        google_gateway=google_gateway,
    )

    planning_service = PlanningService(
        user_uuid=system_user_uuid,
        user_repo=cast("UserRepositoryProtocol", user_repo),
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        routine_repo=cast(
            "RoutineRepositoryProtocol", RoutineRepository(user_uuid=system_user_uuid)
        ),
        task_definition_repo=cast(
            "TaskDefinitionRepositoryProtocol",
            TaskDefinitionRepository(user_uuid=system_user_uuid),
        ),
        task_repo=task_repo,
    )

    # Create day service for current date
    day_svc = await DayService.for_date(
        get_current_date(),
        user_uuid=system_user_uuid,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        task_repo=task_repo,
        user_repo=cast("UserRepositoryProtocol", user_repo),
    )

    # Load push subscriptions
    push_subscriptions = await push_subscription_repo.all()

    # Create and return SheppardService
    return SheppardService(
        day_svc=day_svc,
        push_subscription_repo=push_subscription_repo,
        task_repo=task_repo,
        calendar_service=calendar_service,
        planning_service=planning_service,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        web_push_gateway=web_push_gateway,
        push_subscriptions=push_subscriptions,
        mode="starting",
    )


@asynccontextmanager
async def init_lifespan(app: FastAPI) -> AsyncIterator[Never]:
    """
    Lifespan context manager for FastAPI application.
    """
    # Create SheppardService
    sheppard_svc = await create_sheppard_service()

    task = asyncio.create_task(sheppard_svc.run())
    yield  # type: ignore
    sheppard_svc.stop()
    task.cancel()
    youtube.kill_current_player()


app = FastAPI(
    title="Planned.day",
    description="API for managing calendar events",
    debug=settings.DEBUG,
    lifespan=init_lifespan,
)


app.add_middleware(
    AuthMiddleware,  # type: ignore
)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET,
)

# Set all CORS enabled origins
if settings.ENVIRONMENT == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    origins = [
        "planned.day",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

app.include_router(
    router,
    prefix=settings.API_PREFIX,
)


@app.exception_handler(BaseError)
async def custom_exception_handler(request: Request, exc: BaseError) -> JSONResponse:
    """Handle custom application exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    """
    Health check endpoint.
    """

    return {"status": "healthy"}
