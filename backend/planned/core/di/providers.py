"""Provider functions for creating and registering dependencies in the DI container."""

from typing import cast

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
)
from planned.application.services import CalendarService, PlanningService, SheppardService
from planned.core.config import settings
from planned.core.di.container import DIContainer
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
from planned.infrastructure.utils.dates import get_current_date


def register_repositories(container: DIContainer) -> None:
    """Register all repository implementations in the DI container.
    
    Args:
        container: The DI container to register repositories in
    """
    # Register repositories as singletons
    container.register_singleton(AuthTokenRepositoryProtocol, AuthTokenRepository())  # type: ignore[type-abstract]
    container.register_singleton(CalendarRepositoryProtocol, CalendarRepository())  # type: ignore[type-abstract]
    container.register_singleton(DayRepositoryProtocol, DayRepository())  # type: ignore[type-abstract]
    container.register_singleton(
        DayTemplateRepositoryProtocol, DayTemplateRepository()  # type: ignore[type-abstract]
    )
    container.register_singleton(EventRepositoryProtocol, EventRepository())  # type: ignore[type-abstract]
    container.register_singleton(MessageRepositoryProtocol, MessageRepository())  # type: ignore[type-abstract]
    container.register_singleton(
        PushSubscriptionRepositoryProtocol, PushSubscriptionRepository()  # type: ignore[type-abstract]
    )
    container.register_singleton(RoutineRepositoryProtocol, RoutineRepository())  # type: ignore[type-abstract]
    container.register_singleton(
        TaskDefinitionRepositoryProtocol, TaskDefinitionRepository()  # type: ignore[type-abstract]
    )
    container.register_singleton(TaskRepositoryProtocol, TaskRepository())  # type: ignore[type-abstract]


def register_services(container: DIContainer) -> None:
    """Register all service implementations in the DI container.
    
    Args:
        container: The DI container to register services in
    """
    # Get repositories from container
    auth_token_repo = cast(AuthTokenRepositoryProtocol, container.get(AuthTokenRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]
    calendar_repo = cast(CalendarRepositoryProtocol, container.get(CalendarRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]
    day_repo = cast(DayRepositoryProtocol, container.get(DayRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]
    day_template_repo = cast(DayTemplateRepositoryProtocol, container.get(DayTemplateRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]
    event_repo = cast(EventRepositoryProtocol, container.get(EventRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]
    message_repo = cast(MessageRepositoryProtocol, container.get(MessageRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]
    push_subscription_repo = cast(PushSubscriptionRepositoryProtocol, container.get(PushSubscriptionRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]
    routine_repo = cast(RoutineRepositoryProtocol, container.get(RoutineRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]
    task_definition_repo = cast(TaskDefinitionRepositoryProtocol, container.get(TaskDefinitionRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]
    task_repo = cast(TaskRepositoryProtocol, container.get(TaskRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]

    # Create and register services
    calendar_service = CalendarService(
        auth_token_repo=auth_token_repo,
        calendar_repo=calendar_repo,
        event_repo=event_repo,
    )
    container.register_singleton(CalendarService, calendar_service)

    planning_service = PlanningService(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        routine_repo=routine_repo,
        task_definition_repo=task_definition_repo,
        task_repo=task_repo,
    )
    container.register_singleton(PlanningService, planning_service)


async def create_sheppard_service(container: DIContainer) -> SheppardService:
    """Create and return a SheppardService instance with all dependencies.
    
    Args:
        container: The DI container to resolve dependencies from
        
    Returns:
        A configured SheppardService instance
    """
    from planned.application.services import DayService

    # Get repositories and services from container
    day_repo = cast(DayRepositoryProtocol, container.get(DayRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]
    day_template_repo = cast(DayTemplateRepositoryProtocol, container.get(DayTemplateRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]
    event_repo = cast(EventRepositoryProtocol, container.get(EventRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]
    message_repo = cast(MessageRepositoryProtocol, container.get(MessageRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]
    push_subscription_repo = cast(PushSubscriptionRepositoryProtocol, container.get(PushSubscriptionRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]
    task_repo = cast(TaskRepositoryProtocol, container.get(TaskRepositoryProtocol))  # type: ignore[type-abstract,redundant-cast]
    calendar_service = container.get(CalendarService)
    planning_service = container.get(PlanningService)

    # Create day service for current date
    day_svc = await DayService.for_date(
        get_current_date(),
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        task_repo=task_repo,
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
        push_subscriptions=push_subscriptions,
        mode="starting",
    )


def create_container() -> DIContainer:
    """Create and configure a DI container with all dependencies.
    
    Returns:
        A configured DI container
    """
    container = DIContainer()
    register_repositories(container)
    register_services(container)
    return container

