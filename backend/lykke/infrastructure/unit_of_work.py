"""Infrastructure implementation of Unit of Work pattern using SQLAlchemy."""

from __future__ import annotations

from contextvars import Token
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

from lykke.application.events import send_domain_events
from lykke.application.repositories import (
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
from lykke.application.unit_of_work import (
    ReadOnlyRepositories,
    ReadOnlyRepositoryFactory,
    UnitOfWorkProtocol,
)
from lykke.core.exceptions import BadRequestError, NotFoundError
from lykke.domain.entities import (
    CalendarEntity,
    CalendarEntryEntity,
    DayEntity,
    DayTemplateEntity,
    RoutineEntity,
    TaskEntity,
    UserEntity,
)
from lykke.domain.entities.base import BaseEntityObject
from lykke.domain.events.base import (
    DomainEvent,
    EntityCreatedEvent,
    EntityDeletedEvent,
    EntityUpdatedEvent,
)
from lykke.infrastructure import data_objects
from lykke.infrastructure.database import get_engine
from lykke.infrastructure.database.transaction import (
    get_transaction_connection,
    reset_transaction_connection,
    set_transaction_connection,
)
from lykke.infrastructure.repositories import (
    AuthTokenRepository,
    CalendarEntryRepository,
    CalendarRepository,
    DayRepository,
    DayTemplateRepository,
    PushSubscriptionRepository,
    RoutineRepository,
    TaskDefinitionRepository,
    TaskRepository,
    UserRepository,
)
from sqlalchemy.ext.asyncio import AsyncConnection

if TYPE_CHECKING:
    from typing import Self


class SqlAlchemyUnitOfWork:
    """SQLAlchemy implementation of UnitOfWorkProtocol.

    Manages a single database transaction and provides access to read-only
    repositories for querying and an add() method for tracking entities to save.
    All repositories share the same connection.

    Read-write repositories are kept internally for commit() processing only.
    Commands should not access them directly.
    """

    # Read-only repository type annotations (public API for commands)
    auth_token_ro_repo: AuthTokenRepositoryReadOnlyProtocol
    calendar_entry_ro_repo: CalendarEntryRepositoryReadOnlyProtocol
    calendar_ro_repo: CalendarRepositoryReadOnlyProtocol
    day_ro_repo: DayRepositoryReadOnlyProtocol
    day_template_ro_repo: DayTemplateRepositoryReadOnlyProtocol
    push_subscription_ro_repo: PushSubscriptionRepositoryReadOnlyProtocol
    routine_ro_repo: RoutineRepositoryReadOnlyProtocol
    task_definition_ro_repo: TaskDefinitionRepositoryReadOnlyProtocol
    task_ro_repo: TaskRepositoryReadOnlyProtocol
    user_ro_repo: UserRepositoryReadOnlyProtocol

    def __init__(self, user_id: UUID) -> None:
        """Initialize the unit of work for a specific user.

        Args:
            user_id: The UUID of the user to scope repositories to.
        """
        self.user_id = user_id
        self._connection: AsyncConnection | None = None
        self._token: Token[AsyncConnection | None] | None = None
        self._is_nested = False
        # Track entities that need to be saved
        self._added_entities: list[BaseEntityObject] = []
        # Internal read-write repositories (not exposed to commands)
        self._auth_token_rw_repo: AuthTokenRepositoryReadWriteProtocol | None = None
        self._calendar_entry_rw_repo: (
            CalendarEntryRepositoryReadWriteProtocol | None
        ) = None
        self._calendar_rw_repo: CalendarRepositoryReadWriteProtocol | None = None
        self._day_rw_repo: DayRepositoryReadWriteProtocol | None = None
        self._day_template_rw_repo: DayTemplateRepositoryReadWriteProtocol | None = None
        self._push_subscription_rw_repo: (
            PushSubscriptionRepositoryReadWriteProtocol | None
        ) = None
        self._routine_rw_repo: RoutineRepositoryReadWriteProtocol | None = None
        self._task_definition_rw_repo: (
            TaskDefinitionRepositoryReadWriteProtocol | None
        ) = None
        self._task_rw_repo: TaskRepositoryReadWriteProtocol | None = None
        self._user_rw_repo: UserRepositoryReadWriteProtocol | None = None

    async def __aenter__(self) -> Self:
        """Enter the unit of work context.

        Creates a database connection and transaction, then initializes all repositories
        to use that connection.

        Returns:
            The unit of work instance.
        """
        # Check if there's already an active transaction (nested UoW)
        existing_conn = get_transaction_connection()
        if existing_conn is not None:
            self._is_nested = True
            self._connection = existing_conn
        else:
            # Create a new transaction
            engine = get_engine()
            self._connection = await engine.connect()
            await self._connection.begin()

            # Set the connection in the context variable so repositories can use it
            self._token = set_transaction_connection(self._connection)

        # Initialize all repositories with user scoping (where applicable)
        # UserRepository and AuthTokenRepository are not user-scoped
        # Use cast to satisfy type checker - concrete repos implement both protocols
        # We assign the same instance to both ro and rw since they implement both
        user_repo = cast("UserRepositoryReadWriteProtocol", UserRepository())
        self.user_ro_repo = cast("UserRepositoryReadOnlyProtocol", user_repo)
        self._user_rw_repo = user_repo

        auth_token_repo = cast(
            "AuthTokenRepositoryReadWriteProtocol", AuthTokenRepository()
        )
        self.auth_token_ro_repo = cast(
            "AuthTokenRepositoryReadOnlyProtocol", auth_token_repo
        )
        self._auth_token_rw_repo = auth_token_repo

        # All other repositories are user-scoped
        calendar_repo = cast(
            "CalendarRepositoryReadWriteProtocol",
            CalendarRepository(user_id=self.user_id),
        )
        self.calendar_ro_repo = cast(
            "CalendarRepositoryReadOnlyProtocol", calendar_repo
        )
        self._calendar_rw_repo = calendar_repo

        day_repo = cast(
            "DayRepositoryReadWriteProtocol", DayRepository(user_id=self.user_id)
        )
        self.day_ro_repo = cast("DayRepositoryReadOnlyProtocol", day_repo)
        self._day_rw_repo = day_repo

        day_template_repo = cast(
            "DayTemplateRepositoryReadWriteProtocol",
            DayTemplateRepository(user_id=self.user_id),
        )
        self.day_template_ro_repo = cast(
            "DayTemplateRepositoryReadOnlyProtocol", day_template_repo
        )
        self._day_template_rw_repo = day_template_repo

        calendar_entry_repo = cast(
            "CalendarEntryRepositoryReadWriteProtocol",
            CalendarEntryRepository(user_id=self.user_id),
        )
        self.calendar_entry_ro_repo = cast(
            "CalendarEntryRepositoryReadOnlyProtocol", calendar_entry_repo
        )
        self._calendar_entry_rw_repo = calendar_entry_repo

        push_subscription_repo = cast(
            "PushSubscriptionRepositoryReadWriteProtocol",
            PushSubscriptionRepository(user_id=self.user_id),
        )
        self.push_subscription_ro_repo = cast(
            "PushSubscriptionRepositoryReadOnlyProtocol", push_subscription_repo
        )
        self._push_subscription_rw_repo = push_subscription_repo

        routine_repo = cast(
            "RoutineRepositoryReadWriteProtocol",
            RoutineRepository(user_id=self.user_id),
        )
        self.routine_ro_repo = cast("RoutineRepositoryReadOnlyProtocol", routine_repo)
        self._routine_rw_repo = routine_repo

        task_definition_repo = cast(
            "TaskDefinitionRepositoryReadWriteProtocol",
            TaskDefinitionRepository(user_id=self.user_id),
        )
        self.task_definition_ro_repo = cast(
            "TaskDefinitionRepositoryReadOnlyProtocol", task_definition_repo
        )
        self._task_definition_rw_repo = task_definition_repo

        task_repo = cast(
            "TaskRepositoryReadWriteProtocol",
            TaskRepository(user_id=self.user_id),
        )
        self.task_ro_repo = cast("TaskRepositoryReadOnlyProtocol", task_repo)
        self._task_rw_repo = task_repo

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit the unit of work context.

        For nested transactions, do nothing (let outer transaction handle it).
        For top-level transactions, commit on success or rollback on exception.
        """
        if self._connection is None:
            return

        # If this is a nested transaction, don't commit/rollback
        if self._is_nested:
            return

        try:
            if exc_type is None:
                # Success - commit the transaction
                await self.commit()
            else:
                # Exception occurred - rollback the transaction
                await self.rollback()
        finally:
            # Reset the context variable
            if self._token is not None:
                reset_transaction_connection(self._token)
                self._token = None

            # Close the connection
            if self._connection is not None:
                await self._connection.close()
                self._connection = None

    def add(self, entity: BaseEntityObject) -> None:
        """Add an entity to be tracked for persistence.

        Only entities added via this method will be saved when commit() is called.
        The commit() method will inspect domain events on each added entity to
        determine whether to create, update, or delete it.

        Args:
            entity: The entity to track for persistence.
        """
        self._added_entities.append(entity)

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
        repo = self._get_read_only_repository_for_entity(entity)
        try:
            # Try to get the entity - if it exists, raise an error
            await repo.get(entity.id)
            raise BadRequestError(f"Entity with id {entity.id} already exists")
        except NotFoundError:
            # Entity doesn't exist, which is what we want for create
            pass

        # Mark as newly created and add to tracking
        entity.create()
        self.add(entity)

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
        repo = self._get_read_only_repository_for_entity(entity)
        # Verify entity exists - this will raise NotFoundError if it doesn't
        await repo.get(entity.id)

        # Mark for deletion and add to tracking
        entity.delete()
        self.add(entity)

    async def commit(self) -> None:
        """Commit the current transaction.

        This will:
        1. Process all added entities (create, update, delete based on domain events)
        2. Collect domain events from all aggregates
        3. Commit the database transaction
        4. Dispatch domain events (after successful commit)
        """
        if self._connection is None:
            raise RuntimeError("Cannot commit: not in a transaction context")

        if self._is_nested:
            # Nested transactions don't commit - outer transaction handles it
            return

        # Process all added entities based on their domain events
        await self._process_added_entities()

        # Collect domain events from all processed entities
        events = self._collect_domain_events_from_entities()

        # Commit the database transaction first
        await self._connection.commit()

        # Dispatch domain events after successful commit
        # This ensures events are only dispatched if the transaction succeeded
        await self._dispatch_domain_events(events)

    def _get_repository_for_entity(self, entity: BaseEntityObject) -> Any:
        """Get the appropriate read-write repository for an entity type.

        Args:
            entity: The entity to get a repository for.

        Returns:
            The read-write repository for the entity type.

        Raises:
            ValueError: If no repository is found for the entity type.
        """
        entity_type = type(entity)

        # Map entity types to their repositories
        if entity_type == DayEntity:
            return self._day_rw_repo
        elif entity_type == DayTemplateEntity:
            return self._day_template_rw_repo
        elif entity_type == CalendarEntryEntity:
            return self._calendar_entry_rw_repo
        elif entity_type == CalendarEntity:
            return self._calendar_rw_repo
        elif entity_type == TaskEntity:
            return self._task_rw_repo
        elif entity_type == RoutineEntity:
            return self._routine_rw_repo
        elif entity_type == data_objects.TaskDefinition:
            return self._task_definition_rw_repo
        elif entity_type == UserEntity:
            return self._user_rw_repo
        elif entity_type == data_objects.PushSubscription:
            return self._push_subscription_rw_repo
        elif entity_type == data_objects.AuthToken:
            return self._auth_token_rw_repo
        else:
            raise ValueError(f"No repository found for entity type {entity_type}")

    def _get_read_only_repository_for_entity(self, entity: BaseEntityObject) -> Any:
        """Get the appropriate read-only repository for an entity type.

        Args:
            entity: The entity to get a repository for.

        Returns:
            The read-only repository for the entity type.

        Raises:
            ValueError: If no repository is found for the entity type.
        """
        entity_type = type(entity)

        # Map entity types to their read-only repositories
        if entity_type == DayEntity:
            return self.day_ro_repo
        elif entity_type == DayTemplateEntity:
            return self.day_template_ro_repo
        elif entity_type == CalendarEntryEntity:
            return self.calendar_entry_ro_repo
        elif entity_type == CalendarEntity:
            return self.calendar_ro_repo
        elif entity_type == TaskEntity:
            return self.task_ro_repo
        elif entity_type == RoutineEntity:
            return self.routine_ro_repo
        elif entity_type == data_objects.TaskDefinition:
            return self.task_definition_ro_repo
        elif entity_type == UserEntity:
            return self.user_ro_repo
        elif entity_type == data_objects.PushSubscription:
            return self.push_subscription_ro_repo
        elif entity_type == data_objects.AuthToken:
            return self.auth_token_ro_repo
        else:
            raise ValueError(f"No repository found for entity type {entity_type}")

    async def _process_added_entities(self) -> None:
        """Process all added entities based on their domain events.

        For each entity:
        - If it has EntityDeletedEvent: delete it
        - If it has EntityCreatedEvent: insert it
        - If it has EntityUpdatedEvent or other events: update it

        Note: Events are not collected here - they remain on entities
        to be collected after processing.
        """
        for entity in self._added_entities:
            repo = self._get_repository_for_entity(entity)

            # Check events without collecting them (use has_events to peek)
            # We need to check what events exist to determine the operation
            # Since we can't peek at events without collecting, we'll collect
            # and then put them back temporarily
            events = entity.collect_events()
            if not events:
                continue

            # Check for EntityCreatedEvent, EntityDeletedEvent, EntityUpdatedEvent
            has_created_event = any(isinstance(e, EntityCreatedEvent) for e in events)
            has_deleted_event = any(isinstance(e, EntityDeletedEvent) for e in events)
            has_updated_event = any(isinstance(e, EntityUpdatedEvent) for e in events)

            # Put events back so they can be collected later for dispatching
            for event in events:
                entity._add_event(event)

            if has_deleted_event:
                # Delete the entity
                await repo.delete(entity)
            elif has_created_event:
                # Insert the entity (new entity)
                await repo.put(entity)
            else:
                # Update the entity (existing entity with changes)
                await repo.put(entity)

    def _collect_domain_events_from_entities(self) -> list[DomainEvent]:
        """Collect domain events from all added entities.

        This collects and clears events from entities after processing.
        The added entities list is cleared after collecting events.

        Returns:
            A list of all domain events collected from entities.
        """
        events: list[DomainEvent] = []

        for entity in self._added_entities:
            events.extend(entity.collect_events())

        # Clear the added entities list after processing
        self._added_entities.clear()

        return events

    async def _dispatch_domain_events(self, events: list[DomainEvent]) -> None:
        """Dispatch domain events after successful commit.

        Uses blinker signals to dispatch events to registered handlers.
        This enables event-driven workflows like:
        - Keeping service caches up to date
        - Sending notifications when tasks are completed
        - Triggering calendar syncs when events change
        - Audit logging

        Args:
            events: List of domain events to dispatch.
        """
        await send_domain_events(events)

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        if self._connection is None:
            raise RuntimeError("Cannot rollback: not in a transaction context")

        if self._is_nested:
            # Nested transactions don't rollback - outer transaction handles it
            return

        await self._connection.rollback()


class SqlAlchemyUnitOfWorkFactory:
    """Factory for creating SqlAlchemyUnitOfWork instances."""

    def create(self, user_id: UUID) -> UnitOfWorkProtocol:
        """Create a new UnitOfWork instance for the given user.

        Args:
            user_id: The UUID of the user to scope the unit of work to.

        Returns:
            A new UnitOfWork instance (not yet entered).
        """
        return SqlAlchemyUnitOfWork(user_id=user_id)


class SqlAlchemyReadOnlyRepositories:
    """SQLAlchemy implementation of ReadOnlyRepositories.

    Provides read-only access to repositories without write capabilities.
    Each repository manages its own database connections for read operations.
    """

    def __init__(self, user_id: UUID) -> None:
        """Initialize read-only repositories for a specific user.

        Args:
            user_id: The UUID of the user to scope repositories to.
        """
        self.user_id = user_id

        # Initialize all read-only repositories with user scoping (where applicable)
        # UserRepository and AuthTokenRepository are not user-scoped
        user_repo = cast("UserRepositoryReadOnlyProtocol", UserRepository())
        self.user_ro_repo = user_repo

        auth_token_repo = cast(
            "AuthTokenRepositoryReadOnlyProtocol", AuthTokenRepository()
        )
        self.auth_token_ro_repo = auth_token_repo

        # All other repositories are user-scoped
        calendar_repo = cast(
            "CalendarRepositoryReadOnlyProtocol",
            CalendarRepository(user_id=self.user_id),
        )
        self.calendar_ro_repo = calendar_repo

        day_repo = cast(
            "DayRepositoryReadOnlyProtocol", DayRepository(user_id=self.user_id)
        )
        self.day_ro_repo = day_repo

        day_template_repo = cast(
            "DayTemplateRepositoryReadOnlyProtocol",
            DayTemplateRepository(user_id=self.user_id),
        )
        self.day_template_ro_repo = day_template_repo

        calendar_entry_repo = cast(
            "CalendarEntryRepositoryReadOnlyProtocol",
            CalendarEntryRepository(user_id=self.user_id),
        )
        self.calendar_entry_ro_repo = calendar_entry_repo

        push_subscription_repo = cast(
            "PushSubscriptionRepositoryReadOnlyProtocol",
            PushSubscriptionRepository(user_id=self.user_id),
        )
        self.push_subscription_ro_repo = push_subscription_repo

        routine_repo = cast(
            "RoutineRepositoryReadOnlyProtocol",
            RoutineRepository(user_id=self.user_id),
        )
        self.routine_ro_repo = routine_repo

        task_definition_repo = cast(
            "TaskDefinitionRepositoryReadOnlyProtocol",
            TaskDefinitionRepository(user_id=self.user_id),
        )
        self.task_definition_ro_repo = task_definition_repo

        task_repo = cast(
            "TaskRepositoryReadOnlyProtocol", TaskRepository(user_id=self.user_id)
        )
        self.task_ro_repo = task_repo


class SqlAlchemyReadOnlyRepositoryFactory:
    """Factory for creating SqlAlchemyReadOnlyRepositories instances."""

    def create(self, user_id: UUID) -> ReadOnlyRepositories:
        """Create read-only repositories for the given user.

        Args:
            user_id: The UUID of the user to scope the repositories to.

        Returns:
            Read-only repositories scoped to the user.
        """
        return SqlAlchemyReadOnlyRepositories(user_id=user_id)
