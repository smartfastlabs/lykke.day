"""Unit of Work pattern for managing transactions and repositories.

The Unit of Work pattern provides a way to:
1. Group multiple repository operations into a single transaction
2. Ensure all repositories share the same database connection
3. Handle domain event dispatching after commit
4. Provide a clean abstraction for testing
5. Track entities that need to be saved (via add() method)
"""

from typing import Protocol, Self
from uuid import UUID

from lykke.application.repositories import (
    AuthTokenRepositoryReadOnlyProtocol,
    CalendarEntryRepositoryReadOnlyProtocol,
    CalendarEntrySeriesRepositoryReadOnlyProtocol,
    CalendarRepositoryReadOnlyProtocol,
    DayRepositoryReadOnlyProtocol,
    DayTemplateRepositoryReadOnlyProtocol,
    PushSubscriptionRepositoryReadOnlyProtocol,
    RoutineRepositoryReadOnlyProtocol,
    TaskDefinitionRepositoryReadOnlyProtocol,
    TaskRepositoryReadOnlyProtocol,
    UserRepositoryReadOnlyProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities.base import BaseEntityObject


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

    # Read-only repository properties (for reading entities)
    auth_token_ro_repo: AuthTokenRepositoryReadOnlyProtocol
    calendar_entry_ro_repo: CalendarEntryRepositoryReadOnlyProtocol
    calendar_entry_series_ro_repo: CalendarEntrySeriesRepositoryReadOnlyProtocol
    calendar_ro_repo: CalendarRepositoryReadOnlyProtocol
    day_ro_repo: DayRepositoryReadOnlyProtocol
    day_template_ro_repo: DayTemplateRepositoryReadOnlyProtocol
    push_subscription_ro_repo: PushSubscriptionRepositoryReadOnlyProtocol
    routine_ro_repo: RoutineRepositoryReadOnlyProtocol
    task_definition_ro_repo: TaskDefinitionRepositoryReadOnlyProtocol
    task_ro_repo: TaskRepositoryReadOnlyProtocol
    user_ro_repo: UserRepositoryReadOnlyProtocol

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

    def add(self, entity: BaseEntityObject) -> None:
        """Add an entity to be tracked for persistence.

        Only entities added via this method will be saved when commit() is called.
        The commit() method will inspect domain events on each added entity to
        determine whether to create, update, or delete it.

        Args:
            entity: The entity to track for persistence.
        """
        ...

    async def create(self, entity: BaseEntityObject) -> None:
        """Create a new entity.

        This method:
        1. Verifies the entity does not already exist
        2. Calls entity.create() to mark it as newly created
        3. Adds the entity to be tracked for persistence

        Args:
            entity: The entity to create

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
    calendar_entry_series_ro_repo: CalendarEntrySeriesRepositoryReadOnlyProtocol
    calendar_ro_repo: CalendarRepositoryReadOnlyProtocol
    day_ro_repo: DayRepositoryReadOnlyProtocol
    day_template_ro_repo: DayTemplateRepositoryReadOnlyProtocol
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
