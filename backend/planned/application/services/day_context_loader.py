"""Helper class for loading DayContext with all related data."""

import asyncio
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
from planned.core.constants import DEFAULT_END_OF_DAY_TIME
from planned.core.exceptions import exceptions
from planned.domain import entities as objects
from planned.domain.value_objects.query import DateQuery


class DayContextLoader:
    """Loads DayContext with tasks, events, messages, and day data.

    Encapsulates the logic for loading a complete day context, handling
    both existing days and creating preview days when needed.
    """

    def __init__(
        self,
        user: objects.User,
        day_repo: DayRepositoryProtocol,
        day_template_repo: DayTemplateRepositoryProtocol,
        event_repo: EventRepositoryProtocol,
        message_repo: MessageRepositoryProtocol,
        task_repo: TaskRepositoryProtocol,
    ) -> None:
        """Initialize the loader with required repositories.

        Args:
            user: The user for whom to load context
            day_repo: Repository for day entities
            day_template_repo: Repository for day templates
            event_repo: Repository for event entities
            message_repo: Repository for message entities
            task_repo: Repository for task entities
        """
        self.user = user
        self.day_repo = day_repo
        self.day_template_repo = day_template_repo
        self.event_repo = event_repo
        self.message_repo = message_repo
        self.task_repo = task_repo

    async def load(
        self,
        date: datetime.date,
        user_id: UUID,
    ) -> objects.DayContext:
        """Load complete day context for the given date and user.

        Args:
            date: The date to load context for
            user_id: The user ID for the context

        Returns:
            A DayContext with day, tasks, events, and messages loaded and sorted
        """
        tasks: list[objects.Task] = []
        events: list[objects.Event] = []
        messages: list[objects.Message] = []
        day: objects.Day

        try:
            # Try to load existing day and all related data
            day_id = objects.Day.id_from_date_and_user(date, user_id)
            tasks, events, messages, day = await asyncio.gather(
                self.task_repo.search_query(DateQuery(date=date)),
                self.event_repo.search_query(DateQuery(date=date)),
                self.message_repo.search_query(DateQuery(date=date)),
                self.day_repo.get(day_id),
            )
        except exceptions.NotFoundError:
            # Day doesn't exist, create a preview day using default template
            day = await self._create_preview_day(date, user_id)

        return self._build_context(day, tasks, events, messages)

    async def _create_preview_day(
        self,
        date: datetime.date,
        user_id: UUID,
    ) -> objects.Day:
        """Create a preview day when no existing day is found.

        Args:
            date: The date for the preview day
            user_id: The user ID for the preview day

        Returns:
            A Day entity (not saved to database)
        """
        template_slug = self.user.settings.template_defaults[date.weekday()]
        template = await self.day_template_repo.get_by_slug(template_slug)
        return self._base_day(date, user_id, template)

    @staticmethod
    def _base_day(
        date: datetime.date,
        user_id: UUID,
        template: objects.DayTemplate,
    ) -> objects.Day:
        """Create a base day entity.

        Args:
            date: The date for the day
            user_id: The user ID for the day
            template: The template to use for the day

        Returns:
            A Day entity with default status
        """
        return objects.Day.create_for_date(
            date,
            user_id=user_id,
            template=template,
        )

    def _build_context(
        self,
        day: objects.Day,
        tasks: list[objects.Task],
        events: list[objects.Event],
        messages: list[objects.Message],
    ) -> objects.DayContext:
        """Build a DayContext from loaded data.

        Args:
            day: The day entity
            tasks: List of tasks for the day
            events: List of events for the day
            messages: List of messages for the day

        Returns:
            A DayContext with sorted tasks and events
        """
        return objects.DayContext(
            day=day,
            tasks=sorted(
                tasks,
                key=lambda x: x.schedule.start_time
                if x.schedule and x.schedule.start_time
                else DEFAULT_END_OF_DAY_TIME,
            ),
            events=sorted(events, key=lambda e: e.starts_at),
            messages=messages,
        )

