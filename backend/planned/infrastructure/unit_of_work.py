"""Infrastructure implementation of Unit of Work pattern using SQLAlchemy."""

from __future__ import annotations

from contextvars import Token
from typing import TYPE_CHECKING, cast
from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncConnection

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
from planned.application.unit_of_work import UnitOfWorkProtocol
from planned.domain.events.base import DomainEvent
from planned.infrastructure.database import get_engine
from planned.infrastructure.database.transaction import (
    get_transaction_connection,
    reset_transaction_connection,
    set_transaction_connection,
)
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
    UserRepository,
)

if TYPE_CHECKING:
    from typing import Self


class SqlAlchemyUnitOfWork:
    """SQLAlchemy implementation of UnitOfWorkProtocol.

    Manages a single database transaction and provides access to all repositories
    scoped to that transaction. All repositories share the same connection.
    """

    # Repository type annotations for protocol compatibility
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

    def __init__(self, user_id: UUID) -> None:
        """Initialize the unit of work for a specific user.

        Args:
            user_id: The UUID of the user to scope repositories to.
        """
        self.user_id = user_id
        self._connection: AsyncConnection | None = None
        self._token: Token[AsyncConnection | None] | None = None
        self._is_nested = False

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
        # Use cast to satisfy type checker - concrete repos implement protocols
        self.users = cast("UserRepositoryProtocol", UserRepository())
        self.auth_tokens = cast("AuthTokenRepositoryProtocol", AuthTokenRepository())

        # All other repositories are user-scoped
        self.calendars = cast(
            "CalendarRepositoryProtocol", CalendarRepository(user_id=self.user_id)
        )
        self.days = cast("DayRepositoryProtocol", DayRepository(user_id=self.user_id))
        self.day_templates = cast(
            "DayTemplateRepositoryProtocol", DayTemplateRepository(user_id=self.user_id)
        )
        self.events = cast(
            "EventRepositoryProtocol", EventRepository(user_id=self.user_id)
        )
        self.messages = cast(
            "MessageRepositoryProtocol", MessageRepository(user_id=self.user_id)
        )
        self.push_subscriptions = cast(
            "PushSubscriptionRepositoryProtocol",
            PushSubscriptionRepository(user_id=self.user_id),
        )
        self.routines = cast(
            "RoutineRepositoryProtocol", RoutineRepository(user_id=self.user_id)
        )
        self.task_definitions = cast(
            "TaskDefinitionRepositoryProtocol",
            TaskDefinitionRepository(user_id=self.user_id),
        )
        self.tasks = cast(
            "TaskRepositoryProtocol", TaskRepository(user_id=self.user_id)
        )

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

    async def commit(self) -> None:
        """Commit the current transaction.

        This will:
        1. Collect domain events from all aggregates that were modified
        2. Commit the database transaction
        3. Dispatch domain events (after successful commit)
        """
        if self._connection is None:
            raise RuntimeError("Cannot commit: not in a transaction context")

        if self._is_nested:
            # Nested transactions don't commit - outer transaction handles it
            return

        # Collect domain events from all aggregates
        # We need to check all repositories for aggregates that have events
        # For now, we'll collect from repositories that were accessed
        # A more sophisticated implementation would track which aggregates were modified
        events = await self._collect_domain_events()

        # Commit the database transaction first
        await self._connection.commit()

        # Dispatch domain events after successful commit
        # This ensures events are only dispatched if the transaction succeeded
        await self._dispatch_domain_events(events)

    async def _collect_domain_events(self) -> list[DomainEvent]:
        """Collect domain events from all aggregates in this unit of work.

        Iterates through all repositories and collects domain events from
        aggregates that were saved during this transaction.

        Returns:
            A list of all domain events collected from aggregates.
        """
        events: list[DomainEvent] = []

        # Collect events from all repositories that track aggregates
        # Each repository tracks aggregates saved via put() that had pending events
        repositories = [
            self.days,
            self.day_templates,
            self.events,
            self.messages,
            self.tasks,
            self.routines,
            self.calendars,
            self.users,
            self.auth_tokens,
            self.task_definitions,
            self.push_subscriptions,
        ]

        for repo in repositories:
            # All our concrete repositories have collect_domain_events method
            if hasattr(repo, "collect_domain_events"):
                events.extend(repo.collect_domain_events())

        return events

    async def _dispatch_domain_events(self, events: list[DomainEvent]) -> None:
        """Dispatch domain events after successful commit.

        Currently logs events for debugging. This can be enhanced with a proper
        event bus/dispatcher to enable event-driven workflows like:
        - Sending notifications when tasks are completed
        - Triggering calendar syncs when events change
        - Audit logging

        Args:
            events: List of domain events to dispatch.
        """
        if not events:
            return

        logger.debug(f"Dispatching {len(events)} domain events")
        for event in events:
            logger.debug(
                f"Domain event: {event.__class__.__name__} at {event.occurred_at}"
            )
            # Future: dispatch to event handlers via an event bus
            # await self._event_bus.publish(event)

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
