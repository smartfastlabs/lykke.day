"""Unit of Work pattern for managing transactions and repositories.

The Unit of Work pattern provides a way to:
1. Group multiple repository operations into a single transaction
2. Ensure all repositories share the same database connection
3. Handle domain event dispatching after commit
4. Provide a clean abstraction for testing
"""

from typing import Protocol, Self
from uuid import UUID

from planned.application.repositories import (
    AuthTokenRepositoryReadOnlyProtocol,
    AuthTokenRepositoryReadWriteProtocol,
    CalendarEntryRepositoryReadOnlyProtocol,
    CalendarEntryRepositoryReadWriteProtocol,
    CalendarRepositoryReadOnlyProtocol,
    CalendarRepositoryReadWriteProtocol,
    DayRepositoryReadOnlyProtocol,
    DayRepositoryReadWriteProtocol,
    DayTemplateRepositoryReadOnlyProtocol,
    DayTemplateRepositoryReadWriteProtocol,
    MessageRepositoryReadOnlyProtocol,
    MessageRepositoryReadWriteProtocol,
    PushSubscriptionRepositoryReadOnlyProtocol,
    PushSubscriptionRepositoryReadWriteProtocol,
    RoutineRepositoryReadOnlyProtocol,
    RoutineRepositoryReadWriteProtocol,
    TaskDefinitionRepositoryReadOnlyProtocol,
    TaskDefinitionRepositoryReadWriteProtocol,
    TaskRepositoryReadOnlyProtocol,
    TaskRepositoryReadWriteProtocol,
    UserRepositoryReadOnlyProtocol,
    UserRepositoryReadWriteProtocol,
)


class UnitOfWorkProtocol(Protocol):
    """Protocol for Unit of Work pattern.

    Provides access to all repositories scoped to a single transaction.
    All repositories share the same database connection and transaction context.
    Provides both read-only and read-write repositories with explicit naming.
    """

    # Read-only repository properties (for query handlers)
    auth_token_ro_repo: AuthTokenRepositoryReadOnlyProtocol
    calendar_entry_ro_repo: CalendarEntryRepositoryReadOnlyProtocol
    calendar_ro_repo: CalendarRepositoryReadOnlyProtocol
    day_ro_repo: DayRepositoryReadOnlyProtocol
    day_template_ro_repo: DayTemplateRepositoryReadOnlyProtocol
    message_ro_repo: MessageRepositoryReadOnlyProtocol
    push_subscription_ro_repo: PushSubscriptionRepositoryReadOnlyProtocol
    routine_ro_repo: RoutineRepositoryReadOnlyProtocol
    task_definition_ro_repo: TaskDefinitionRepositoryReadOnlyProtocol
    task_ro_repo: TaskRepositoryReadOnlyProtocol
    user_ro_repo: UserRepositoryReadOnlyProtocol

    # Read-write repository properties (for command handlers)
    auth_token_rw_repo: AuthTokenRepositoryReadWriteProtocol
    calendar_entry_rw_repo: CalendarEntryRepositoryReadWriteProtocol
    calendar_rw_repo: CalendarRepositoryReadWriteProtocol
    day_rw_repo: DayRepositoryReadWriteProtocol
    day_template_rw_repo: DayTemplateRepositoryReadWriteProtocol
    message_rw_repo: MessageRepositoryReadWriteProtocol
    push_subscription_rw_repo: PushSubscriptionRepositoryReadWriteProtocol
    routine_rw_repo: RoutineRepositoryReadWriteProtocol
    task_definition_rw_repo: TaskDefinitionRepositoryReadWriteProtocol
    task_rw_repo: TaskRepositoryReadWriteProtocol
    user_rw_repo: UserRepositoryReadWriteProtocol

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

    async def commit(self) -> None:
        """Commit the current transaction.

        This should:
        1. Collect domain events from all aggregates
        2. Dispatch domain events
        3. Commit the database transaction
        """
        ...

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        ...


class UnitOfWorkFactory(Protocol):
    """Factory protocol for creating UnitOfWork instances.

    This allows the application layer to create units of work without
    depending on infrastructure implementations.
    """

    def create(self, user_id: UUID) -> UnitOfWorkProtocol:
        """Create a new UnitOfWork instance for the given user.

        Args:
            user_id: The UUID of the user to scope the unit of work to.

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
    auth_token_ro_repo: AuthTokenRepositoryReadOnlyProtocol
    calendar_entry_ro_repo: CalendarEntryRepositoryReadOnlyProtocol
    calendar_ro_repo: CalendarRepositoryReadOnlyProtocol
    day_ro_repo: DayRepositoryReadOnlyProtocol
    day_template_ro_repo: DayTemplateRepositoryReadOnlyProtocol
    message_ro_repo: MessageRepositoryReadOnlyProtocol
    push_subscription_ro_repo: PushSubscriptionRepositoryReadOnlyProtocol
    routine_ro_repo: RoutineRepositoryReadOnlyProtocol
    task_definition_ro_repo: TaskDefinitionRepositoryReadOnlyProtocol
    task_ro_repo: TaskRepositoryReadOnlyProtocol
    user_ro_repo: UserRepositoryReadOnlyProtocol


class ReadOnlyRepositoryFactory(Protocol):
    """Factory protocol for creating ReadOnlyRepositories instances.

    This allows query handlers to access read-only repositories without
    the ability to perform writes.
    """

    def create(self, user_id: UUID) -> ReadOnlyRepositories:
        """Create read-only repositories for the given user.

        Args:
            user_id: The UUID of the user to scope the repositories to.

        Returns:
            Read-only repositories scoped to the user.
        """
        ...
