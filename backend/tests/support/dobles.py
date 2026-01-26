"""Dobles-based test doubles for repositories, gateways, and UoW.

This module provides helper functions to create dobles InstanceDouble instances
for all repository protocols, gateway protocols, and UnitOfWork/ReadOnlyRepositories.
"""

from datetime import date
from typing import Any, Protocol
from uuid import UUID

from dobles import InstanceDouble, allow

from lykke.application.gateways import (
    GoogleCalendarGatewayProtocol,
    PubSubGatewayProtocol,
    WebPushGatewayProtocol,
)
from lykke.application.repositories import (
    AuditLogRepositoryReadOnlyProtocol,
    AuthTokenRepositoryReadOnlyProtocol,
    BotPersonalityRepositoryReadOnlyProtocol,
    BrainDumpRepositoryReadOnlyProtocol,
    CalendarEntryRepositoryReadOnlyProtocol,
    CalendarEntrySeriesRepositoryReadOnlyProtocol,
    CalendarRepositoryReadOnlyProtocol,
    ConversationRepositoryReadOnlyProtocol,
    DayRepositoryReadOnlyProtocol,
    DayTemplateRepositoryReadOnlyProtocol,
    FactoidRepositoryReadOnlyProtocol,
    MessageRepositoryReadOnlyProtocol,
    PushNotificationRepositoryReadOnlyProtocol,
    PushSubscriptionRepositoryReadOnlyProtocol,
    RoutineDefinitionRepositoryReadOnlyProtocol,
    RoutineRepositoryReadOnlyProtocol,
    TacticRepositoryReadOnlyProtocol,
    TaskDefinitionRepositoryReadOnlyProtocol,
    TaskRepositoryReadOnlyProtocol,
    TimeBlockDefinitionRepositoryReadOnlyProtocol,
    TriggerRepositoryReadOnlyProtocol,
    UseCaseConfigRepositoryReadOnlyProtocol,
    UserRepositoryReadOnlyProtocol,
)
from lykke.application.unit_of_work import (
    ReadOnlyRepositories,
    UnitOfWorkFactory,
    UnitOfWorkProtocol,
)
from lykke.domain import value_objects


class PreviewDayHandlerProtocol(Protocol):
    """Protocol for PreviewDayHandler interface."""

    async def preview_day(
        self, target_date: date, template_id: UUID | None = None
    ) -> value_objects.DayContext:
        """Preview what a day would look like if scheduled."""
        ...


def create_repo_double(protocol_class: type | str) -> InstanceDouble:
    """Create a dobles InstanceDouble for a repository protocol.

    Args:
        protocol_class: The repository protocol class or string path to double.

    Returns:
        An InstanceDouble instance that implements the protocol.
    """
    if isinstance(protocol_class, str):
        return InstanceDouble(protocol_class)
    # Convert class to string path
    module = protocol_class.__module__
    name = protocol_class.__name__
    return InstanceDouble(f"{module}.{name}")


def create_gateway_double(protocol_class: type | str) -> InstanceDouble:
    """Create a dobles InstanceDouble for a gateway protocol.

    Args:
        protocol_class: The gateway protocol class or string path to double.

    Returns:
        An InstanceDouble instance that implements the protocol.
    """
    return create_repo_double(protocol_class)


def create_task_repo_double() -> InstanceDouble:
    """Create a dobles double for TaskRepositoryReadOnlyProtocol."""
    return create_repo_double(TaskRepositoryReadOnlyProtocol)


def create_day_repo_double() -> InstanceDouble:
    """Create a dobles double for DayRepositoryReadOnlyProtocol."""
    return create_repo_double(DayRepositoryReadOnlyProtocol)


def create_day_template_repo_double() -> InstanceDouble:
    """Create a dobles double for DayTemplateRepositoryReadOnlyProtocol."""
    return create_repo_double(DayTemplateRepositoryReadOnlyProtocol)


def create_brain_dump_repo_double() -> InstanceDouble:
    """Create a dobles double for BrainDumpRepositoryReadOnlyProtocol."""
    return create_repo_double(BrainDumpRepositoryReadOnlyProtocol)


def create_calendar_entry_repo_double() -> InstanceDouble:
    """Create a dobles double for CalendarEntryRepositoryReadOnlyProtocol."""
    return create_repo_double(CalendarEntryRepositoryReadOnlyProtocol)


