"""Factory for creating DayService instances with proper context loading."""

import datetime
from uuid import UUID

from planned.application.repositories import (
    DayRepositoryProtocol,
    DayTemplateRepositoryProtocol,
    EventRepositoryProtocol,
    MessageRepositoryProtocol,
    TaskRepositoryProtocol,
    UserRepositoryProtocol,
)
from planned.domain import entities as objects
from planned.domain.entities import User
from planned.domain.value_objects.day import DayContext

from ..day import DayService


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
        day_repo: DayRepositoryProtocol,
        day_template_repo: DayTemplateRepositoryProtocol,
        event_repo: EventRepositoryProtocol,
        message_repo: MessageRepositoryProtocol,
        task_repo: TaskRepositoryProtocol,
        user_repo: UserRepositoryProtocol,
    ) -> None:
        """Initialize the factory with required dependencies.

        Args:
            user: The user for whom to create DayService instances
            day_repo: Repository for day entities
            day_template_repo: Repository for day templates
            event_repo: Repository for event entities
            message_repo: Repository for message entities
            task_repo: Repository for task entities
            user_repo: Repository for user entities (needed for context loading)
        """
        self.user = user
        self.day_repo = day_repo
        self.day_template_repo = day_template_repo
        self.event_repo = event_repo
        self.message_repo = message_repo
        self.task_repo = task_repo
        self.user_repo = user_repo

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

        # Get template from user settings based on weekday
        template_slug = self.user.settings.template_defaults[date.weekday()]
        template = await self.day_template_repo.get_by_slug(template_slug)

        # Create base day
        temp_day = await DayService.base_day(
            date,
            user_id=user_id,
            template=template,
        )

        # Create temporary context and service for loading
        temp_ctx = DayContext(day=temp_day)
        temp_day_svc = DayService(
            user=self.user,
            ctx=temp_ctx,
            day_repo=self.day_repo,
            day_template_repo=self.day_template_repo,
            event_repo=self.event_repo,
            message_repo=self.message_repo,
            task_repo=self.task_repo,
        )

        # Load full context
        ctx = await temp_day_svc.load_context(
            date=date,
            user_id=user_id,
            user_repo=self.user_repo,
        )

        # Create and return final DayService with loaded context
        return DayService(
            user=self.user,
            ctx=ctx,
            day_repo=self.day_repo,
            day_template_repo=self.day_template_repo,
            event_repo=self.event_repo,
            message_repo=self.message_repo,
            task_repo=self.task_repo,
        )

