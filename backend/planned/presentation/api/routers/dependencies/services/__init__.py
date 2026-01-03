"""
Service dependency injection functions.

Each function returns an instance of a service, which can be used
with FastAPI's Depends() in route handlers.
"""

import datetime
from typing import Annotated

from fastapi import Depends, Request
from planned.application.commands import (
    CreateOrGetDayHandler,
    RecordTaskActionHandler,
    SaveDayHandler,
    ScheduleDayHandler,
    SyncAllCalendarsHandler,
    SyncCalendarHandler,
    UnscheduleDayHandler,
    UpdateDayHandler,
)
from planned.application.commands.calendar import (
    CreateCalendarHandler,
    DeleteCalendarHandler,
    UpdateCalendarHandler,
)
from planned.application.commands.day_template import (
    CreateDayTemplateHandler,
    DeleteDayTemplateHandler,
    UpdateDayTemplateHandler,
)
from planned.application.commands.push_subscription import (
    CreatePushSubscriptionHandler,
    DeletePushSubscriptionHandler,
)
from planned.application.commands.task_definition import (
    BulkCreateTaskDefinitionsHandler,
    CreateTaskDefinitionHandler,
    DeleteTaskDefinitionHandler,
    UpdateTaskDefinitionHandler,
)
from planned.application.commands.user import UpdateUserHandler
from planned.application.queries import (
    GetDayContextHandler,
    GetUpcomingCalendarEntriesHandler,
    GetUpcomingTasksHandler,
    PreviewDayHandler,
    PreviewTasksHandler,
)
from planned.application.queries.calendar import (
    GetCalendarHandler,
    ListCalendarsHandler,
)
from planned.application.queries.calendar_entry import ListCalendarEntriesHandler
from planned.application.queries.day_template import (
    GetDayTemplateHandler,
    ListDayTemplatesHandler,
)
from planned.application.queries.push_subscription import ListPushSubscriptionsHandler
from planned.application.queries.routine import GetRoutineHandler, ListRoutinesHandler
from planned.application.queries.task import ListTasksHandler
from planned.application.queries.task_definition import (
    GetTaskDefinitionHandler,
    ListTaskDefinitionsHandler,
)
from planned.application.services import (
    CalendarService,
    DayService,
    PlanningService,
    SheppardService,
)
from planned.application.services.factories import DayServiceFactory
from planned.application.unit_of_work import UnitOfWorkFactory
from planned.core.exceptions import ServerError
from planned.core.utils.dates import get_current_date, get_tomorrows_date
from planned.domain.entities import UserEntity
from planned.infrastructure.gateways import GoogleCalendarGateway, WebPushGateway
from planned.infrastructure.unit_of_work import SqlAlchemyUnitOfWorkFactory

from ..user import get_current_user


def get_unit_of_work_factory() -> UnitOfWorkFactory:
    """Get a UnitOfWorkFactory instance."""
    return SqlAlchemyUnitOfWorkFactory()


# Query Handler Dependencies
def get_get_day_context_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> GetDayContextHandler:
    """Get a GetDayContextHandler instance."""
    return GetDayContextHandler(uow_factory)


def get_preview_day_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> PreviewDayHandler:
    """Get a PreviewDayHandler instance."""
    return PreviewDayHandler(uow_factory)


def get_preview_tasks_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> PreviewTasksHandler:
    """Get a PreviewTasksHandler instance."""
    return PreviewTasksHandler(uow_factory)


# Calendar handlers
def get_get_calendar_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> GetCalendarHandler:
    """Get a GetCalendarHandler instance."""
    return GetCalendarHandler(uow_factory)


def get_list_calendars_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> ListCalendarsHandler:
    """Get a ListCalendarsHandler instance."""
    return ListCalendarsHandler(uow_factory)


def get_create_calendar_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> CreateCalendarHandler:
    """Get a CreateCalendarHandler instance."""
    return CreateCalendarHandler(uow_factory)


def get_update_calendar_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> UpdateCalendarHandler:
    """Get an UpdateCalendarHandler instance."""
    return UpdateCalendarHandler(uow_factory)


def get_delete_calendar_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> DeleteCalendarHandler:
    """Get a DeleteCalendarHandler instance."""
    return DeleteCalendarHandler(uow_factory)


# TaskDefinition handlers
def get_get_task_definition_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> GetTaskDefinitionHandler:
    """Get a GetTaskDefinitionHandler instance."""
    return GetTaskDefinitionHandler(uow_factory)


def get_list_task_definitions_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> ListTaskDefinitionsHandler:
    """Get a ListTaskDefinitionsHandler instance."""
    return ListTaskDefinitionsHandler(uow_factory)


def get_create_task_definition_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> CreateTaskDefinitionHandler:
    """Get a CreateTaskDefinitionHandler instance."""
    return CreateTaskDefinitionHandler(uow_factory)


def get_update_task_definition_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> UpdateTaskDefinitionHandler:
    """Get an UpdateTaskDefinitionHandler instance."""
    return UpdateTaskDefinitionHandler(uow_factory)


def get_delete_task_definition_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> DeleteTaskDefinitionHandler:
    """Get a DeleteTaskDefinitionHandler instance."""
    return DeleteTaskDefinitionHandler(uow_factory)


def get_bulk_create_task_definitions_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> BulkCreateTaskDefinitionsHandler:
    """Get a BulkCreateTaskDefinitionsHandler instance."""
    return BulkCreateTaskDefinitionsHandler(uow_factory)


# DayTemplate handlers
def get_get_day_template_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> GetDayTemplateHandler:
    """Get a GetDayTemplateHandler instance."""
    return GetDayTemplateHandler(uow_factory)


def get_list_day_templates_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> ListDayTemplatesHandler:
    """Get a ListDayTemplatesHandler instance."""
    return ListDayTemplatesHandler(uow_factory)


