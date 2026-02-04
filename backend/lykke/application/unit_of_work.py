"""Unit of Work pattern for managing transactions and repositories.

The Unit of Work pattern provides a way to:
1. Group multiple repository operations into a single transaction
2. Ensure all repositories share the same database connection
3. Handle domain event dispatching after commit
4. Provide a clean abstraction for testing
5. Track entities that need to be saved (via add() method)
"""

from typing import TYPE_CHECKING, Protocol, Self, TypeVar
from uuid import UUID

from lykke.application.repositories import (
    AuditLogRepositoryReadOnlyProtocol,
    AuthTokenRepositoryReadOnlyProtocol,
    AuthTokenRepositoryReadWriteProtocol,
    BotPersonalityRepositoryReadOnlyProtocol,
    BotPersonalityRepositoryReadWriteProtocol,
    BrainDumpRepositoryReadOnlyProtocol,
    BrainDumpRepositoryReadWriteProtocol,
    CalendarEntryRepositoryReadOnlyProtocol,
    CalendarEntryRepositoryReadWriteProtocol,
    CalendarEntrySeriesRepositoryReadOnlyProtocol,
    CalendarEntrySeriesRepositoryReadWriteProtocol,
    CalendarRepositoryReadOnlyProtocol,
    CalendarRepositoryReadWriteProtocol,
    DayRepositoryReadOnlyProtocol,
    DayRepositoryReadWriteProtocol,
    DayTemplateRepositoryReadOnlyProtocol,
    DayTemplateRepositoryReadWriteProtocol,
    FactoidRepositoryReadOnlyProtocol,
    FactoidRepositoryReadWriteProtocol,
    MessageRepositoryReadOnlyProtocol,
    MessageRepositoryReadWriteProtocol,
    PushNotificationRepositoryReadOnlyProtocol,
    PushNotificationRepositoryReadWriteProtocol,
    PushSubscriptionRepositoryReadOnlyProtocol,
    PushSubscriptionRepositoryReadWriteProtocol,
    RoutineDefinitionRepositoryReadOnlyProtocol,
    RoutineDefinitionRepositoryReadWriteProtocol,
    RoutineRepositoryReadOnlyProtocol,
    RoutineRepositoryReadWriteProtocol,
    SmsLoginCodeRepositoryReadOnlyProtocol,
    SmsLoginCodeRepositoryReadWriteProtocol,
    TacticRepositoryReadOnlyProtocol,
    TacticRepositoryReadWriteProtocol,
    TaskDefinitionRepositoryReadOnlyProtocol,
    TaskDefinitionRepositoryReadWriteProtocol,
    TaskRepositoryReadOnlyProtocol,
    TaskRepositoryReadWriteProtocol,
    TimeBlockDefinitionRepositoryReadOnlyProtocol,
    TimeBlockDefinitionRepositoryReadWriteProtocol,
    TriggerRepositoryReadOnlyProtocol,
    TriggerRepositoryReadWriteProtocol,
    UseCaseConfigRepositoryReadOnlyProtocol,
    UseCaseConfigRepositoryReadWriteProtocol,
    UserRepositoryReadOnlyProtocol,
    UserRepositoryReadWriteProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import UserEntity
from lykke.domain.entities.base import BaseEntityObject

if TYPE_CHECKING:
    from lykke.application.worker_schedule import WorkersToScheduleProtocol

# Type variable for entities
_T = TypeVar("_T", bound=BaseEntityObject)


class UnitOfWorkProtocol(Protocol):
    """Protocol for Unit of Work pattern.

    Provides access to read-only repositories for querying and an add() method
    for tracking entities that need to be saved. All repositories share the same
    database connection and transaction context.

    Commands should use:
    - ro_repo properties for reading entities
    - add() method for tracking entities to save
    - commit() to persist changes

    The commit() method will:
    1. Process all added entities (create, update, delete based on domain events)
    2. Collect domain events from all aggregates
    3. Commit the database transaction
    4. Dispatch domain events
    """

    # Workers to schedule after commit; flushed to broker only on successful commit
    workers_to_schedule: "WorkersToScheduleProtocol"

    async def __aenter__(self) -> Self:
        """Enter the unit of work context.

        Returns:
            The unit of work instance.
        """
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit the unit of work context.

        Automatically commits on success or rolls back on exception.
        """
        ...

    def add(self, entity: _T) -> _T:
        """Add an entity to be tracked for persistence.

        Only entities added via this method will be saved when commit() is called.
        The commit() method will inspect domain events on each added entity to
        determine whether to create, update, or delete it.

        Args:
            entity: The entity to track for persistence.

        Returns:
            The entity that was added.
        """
        ...

    async def create(self, entity: _T) -> _T:
        """Create a new entity.

        This method:
        1. Verifies the entity does not already exist
        2. Calls entity.create() to mark it as newly created
        3. Adds the entity to be tracked for persistence

        Args:
            entity: The entity to create

        Returns:
            The entity that was created.

        Raises:
            BadRequestError: If the entity already exists
        """
        ...

    async def delete(self, entity: BaseEntityObject) -> None:
        """Delete an existing entity.

        This method:
        1. Verifies the entity exists
        2. Calls entity.delete() to mark it for deletion
        3. Adds the entity to be tracked for persistence

        Args:
            entity: The entity to delete

        Raises:
            NotFoundError: If the entity does not exist
        """
        ...

    async def commit(self) -> None:
        """Commit the current transaction.

        This will:
        1. Process all added entities (create, update, delete based on domain events)
        2. Collect domain events from all aggregates
        3. Commit the database transaction
        4. Dispatch domain events
        """
        ...

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        ...

    async def bulk_delete_calendar_entries(
        self, query: value_objects.CalendarEntryQuery
    ) -> None:
        """Bulk delete calendar entries matching query filters."""
        ...

    async def bulk_delete_tasks(self, query: value_objects.TaskQuery) -> None:
        """Bulk delete tasks matching query filters."""
        ...

    async def bulk_delete_routines(self, query: value_objects.RoutineQuery) -> None:
        """Bulk delete routines matching query filters."""
        ...

    async def bulk_delete_audit_logs(self, query: value_objects.AuditLogQuery) -> None:
        """Bulk delete audit logs matching query filters."""
        ...

    async def set_trigger_tactics(
        self, trigger_id: UUID, tactic_ids: list[UUID]
    ) -> None:
        """Replace all tactics linked to a trigger."""
        ...


class UnitOfWorkFactory(Protocol):
    """Factory protocol for creating UnitOfWork instances.

    This allows the application layer to create units of work without
    depending on infrastructure implementations.
    """

    def create(self, user: UserEntity) -> UnitOfWorkProtocol:
        """Create a new UnitOfWork instance for the given user.

        Args:
            user: The user entity to scope the unit of work to.

        Returns:
            A new UnitOfWork instance (not yet entered).
        """
        ...


class ReadOnlyRepositories(Protocol):
    """Protocol for providing read-only repositories.

    This is used by query handlers to access read-only repositories
    without the ability to perform writes. Each repository manages
    its own database connections for read operations.
    """

    # Read-only repository properties
    audit_log_ro_repo: AuditLogRepositoryReadOnlyProtocol
    auth_token_ro_repo: AuthTokenRepositoryReadOnlyProtocol
    bot_personality_ro_repo: BotPersonalityRepositoryReadOnlyProtocol
    brain_dump_ro_repo: BrainDumpRepositoryReadOnlyProtocol
    calendar_entry_ro_repo: CalendarEntryRepositoryReadOnlyProtocol
    calendar_entry_series_ro_repo: CalendarEntrySeriesRepositoryReadOnlyProtocol
    calendar_ro_repo: CalendarRepositoryReadOnlyProtocol
    day_ro_repo: DayRepositoryReadOnlyProtocol
    day_template_ro_repo: DayTemplateRepositoryReadOnlyProtocol
    factoid_ro_repo: FactoidRepositoryReadOnlyProtocol
    message_ro_repo: MessageRepositoryReadOnlyProtocol
    push_notification_ro_repo: PushNotificationRepositoryReadOnlyProtocol
    push_subscription_ro_repo: PushSubscriptionRepositoryReadOnlyProtocol
    routine_ro_repo: RoutineRepositoryReadOnlyProtocol
    routine_definition_ro_repo: RoutineDefinitionRepositoryReadOnlyProtocol
    tactic_ro_repo: TacticRepositoryReadOnlyProtocol
    task_definition_ro_repo: TaskDefinitionRepositoryReadOnlyProtocol
    task_ro_repo: TaskRepositoryReadOnlyProtocol
    time_block_definition_ro_repo: TimeBlockDefinitionRepositoryReadOnlyProtocol
    trigger_ro_repo: TriggerRepositoryReadOnlyProtocol
    usecase_config_ro_repo: UseCaseConfigRepositoryReadOnlyProtocol
    user_ro_repo: UserRepositoryReadOnlyProtocol
    sms_login_code_ro_repo: SmsLoginCodeRepositoryReadOnlyProtocol


class ReadOnlyRepositoryFactory(Protocol):
    """Factory protocol for creating ReadOnlyRepositories instances.

    This allows query handlers to access read-only repositories without
    the ability to perform writes.
    """

    def create(self, user: UserEntity) -> ReadOnlyRepositories:
        """Create read-only repositories for the given user.

        Args:
            user: The user entity to scope the repositories to.

        Returns:
            Read-only repositories scoped to the user.
        """
        ...


class ReadWriteRepositories(Protocol):
    """Protocol for providing read-write repositories.

    This is used when a handler needs explicit read-write repository access
    without a Unit of Work. Each repository manages its own connections.
    """

    auth_token_rw_repo: AuthTokenRepositoryReadWriteProtocol
    bot_personality_rw_repo: BotPersonalityRepositoryReadWriteProtocol
    brain_dump_rw_repo: BrainDumpRepositoryReadWriteProtocol
    calendar_entry_rw_repo: CalendarEntryRepositoryReadWriteProtocol
    calendar_entry_series_rw_repo: CalendarEntrySeriesRepositoryReadWriteProtocol
    calendar_rw_repo: CalendarRepositoryReadWriteProtocol
    day_rw_repo: DayRepositoryReadWriteProtocol
    day_template_rw_repo: DayTemplateRepositoryReadWriteProtocol
    factoid_rw_repo: FactoidRepositoryReadWriteProtocol
    message_rw_repo: MessageRepositoryReadWriteProtocol
    push_notification_rw_repo: PushNotificationRepositoryReadWriteProtocol
    push_subscription_rw_repo: PushSubscriptionRepositoryReadWriteProtocol
    routine_rw_repo: RoutineRepositoryReadWriteProtocol
    routine_definition_rw_repo: RoutineDefinitionRepositoryReadWriteProtocol
    tactic_rw_repo: TacticRepositoryReadWriteProtocol
    task_definition_rw_repo: TaskDefinitionRepositoryReadWriteProtocol
    task_rw_repo: TaskRepositoryReadWriteProtocol
    time_block_definition_rw_repo: TimeBlockDefinitionRepositoryReadWriteProtocol
    trigger_rw_repo: TriggerRepositoryReadWriteProtocol
    usecase_config_rw_repo: UseCaseConfigRepositoryReadWriteProtocol
    user_rw_repo: UserRepositoryReadWriteProtocol
    sms_login_code_rw_repo: SmsLoginCodeRepositoryReadWriteProtocol


class ReadWriteRepositoryFactory(Protocol):
    """Factory protocol for creating ReadWriteRepositories instances."""

    def create(self, user: UserEntity) -> ReadWriteRepositories:
        """Create read-write repositories for the given user."""
        ...
