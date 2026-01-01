"""Factory for creating DayService instances with proper context loading."""

import datetime
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain import entities as objects
from planned.domain.entities import User
from planned.domain.value_objects.day import DayContext

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
        user: User,
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
        """Create a DayService instance with loaded context for the given date.

        Args:
            date: The date for which to create the DayService
            user_id: Optional user ID (defaults to self.user.id if not provided)

        Returns:
            A DayService instance with fully loaded context
        """
        if user_id is None:
            user_id = self.user.id

        # Create a UoW to load context
        uow = self.uow_factory.create(user_id)
        async with uow:
            # Get template from user settings based on weekday
            template_slug = self.user.settings.template_defaults[date.weekday()]
            template = await uow.day_templates.get_by_slug(template_slug)

            # Create base day
            temp_day = objects.Day.create_for_date(
                date,
                user_id=user_id,
                template=template,
            )

            # Create temporary context and service for loading
            temp_day_ctx = DayContext(day=temp_day)
            temp_day_svc = DayService(
                user=self.user,
                day_ctx=temp_day_ctx,
                uow_factory=self.uow_factory,
            )

            # Load full context
            day_ctx = await temp_day_svc.load_context(
                date=date,
                user_id=user_id,
            )

        # Create and return final DayService with loaded context
        return DayService(
            user=self.user,
            day_ctx=day_ctx,
            uow_factory=self.uow_factory,
        )