def get_create_day_template_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> CreateDayTemplateHandler:
    """Get a CreateDayTemplateHandler instance."""
    return CreateDayTemplateHandler(uow_factory)


def get_update_day_template_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> UpdateDayTemplateHandler:
    """Get an UpdateDayTemplateHandler instance."""
    return UpdateDayTemplateHandler(uow_factory)


def get_delete_day_template_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> DeleteDayTemplateHandler:
    """Get a DeleteDayTemplateHandler instance."""
    return DeleteDayTemplateHandler(uow_factory)


# Routine handlers
def get_get_routine_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> GetRoutineHandler:
    """Get a GetRoutineHandler instance."""
    return GetRoutineHandler(uow_factory)


def get_list_routines_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> ListRoutinesHandler:
    """Get a ListRoutinesHandler instance."""
    return ListRoutinesHandler(uow_factory)


# PushSubscription handlers
def get_list_push_subscriptions_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> ListPushSubscriptionsHandler:
    """Get a ListPushSubscriptionsHandler instance."""
    return ListPushSubscriptionsHandler(uow_factory)


def get_create_push_subscription_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> CreatePushSubscriptionHandler:
    """Get a CreatePushSubscriptionHandler instance."""
    return CreatePushSubscriptionHandler(uow_factory)


def get_delete_push_subscription_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> DeletePushSubscriptionHandler:
    """Get a DeletePushSubscriptionHandler instance."""
    return DeletePushSubscriptionHandler(uow_factory)


# User handlers
def get_update_user_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> UpdateUserHandler:
    """Get an UpdateUserHandler instance."""
    return UpdateUserHandler(uow_factory)


# CalendarEntry handlers
def get_list_calendar_entries_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> ListCalendarEntriesHandler:
    """Get a ListCalendarEntriesHandler instance."""
    return ListCalendarEntriesHandler(uow_factory)


# Task handlers
def get_list_tasks_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> ListTasksHandler:
    """Get a ListTasksHandler instance."""
    return ListTasksHandler(uow_factory)


def get_get_upcoming_tasks_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> GetUpcomingTasksHandler:
    """Get a GetUpcomingTasksHandler instance."""
    return GetUpcomingTasksHandler(uow_factory)


def get_get_upcoming_calendar_entries_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> GetUpcomingCalendarEntriesHandler:
    """Get a GetUpcomingCalendarEntriesHandler instance."""
    return GetUpcomingCalendarEntriesHandler(uow_factory)


# Command Handler Dependencies
def get_schedule_day_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> ScheduleDayHandler:
    """Get a ScheduleDayHandler instance."""
    return ScheduleDayHandler(uow_factory)


def get_update_day_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> UpdateDayHandler:
    """Get an UpdateDayHandler instance."""
    return UpdateDayHandler(uow_factory)


def get_record_task_action_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> RecordTaskActionHandler:
    """Get a RecordTaskActionHandler instance."""
    return RecordTaskActionHandler(uow_factory)


def get_create_or_get_day_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> CreateOrGetDayHandler:
    """Get a CreateOrGetDayHandler instance."""
    return CreateOrGetDayHandler(uow_factory)


def get_unschedule_day_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> UnscheduleDayHandler:
    """Get an UnscheduleDayHandler instance."""
    return UnscheduleDayHandler(uow_factory)


def get_save_day_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> SaveDayHandler:
    """Get a SaveDayHandler instance."""
    return SaveDayHandler(uow_factory)


def get_google_gateway() -> GoogleCalendarGateway:
    """Get a GoogleCalendarGateway instance."""
    return GoogleCalendarGateway()


def get_web_push_gateway() -> WebPushGateway:
    """Get a WebPushGateway instance."""
    return WebPushGateway()


def get_sync_calendar_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    google_gateway: Annotated[GoogleCalendarGateway, Depends(get_google_gateway)],
) -> SyncCalendarHandler:
    """Get a SyncCalendarHandler instance."""
    return SyncCalendarHandler(uow_factory, google_gateway)


def get_sync_all_calendars_handler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    google_gateway: Annotated[GoogleCalendarGateway, Depends(get_google_gateway)],
) -> SyncAllCalendarsHandler:
    """Get a SyncAllCalendarsHandler instance."""
    return SyncAllCalendarsHandler(uow_factory, google_gateway)


def get_calendar_service(
    user: Annotated[UserEntity, Depends(get_current_user)],
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    google_gateway: Annotated[GoogleCalendarGateway, Depends(get_google_gateway)],
) -> CalendarService:
    """Get an instance of CalendarService."""
    return CalendarService(
        user=user,
        uow_factory=uow_factory,
        google_gateway=google_gateway,
    )


def get_planning_service(
    user: Annotated[UserEntity, Depends(get_current_user)],
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> PlanningService:
    """Get a user-scoped instance of PlanningService."""
    return PlanningService(
        user=user,
        uow_factory=uow_factory,
    )


async def get_day_service_for_current_date(
    user: Annotated[UserEntity, Depends(get_current_user)],
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
) -> DayService:
    """Get a user-scoped instance of DayService for today's date."""
    return await get_day_service_for_date(
        get_current_date(),
        user=user,
        uow_factory=uow_factory,
    )


async def get_day_service_for_tomorrow_date(
    user: Annotated[UserEntity, Depends(get_current_user)],
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
    user: Annotated[UserEntity, Depends(get_current_user)],
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
    user: Annotated[UserEntity, Depends(get_current_user)],
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_unit_of_work_factory)],
    google_gateway: Annotated[GoogleCalendarGateway, Depends(get_google_gateway)],
    web_push_gateway: Annotated[WebPushGateway, Depends(get_web_push_gateway)],
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
