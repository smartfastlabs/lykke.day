"""
Service dependency injection functions.

Each function returns an instance of a service, which can be used
with FastAPI's Depends() in route handlers.
"""

import datetime
from typing import Annotated

from fastapi import Depends, Request
from planned.application.mediator import Mediator
from planned.application.services import (
    CalendarService,
    DayService,
    PlanningService,
    SheppardService,
)
from planned.application.services.factories import DayServiceFactory
from planned.application.unit_of_work import UnitOfWorkFactory
from planned.core.exceptions import ServerError
from planned.domain.entities import User
from planned.infrastructure.gateways.adapters import (
    GoogleCalendarGatewayAdapter,
    WebPushGatewayAdapter,
)
from planned.infrastructure.unit_of_work import SqlAlchemyUnitOfWorkFactory
from planned.infrastructure.utils.dates import get_current_date, get_tomorrows_date

from ..user import get_current_user


def get_unit_of_work_factory() -> UnitOfWorkFactory:
    """Get a UnitOfWorkFactory instance."""
    return SqlAlchemyUnitOfWorkFactory()


def get_mediator(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> Mediator:
    """Get a Mediator instance for dispatching commands and queries."""
    return Mediator(uow_factory)


def get_google_gateway() -> GoogleCalendarGatewayAdapter:
    """Get a GoogleCalendarGatewayAdapter instance."""
    return GoogleCalendarGatewayAdapter()


def get_web_push_gateway() -> WebPushGatewayAdapter:
    """Get a WebPushGatewayAdapter instance."""
    return WebPushGatewayAdapter()


def get_calendar_service(
    user: Annotated[User, Depends(get_current_user)],
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    google_gateway: Annotated[
        GoogleCalendarGatewayAdapter, Depends(get_google_gateway)
    ],
) -> CalendarService:
    """Get an instance of CalendarService."""
    return CalendarService(
        user=user,
        uow_factory=uow_factory,
        google_gateway=google_gateway,
    )


def get_planning_service(
    user: Annotated[User, Depends(get_current_user)],
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> PlanningService:
    """Get a user-scoped instance of PlanningService."""
    return PlanningService(
        user=user,
        uow_factory=uow_factory,
    )


async def get_day_service_for_current_date(
    user: Annotated[User, Depends(get_current_user)],
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> DayService:
    """Get a user-scoped instance of DayService for today's date."""
    return await get_day_service_for_date(
        get_current_date(),
        user=user,
        uow_factory=uow_factory,
    )


async def get_day_service_for_tomorrow_date(
    user: Annotated[User, Depends(get_current_user)],
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> DayService:
    """Get a user-scoped instance of DayService for tomorrow's date."""
    return await get_day_service_for_date(
        get_tomorrows_date(),
        user=user,
        uow_factory=uow_factory,
    )


async def get_day_service_for_date(
    date: datetime.date,
    user: Annotated[User, Depends(get_current_user)],
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> DayService:
    """Get a user-scoped instance of DayService for a specific date."""
    # Use the factory to create DayService
    factory = DayServiceFactory(
        user=user,
        uow_factory=uow_factory,
    )
    return await factory.create(date, user_id=user.id)


async def get_sheppard_service(
    user: Annotated[User, Depends(get_current_user)],
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    google_gateway: Annotated[
        GoogleCalendarGatewayAdapter, Depends(get_google_gateway)
    ],
    web_push_gateway: Annotated[WebPushGatewayAdapter, Depends(get_web_push_gateway)],
    day_service: Annotated[DayService, Depends(get_day_service_for_current_date)],
) -> SheppardService:
    """Get a stateless SheppardService instance for the logged-in user.

    Args:
        user: Current user (from dependency)
        uow_factory: Factory for creating UnitOfWork instances
        google_gateway: Gateway for Google Calendar integration
        web_push_gateway: Gateway for web push notifications
        day_service: DayService instance for the current date

    Returns:
        SheppardService instance for the user
    """
    # Load push subscriptions
    uow = uow_factory.create(user.id)
    async with uow:
        push_subscriptions = await uow.push_subscriptions.all()

    # Create services
    calendar_service = CalendarService(
        user=user,
        uow_factory=uow_factory,
        google_gateway=google_gateway,
    )

    planning_service = PlanningService(
        user=user,
        uow_factory=uow_factory,
    )

    # Create and return stateless SheppardService
    return SheppardService(
        user=user,
        day_svc=day_service,
        uow_factory=uow_factory,
        calendar_service=calendar_service,
        planning_service=planning_service,
        web_push_gateway=web_push_gateway,
        push_subscriptions=push_subscriptions,
    )
