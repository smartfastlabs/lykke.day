"""In-memory UnitOfWork implementation for testing."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkProtocol
from tests.fixtures.repositories import (
    InMemoryAuthTokenRepository,
    InMemoryCalendarEntryRepository,
    InMemoryCalendarRepository,
    InMemoryDayRepository,
    InMemoryDayTemplateRepository,
    InMemoryMessageRepository,
    InMemoryPushSubscriptionRepository,
    InMemoryRoutineRepository,
    InMemoryTaskDefinitionRepository,
    InMemoryTaskRepository,
    InMemoryUserRepository,
)


class InMemoryUnitOfWork:
    """In-memory implementation of UnitOfWorkProtocol for testing.

    This implementation stores all data in memory and doesn't require
    a database connection. Useful for fast unit tests.
    """

    def __init__(self, user_id: UUID) -> None:
        """Initialize the in-memory unit of work.

        Args:
            user_id: The UUID of the user to scope repositories to.
        """
        self.user_id = user_id
        self.committed = False
        self.rolled_back = False

        # Initialize all repositories
        self.auth_tokens = InMemoryAuthTokenRepository()
        self.calendar_entries = InMemoryCalendarEntryRepository()
        self.calendars = InMemoryCalendarRepository()
        self.days = InMemoryDayRepository()
        self.day_templates = InMemoryDayTemplateRepository()
        self.messages = InMemoryMessageRepository()
        self.push_subscriptions = InMemoryPushSubscriptionRepository()
        self.routines = InMemoryRoutineRepository()
        self.task_definitions = InMemoryTaskDefinitionRepository()
        self.tasks = InMemoryTaskRepository()
        self.users = InMemoryUserRepository()

    async def __aenter__(self) -> "InMemoryUnitOfWork":
        """Enter the unit of work context."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the unit of work context."""
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()

    async def commit(self) -> None:
        """Commit the transaction (no-op for in-memory)."""
        self.committed = True
        self.rolled_back = False

    async def rollback(self) -> None:
        """Rollback the transaction (no-op for in-memory)."""
        self.rolled_back = True
        self.committed = False


class InMemoryUnitOfWorkFactory:
    """Factory for creating InMemoryUnitOfWork instances."""

    def create(self, user_id: UUID) -> InMemoryUnitOfWork:
        """Create a new InMemoryUnitOfWork instance.

        Args:
            user_id: The UUID of the user to scope the unit of work to.

        Returns:
            A new InMemoryUnitOfWork instance.
        """
        return InMemoryUnitOfWork(user_id=user_id)