def create_calendar_entry_series_repo_double() -> InstanceDouble:
    """Create a dobles double for CalendarEntrySeriesRepositoryReadOnlyProtocol."""
    return create_repo_double(CalendarEntrySeriesRepositoryReadOnlyProtocol)


def create_calendar_repo_double() -> InstanceDouble:
    """Create a dobles double for CalendarRepositoryReadOnlyProtocol."""
    return create_repo_double(CalendarRepositoryReadOnlyProtocol)


def create_auth_token_repo_double() -> InstanceDouble:
    """Create a dobles double for AuthTokenRepositoryReadOnlyProtocol."""
    return create_repo_double(AuthTokenRepositoryReadOnlyProtocol)


def create_user_repo_double() -> InstanceDouble:
    """Create a dobles double for UserRepositoryReadOnlyProtocol."""
    return create_repo_double(UserRepositoryReadOnlyProtocol)


def create_routine_definition_repo_double() -> InstanceDouble:
    """Create a dobles double for RoutineDefinitionRepositoryReadOnlyProtocol."""
    return create_repo_double(RoutineDefinitionRepositoryReadOnlyProtocol)


def create_routine_repo_double() -> InstanceDouble:
    """Create a dobles double for RoutineRepositoryReadOnlyProtocol."""
    return create_repo_double(RoutineRepositoryReadOnlyProtocol)


def create_task_definition_repo_double() -> InstanceDouble:
    """Create a dobles double for TaskDefinitionRepositoryReadOnlyProtocol."""
    return create_repo_double(TaskDefinitionRepositoryReadOnlyProtocol)


def create_time_block_definition_repo_double() -> InstanceDouble:
    """Create a dobles double for TimeBlockDefinitionRepositoryReadOnlyProtocol."""
    return create_repo_double(TimeBlockDefinitionRepositoryReadOnlyProtocol)


def create_tactic_repo_double() -> InstanceDouble:
    """Create a dobles double for TacticRepositoryReadOnlyProtocol."""
    return create_repo_double(TacticRepositoryReadOnlyProtocol)


def create_trigger_repo_double() -> InstanceDouble:
    """Create a dobles double for TriggerRepositoryReadOnlyProtocol."""
    return create_repo_double(TriggerRepositoryReadOnlyProtocol)


def create_push_subscription_repo_double() -> InstanceDouble:
    """Create a dobles double for PushSubscriptionRepositoryReadOnlyProtocol."""
    return create_repo_double(PushSubscriptionRepositoryReadOnlyProtocol)


def create_google_gateway_double() -> InstanceDouble:
    """Create a dobles double for GoogleCalendarGatewayProtocol."""
    return create_gateway_double(GoogleCalendarGatewayProtocol)


def create_web_push_gateway_double() -> InstanceDouble:
    """Create a dobles double for WebPushGatewayProtocol."""
    return create_gateway_double(WebPushGatewayProtocol)


def create_pubsub_gateway_double() -> InstanceDouble:
    """Create a dobles double for PubSubGatewayProtocol."""
    return create_gateway_double(PubSubGatewayProtocol)


def _protocol_to_string(protocol_class: type) -> str:
    """Convert a protocol class to its string path for dobles."""
    module = protocol_class.__module__
    name = protocol_class.__name__
    return f"{module}.{name}"


