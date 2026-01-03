"""Factory for creating DayService instances with proper context loading."""

import datetime
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain import value_objects
from planned.domain.entities import UserEntity

from .service import DayService


class DayServiceFactory:
    """Factory for creating DayService instances with loaded context.

    Encapsulates the common pattern of:
    1. Getting template from user settings
    2. Creating base day
    3. Loading full context
    4. Creating final DayService instance
    """

    def __init__(
        self,
        user: UserEntity,
        uow_factory: UnitOfWorkFactory,
    ) -> None:
        """Initialize the factory with required dependencies.

        Args:
            user: The user for whom to create DayService instances
            uow_factory: Factory for creating UnitOfWork instances
        """
        self.user = user
        self.uow_factory = uow_factory

    async def create(
        self,
        date: datetime.date,
        user_id: UUID | None = None,
    ) -> DayService:
        """Create a stateless DayService instance for the given date.

        Args:
            date: The date for which to create the DayService
            user_id: Optional user ID (defaults to self.user.id if not provided)

        Returns:
            A stateless DayService instance
        """
        # Create and return stateless DayService
        return DayService(
            user=self.user,
            date=date,
            uow_factory=self.uow_factory,
        )

