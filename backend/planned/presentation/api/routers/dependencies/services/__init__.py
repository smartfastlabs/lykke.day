"""
Service dependency injection functions.

Each function returns an instance of a service, which can be used
with FastAPI's Depends() in route handlers.
"""

import datetime
from typing import Annotated

from fastapi import Depends, Request

from planned.application.services import (
    CalendarService,
    DayService,
    PlanningService,
    SheppardManager,
    SheppardService,
)
from planned.application.services.factories import DayServiceFactory
from planned.application.unit_of_work import UnitOfWorkFactory
from planned.core.exceptions import exceptions
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
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
) -> SheppardService:
    """Get the SheppardService instance for the logged-in user.

    Args:
        request: FastAPI request object (to access app state)
        user: Current user (from dependency)

    Returns:
        SheppardService instance for the user

    Raises:
        RuntimeError: If SheppardManager is not available or service doesn't exist
    """
    # Get SheppardManager from app state
    manager: SheppardManager | None = getattr(
        request.app.state, "sheppard_manager", None
    )
    if manager is None:
        raise exceptions.ServerError(
            "SheppardManager is not available. The service may not be initialized."
        )

    user_id = user.id
    try:
        service = await manager.ensure_service_for_user(user_id)
    except RuntimeError as e:
        raise exceptions.ServerError(
            f"SheppardService is not available for user {user_id}: {e}"
        ) from e

    return service
