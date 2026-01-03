"""Infrastructure implementation of Unit of Work pattern using SQLAlchemy."""

from __future__ import annotations

from contextvars import Token
from typing import TYPE_CHECKING, cast
from uuid import UUID

from planned.application.events import send_domain_events
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
    CalendarEntryRepository,
    CalendarRepository,
    DayRepository,
    DayTemplateRepository,
    MessageRepository,
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

    Manages a single database transaction and provides access to all repositories
    scoped to that transaction. All repositories share the same connection.
    """

    # Read-only repository type annotations
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

    # Read-write repository type annotations
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
        # Use cast to satisfy type checker - concrete repos implement both protocols
        # We assign the same instance to both ro and rw since they implement both
        user_repo = cast("UserRepositoryReadWriteProtocol", UserRepository())
        self.user_ro_repo = cast("UserRepositoryReadOnlyProtocol", user_repo)
        self.user_rw_repo = user_repo

        auth_token_repo = cast(
            "AuthTokenRepositoryReadWriteProtocol", AuthTokenRepository()
        )
        self.auth_token_ro_repo = cast(
            "AuthTokenRepositoryReadOnlyProtocol", auth_token_repo
        )
        self.auth_token_rw_repo = auth_token_repo

        # All other repositories are user-scoped
        calendar_repo = cast(
            "CalendarRepositoryReadWriteProtocol",
            CalendarRepository(user_id=self.user_id),
        )
        self.calendar_ro_repo = cast(
            "CalendarRepositoryReadOnlyProtocol", calendar_repo
        )
        self.calendar_rw_repo = calendar_repo

        day_repo = cast(
            "DayRepositoryReadWriteProtocol", DayRepository(user_id=self.user_id)
        )
        self.day_ro_repo = cast("DayRepositoryReadOnlyProtocol", day_repo)
        self.day_rw_repo = day_repo

        day_template_repo = cast(
            "DayTemplateRepositoryReadWriteProtocol",
            DayTemplateRepository(user_id=self.user_id),
        )
        self.day_template_ro_repo = cast(
            "DayTemplateRepositoryReadOnlyProtocol", day_template_repo
        )
        self.day_template_rw_repo = day_template_repo

        calendar_entry_repo = cast(
            "CalendarEntryRepositoryReadWriteProtocol",
            CalendarEntryRepository(user_id=self.user_id),
        )
        self.calendar_entry_ro_repo = cast(
            "CalendarEntryRepositoryReadOnlyProtocol", calendar_entry_repo
        )
        self.calendar_entry_rw_repo = calendar_entry_repo

        message_repo = cast(
            "MessageRepositoryReadWriteProtocol",
            MessageRepository(user_id=self.user_id),
        )
        self.message_ro_repo = cast("MessageRepositoryReadOnlyProtocol", message_repo)
        self.message_rw_repo = message_repo

        push_subscription_repo = cast(
            "PushSubscriptionRepositoryReadWriteProtocol",
            PushSubscriptionRepository(user_id=self.user_id),
        )
        self.push_subscription_ro_repo = cast(
            "PushSubscriptionRepositoryReadOnlyProtocol", push_subscription_repo
        )
        self.push_subscription_rw_repo = push_subscription_repo

        routine_repo = cast(
            "RoutineRepositoryReadWriteProtocol",
            RoutineRepository(user_id=self.user_id),
        )
        self.routine_ro_repo = cast("RoutineRepositoryReadOnlyProtocol", routine_repo)
        self.routine_rw_repo = routine_repo

        task_definition_repo = cast(
            "TaskDefinitionRepositoryReadWriteProtocol",
            TaskDefinitionRepository(user_id=self.user_id),
        )
        self.task_definition_ro_repo = cast(
            "TaskDefinitionRepositoryReadOnlyProtocol", task_definition_repo
        )
        self.task_definition_rw_repo = task_definition_repo

        task_repo = cast(
            "TaskRepositoryReadWriteProtocol",
            TaskRepository(user_id=self.user_id),
        )
        self.task_ro_repo = cast("TaskRepositoryReadOnlyProtocol", task_repo)
        self.task_rw_repo = task_repo

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
        # Use read-write repos since they're the ones that handle writes
        repositories = [
            self.day_rw_repo,
            self.day_template_rw_repo,
            self.calendar_entry_rw_repo,
            self.message_rw_repo,
            self.task_rw_repo,
            self.routine_rw_repo,
            self.calendar_rw_repo,
            self.user_rw_repo,
            self.auth_token_rw_repo,
            self.task_definition_rw_repo,
            self.push_subscription_rw_repo,
        ]

        for repo in repositories:
            # All our concrete repositories have collect_domain_events method
            if hasattr(repo, "collect_domain_events"):
                events.extend(repo.collect_domain_events())

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
