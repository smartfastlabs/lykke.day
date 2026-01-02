"""Query to get the complete context for a day."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from planned.application.utils.day_context_loader import DayContextLoader
from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain import entities, value_objects

from .base import Query, QueryHandler


@dataclass(frozen=True)
class GetDayContextQuery(Query):
    """Query to get the complete context for a specific day.

    Returns a DayContext with day, tasks, calendar entries, and messages.
    If the day doesn't exist, returns a preview (unsaved) day.
    """

    user: entities.User
    date: date


class GetDayContextHandler(QueryHandler[GetDayContextQuery, value_objects.DayContext]):
    """Handles GetDayContextQuery."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def handle(self, query: GetDayContextQuery) -> value_objects.DayContext:
        """Load complete day context for the given date.

        Args:
            query: The query containing user and date

        Returns:
            A DayContext with all related data
        """
        async with self._uow_factory.create(query.user.id) as uow:
            loader = DayContextLoader(
                user=query.user,
                day_repo=uow.days,
                day_template_repo=uow.day_templates,
                calendar_entry_repo=uow.calendar_entries,
                message_repo=uow.messages,
                task_repo=uow.tasks,
            )
            return await loader.load(query.date, query.user.id)

