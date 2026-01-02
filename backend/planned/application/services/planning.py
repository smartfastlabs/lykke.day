"""PlanningService for planning and scheduling days.

This service acts as a facade that delegates to command and query handlers.
It maintains backward compatibility while the codebase transitions to CQRS.
"""

import datetime
from uuid import UUID

from planned.application.commands.schedule_day import ScheduleDayCommand, ScheduleDayHandler
from planned.application.commands.unschedule_day import UnscheduleDayCommand, UnscheduleDayHandler
from planned.application.queries.preview_day import PreviewDayHandler, PreviewDayQuery
from planned.application.queries.preview_tasks import PreviewTasksHandler, PreviewTasksQuery
from planned.application.services.base import BaseService
from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain import entities, value_objects


class PlanningService(BaseService):
    """Service for planning and scheduling days.

    This service acts as a facade that delegates to command and query handlers.
    """

    user_id: UUID
    uow_factory: UnitOfWorkFactory
    _preview_tasks_handler: PreviewTasksHandler
    _preview_day_handler: PreviewDayHandler
    _schedule_day_handler: ScheduleDayHandler
    _unschedule_day_handler: UnscheduleDayHandler

    def __init__(
        self,
        user: entities.User,
        uow_factory: UnitOfWorkFactory,
    ) -> None:
        """Initialize PlanningService.

        Args:
            user: The user for whom to plan
            uow_factory: Factory for creating UnitOfWork instances
        """
        super().__init__(user)
        self.user_id = user.id
        self.uow_factory = uow_factory
        self._preview_tasks_handler = PreviewTasksHandler(uow_factory)
        self._preview_day_handler = PreviewDayHandler(uow_factory)
        self._schedule_day_handler = ScheduleDayHandler(uow_factory)
        self._unschedule_day_handler = UnscheduleDayHandler(uow_factory)

    async def preview_tasks(self, date: datetime.date) -> list[entities.Task]:
        """Preview tasks that would be created for a given date.

        Args:
            date: The date to preview tasks for

        Returns:
            List of tasks that would be created
        """
        query = PreviewTasksQuery(user_id=self.user_id, date=date)
        return await self._preview_tasks_handler.handle(query)

    async def preview(
        self,
        date: datetime.date,
        template_id: UUID | None = None,
    ) -> value_objects.DayContext:
        """Preview what a day would look like if scheduled.

        Args:
            date: The date to preview
            template_id: Optional template ID to use (otherwise uses defaults)

        Returns:
            A DayContext with preview data (not saved)
        """
        query = PreviewDayQuery(
            user_id=self.user_id,
            date=date,
            template_id=template_id,
        )
        return await self._preview_day_handler.handle(query)

    async def unschedule(self, date: datetime.date) -> None:
        """Unschedule a day, removing routine tasks and marking day as unscheduled.

        Args:
            date: The date to unschedule
        """
        cmd = UnscheduleDayCommand(user_id=self.user_id, date=date)
        await self._unschedule_day_handler.handle(cmd)

    async def schedule(
        self,
        date: datetime.date,
        template_id: UUID | None = None,
    ) -> value_objects.DayContext:
        """Schedule a day with tasks from routines.

        Args:
            date: The date to schedule
            template_id: Optional template ID to use (otherwise uses defaults)

        Returns:
            A DayContext with the scheduled day and tasks
        """
        cmd = ScheduleDayCommand(
            user_id=self.user_id,
            date=date,
            template_id=template_id,
        )
        return await self._schedule_day_handler.handle(cmd)

