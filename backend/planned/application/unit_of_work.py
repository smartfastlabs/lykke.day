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


class UnitOfWorkProtocol(Protocol):
    """Protocol for Unit of Work pattern.

    Provides access to all repositories scoped to a single transaction.
    All repositories share the same database connection and transaction context.
    """

    # Repository properties
    auth_tokens: AuthTokenRepositoryProtocol
    calendars: CalendarRepositoryProtocol
    days: DayRepositoryProtocol
    day_templates: DayTemplateRepositoryProtocol
    events: EventRepositoryProtocol
    messages: MessageRepositoryProtocol
    push_subscriptions: PushSubscriptionRepositoryProtocol
    routines: RoutineRepositoryProtocol
    task_definitions: TaskDefinitionRepositoryProtocol
    tasks: TaskRepositoryProtocol
    users: UserRepositoryProtocol

    async def __aenter__(self) -> Self:
        """Enter the unit of work context.

        Returns:
            The unit of work instance.
        """
        ...

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object) -> None:
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

