import asyncio
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Never

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from starlette.middleware.sessions import SessionMiddleware

from planned import routers, settings
from planned.middlewares.auth import AuthMiddleware
from planned.services import SheppardService
from planned.utils import youtube
from planned.utils.dates import get_current_datetime

logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time}</green> <level>{message}</level>",
)


@asynccontextmanager
async def init_lifespan(app: FastAPI) -> AsyncIterator[Never]:
    """
    Lifespan context manager for FastAPI application.
    """
    from planned.repositories import (
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
    from planned.services import CalendarService, DayService, PlanningService
    from planned.utils.dates import get_current_date

    # Create repository instances
    day_repo = DayRepository()
    day_template_repo = DayTemplateRepository()
    event_repo = EventRepository()
    message_repo = MessageRepository()
    push_subscription_repo = PushSubscriptionRepository()
    task_repo = TaskRepository()
    auth_token_repo = AuthTokenRepository()
    calendar_repo = CalendarRepository()
    routine_repo = RoutineRepository()
    task_definition_repo = TaskDefinitionRepository()

    # Create service instances
    calendar_service = CalendarService(
        auth_token_repo=auth_token_repo,
        calendar_repo=calendar_repo,
        event_repo=event_repo,
    )

    planning_service = PlanningService(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        routine_repo=routine_repo,
        task_definition_repo=task_definition_repo,
        task_repo=task_repo,
    )

    day_svc = await DayService.for_date(
        get_current_date(),
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        task_repo=task_repo,
    )

    push_subscriptions = await push_subscription_repo.all()

    sheppard_svc = SheppardService(
        day_svc=day_svc,
        push_subscription_repo=push_subscription_repo,
        task_repo=task_repo,
        calendar_service=calendar_service,
        planning_service=planning_service,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        push_subscriptions=push_subscriptions,
    )

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
    routers.router,
    prefix=settings.API_PREFIX,
)


@app.get("/health")
def health_check() -> dict[str, str]:
    """
    Health check endpoint.
    """

    return {"status": "healthy"}