def create_read_only_repos_double(
    *,
    audit_log_repo: InstanceDouble | None = None,
    auth_token_repo: InstanceDouble | None = None,
    bot_personality_repo: InstanceDouble | None = None,
    brain_dump_repo: InstanceDouble | None = None,
    calendar_entry_repo: InstanceDouble | None = None,
    calendar_entry_series_repo: InstanceDouble | None = None,
    calendar_repo: InstanceDouble | None = None,
    conversation_repo: InstanceDouble | None = None,
    day_repo: InstanceDouble | None = None,
    day_template_repo: InstanceDouble | None = None,
    factoid_repo: InstanceDouble | None = None,
    message_repo: InstanceDouble | None = None,
    push_notification_repo: InstanceDouble | None = None,
    push_subscription_repo: InstanceDouble | None = None,
    routine_repo: InstanceDouble | None = None,
    routine_definition_repo: InstanceDouble | None = None,
    tactic_repo: InstanceDouble | None = None,
    task_definition_repo: InstanceDouble | None = None,
    task_repo: InstanceDouble | None = None,
    time_block_definition_repo: InstanceDouble | None = None,
    trigger_repo: InstanceDouble | None = None,
    usecase_config_repo: InstanceDouble | None = None,
    user_repo: InstanceDouble | None = None,
) -> InstanceDouble:
    """Create a dobles double for ReadOnlyRepositories protocol.

    Args:
        *: Optional repository doubles to include. If not provided, creates
           minimal doubles for each required repository.

    Returns:
        An InstanceDouble that implements ReadOnlyRepositories protocol.
    """
    repos_double = InstanceDouble(_protocol_to_string(ReadOnlyRepositories))

    # Set all repository properties
    repos_double.audit_log_ro_repo = (
        audit_log_repo or create_repo_double(AuditLogRepositoryReadOnlyProtocol)
    )
    repos_double.auth_token_ro_repo = (
        auth_token_repo or create_repo_double(AuthTokenRepositoryReadOnlyProtocol)
    )
    repos_double.bot_personality_ro_repo = (
        bot_personality_repo
        or create_repo_double(BotPersonalityRepositoryReadOnlyProtocol)
    )
    repos_double.brain_dump_ro_repo = (
        brain_dump_repo or create_repo_double(BrainDumpRepositoryReadOnlyProtocol)
    )
    repos_double.calendar_entry_ro_repo = (
        calendar_entry_repo
        or create_repo_double(CalendarEntryRepositoryReadOnlyProtocol)
    )
    repos_double.calendar_entry_series_ro_repo = (
        calendar_entry_series_repo
        or create_repo_double(CalendarEntrySeriesRepositoryReadOnlyProtocol)
    )
    repos_double.calendar_ro_repo = (
        calendar_repo or create_repo_double(CalendarRepositoryReadOnlyProtocol)
    )
    repos_double.conversation_ro_repo = (
        conversation_repo or create_repo_double(ConversationRepositoryReadOnlyProtocol)
    )
    repos_double.day_ro_repo = (
        day_repo or create_repo_double(DayRepositoryReadOnlyProtocol)
    )
    repos_double.day_template_ro_repo = (
        day_template_repo or create_repo_double(DayTemplateRepositoryReadOnlyProtocol)
    )
    repos_double.factoid_ro_repo = (
        factoid_repo or create_repo_double(FactoidRepositoryReadOnlyProtocol)
    )
    repos_double.message_ro_repo = (
        message_repo or create_repo_double(MessageRepositoryReadOnlyProtocol)
    )
    repos_double.push_notification_ro_repo = (
        push_notification_repo
        or create_repo_double(PushNotificationRepositoryReadOnlyProtocol)
    )
    repos_double.push_subscription_ro_repo = (
        push_subscription_repo
        or create_repo_double(PushSubscriptionRepositoryReadOnlyProtocol)
    )
    repos_double.routine_ro_repo = (
        routine_repo or create_repo_double(RoutineRepositoryReadOnlyProtocol)
    )
    repos_double.routine_definition_ro_repo = (
        routine_definition_repo
        or create_repo_double(RoutineDefinitionRepositoryReadOnlyProtocol)
    )
    repos_double.tactic_ro_repo = (
        tactic_repo or create_repo_double(TacticRepositoryReadOnlyProtocol)
    )
    repos_double.task_definition_ro_repo = (
        task_definition_repo
        or create_repo_double(TaskDefinitionRepositoryReadOnlyProtocol)
    )
    repos_double.task_ro_repo = (
        task_repo or create_repo_double(TaskRepositoryReadOnlyProtocol)
    )
    repos_double.time_block_definition_ro_repo = (
        time_block_definition_repo
        or create_repo_double(TimeBlockDefinitionRepositoryReadOnlyProtocol)
    )
    repos_double.trigger_ro_repo = (
        trigger_repo or create_repo_double(TriggerRepositoryReadOnlyProtocol)
    )
    repos_double.usecase_config_ro_repo = (
        usecase_config_repo
        or create_repo_double(UseCaseConfigRepositoryReadOnlyProtocol)
    )
    repos_double.user_ro_repo = (
        user_repo or create_repo_double(UserRepositoryReadOnlyProtocol)
    )

    return repos_double


def create_uow_double(
    *,
    audit_log_repo: InstanceDouble | None = None,
    auth_token_repo: InstanceDouble | None = None,
    bot_personality_repo: InstanceDouble | None = None,
    brain_dump_repo: InstanceDouble | None = None,
    calendar_entry_repo: InstanceDouble | None = None,
    calendar_entry_series_repo: InstanceDouble | None = None,
    calendar_repo: InstanceDouble | None = None,
    conversation_repo: InstanceDouble | None = None,
    day_repo: InstanceDouble | None = None,
    day_template_repo: InstanceDouble | None = None,
    factoid_repo: InstanceDouble | None = None,
    message_repo: InstanceDouble | None = None,
    push_notification_repo: InstanceDouble | None = None,
    push_subscription_repo: InstanceDouble | None = None,
    routine_repo: InstanceDouble | None = None,
    routine_definition_repo: InstanceDouble | None = None,
    tactic_repo: InstanceDouble | None = None,
    task_definition_repo: InstanceDouble | None = None,
    task_repo: InstanceDouble | None = None,
    time_block_definition_repo: InstanceDouble | None = None,
    trigger_repo: InstanceDouble | None = None,
    usecase_config_repo: InstanceDouble | None = None,
    user_repo: InstanceDouble | None = None,
) -> InstanceDouble:
    """Create a dobles double for UnitOfWorkProtocol.

    Args:
        *: Optional repository doubles to include. If not provided, creates
           minimal doubles for each required repository.

    Returns:
        An InstanceDouble that implements UnitOfWorkProtocol.
    """
    uow_double = InstanceDouble(_protocol_to_string(UnitOfWorkProtocol))

    # Set all repository properties
    uow_double.audit_log_ro_repo = (
        audit_log_repo or create_repo_double(AuditLogRepositoryReadOnlyProtocol)
    )
    uow_double.auth_token_ro_repo = (
        auth_token_repo or create_repo_double(AuthTokenRepositoryReadOnlyProtocol)
    )
    uow_double.bot_personality_ro_repo = (
        bot_personality_repo
        or create_repo_double(BotPersonalityRepositoryReadOnlyProtocol)
    )
    uow_double.brain_dump_ro_repo = (
        brain_dump_repo or create_repo_double(BrainDumpRepositoryReadOnlyProtocol)
    )
    uow_double.calendar_entry_ro_repo = (
        calendar_entry_repo
        or create_repo_double(CalendarEntryRepositoryReadOnlyProtocol)
    )
    uow_double.calendar_entry_series_ro_repo = (
        calendar_entry_series_repo
        or create_repo_double(CalendarEntrySeriesRepositoryReadOnlyProtocol)
    )
    uow_double.calendar_ro_repo = (
        calendar_repo or create_repo_double(CalendarRepositoryReadOnlyProtocol)
    )
    uow_double.conversation_ro_repo = (
        conversation_repo or create_repo_double(ConversationRepositoryReadOnlyProtocol)
    )
    uow_double.day_ro_repo = (
        day_repo or create_repo_double(DayRepositoryReadOnlyProtocol)
    )
    uow_double.day_template_ro_repo = (
        day_template_repo or create_repo_double(DayTemplateRepositoryReadOnlyProtocol)
    )
    uow_double.factoid_ro_repo = (
        factoid_repo or create_repo_double(FactoidRepositoryReadOnlyProtocol)
    )
    uow_double.message_ro_repo = (
        message_repo or create_repo_double(MessageRepositoryReadOnlyProtocol)
    )
    uow_double.push_notification_ro_repo = (
        push_notification_repo
        or create_repo_double(PushNotificationRepositoryReadOnlyProtocol)
    )
    uow_double.push_subscription_ro_repo = (
        push_subscription_repo
        or create_repo_double(PushSubscriptionRepositoryReadOnlyProtocol)
    )
    uow_double.routine_ro_repo = (
        routine_repo or create_repo_double(RoutineRepositoryReadOnlyProtocol)
    )
    uow_double.routine_definition_ro_repo = (
        routine_definition_repo
        or create_repo_double(RoutineDefinitionRepositoryReadOnlyProtocol)
    )
    uow_double.tactic_ro_repo = (
        tactic_repo or create_repo_double(TacticRepositoryReadOnlyProtocol)
    )
    uow_double.task_definition_ro_repo = (
        task_definition_repo
        or create_repo_double(TaskDefinitionRepositoryReadOnlyProtocol)
    )
    uow_double.task_ro_repo = (
        task_repo or create_repo_double(TaskRepositoryReadOnlyProtocol)
    )
    uow_double.time_block_definition_ro_repo = (
        time_block_definition_repo
        or create_repo_double(TimeBlockDefinitionRepositoryReadOnlyProtocol)
    )
    uow_double.trigger_ro_repo = (
        trigger_repo or create_repo_double(TriggerRepositoryReadOnlyProtocol)
    )
    uow_double.usecase_config_ro_repo = (
        usecase_config_repo
        or create_repo_double(UseCaseConfigRepositoryReadOnlyProtocol)
    )
    uow_double.user_ro_repo = (
        user_repo or create_repo_double(UserRepositoryReadOnlyProtocol)
    )

    # Stub async context manager methods
    allow(uow_double).__aenter__.and_return(uow_double)
    allow(uow_double).__aexit__.and_return(None)

    # Stub async methods
    allow(uow_double).commit.and_return(None)
    allow(uow_double).rollback.and_return(None)
    allow(uow_double).create.and_return(None)
    allow(uow_double).delete.and_return(None)
    allow(uow_double).bulk_delete_tasks.and_return(None)
    allow(uow_double).bulk_delete_routines.and_return(None)
    allow(uow_double).bulk_delete_calendar_entries.and_return(None)
    allow(uow_double).bulk_delete_audit_logs.and_return(None)
    allow(uow_double).set_trigger_tactics.and_return(None)

    # Stub add method (synchronous)
    allow(uow_double).add.and_return(None)

    # Track added entities
    uow_double.added: list[Any] = []
    uow_double.created: list[Any] = []
    uow_double.deleted: list[Any] = []
    uow_double.bulk_deleted_tasks: list[Any] = []
    uow_double.bulk_deleted_routines: list[Any] = []

    # Override add to track entities - use a callable that dobles will invoke
    # We need to set this up so the function gets called, not returned
    # Dobles doesn't support returning callables directly, so we'll use a different pattern
    # For now, just return the entity and track separately via a wrapper
    def make_track_add():
        def track_add(entity: Any) -> Any:
            uow_double.added.append(entity)
            return entity
        return track_add

    # Manually assign the method since dobles and_return doesn't support callables
    uow_double.add = make_track_add()

    # For async methods, we need to return coroutines
    async def track_create_async(entity: Any) -> Any:
        uow_double.created.append(entity)
        if hasattr(entity, "create"):
            entity.create()
        return entity

    # Manually assign async methods
    uow_double.create = track_create_async

    async def track_delete_async(entity: Any) -> None:
        if hasattr(entity, "delete"):
            entity.delete()
        uow_double.deleted.append(entity)

    uow_double.delete = track_delete_async

    async def track_bulk_delete_tasks_async(query: Any) -> None:
        uow_double.bulk_deleted_tasks.append(query)

    uow_double.bulk_delete_tasks = track_bulk_delete_tasks_async

    async def track_bulk_delete_routines_async(query: Any) -> None:
        uow_double.bulk_deleted_routines.append(query)

    uow_double.bulk_delete_routines = track_bulk_delete_routines_async

    return uow_double


def create_uow_factory_double(uow: InstanceDouble) -> InstanceDouble:
    """Create a dobles double for UnitOfWorkFactory.

    Args:
        uow: The UnitOfWork double to return from create().

    Returns:
        An InstanceDouble that implements UnitOfWorkFactory protocol.
    """
    factory_double = InstanceDouble(_protocol_to_string(UnitOfWorkFactory))
    allow(factory_double).create.and_return(uow)
    return factory_double


def create_preview_day_handler_double() -> InstanceDouble:
    """Create a dobles double for PreviewDayHandlerProtocol."""
    return InstanceDouble(_protocol_to_string(PreviewDayHandlerProtocol))
