"""Event handler for task-related domain events."""

from typing import TYPE_CHECKING
from uuid import UUID

from loguru import logger

from planned.application.services.event_handler import EventHandler
from planned.application.unit_of_work import UnitOfWorkFactory
from planned.core.constants import DEFAULT_END_OF_DAY_TIME
from planned.core.exceptions import NotFoundError
from planned.domain import entities as objects
from planned.domain.events.base import DomainEvent
from planned.domain.events.task_events import (
    TaskActionRecordedEvent,
    TaskCompletedEvent,
    TaskStatusChangedEvent,
)

if TYPE_CHECKING:
    from ..service import DayService


class TaskEventHandler(EventHandler["DayService"]):
    """Handles task-related domain events for DayService.

    Keeps the DayContext's task list synchronized with task changes.
    """

    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
    ) -> None:
        """Initialize the task event handler.

        Args:
            uow_factory: Factory for creating UnitOfWork instances
            user_id: The user ID for database operations
        """
        super().__init__()
        self._uow_factory = uow_factory
        self._user_id = user_id

    @property
    def day_ctx(self) -> objects.DayContext:
        """Get the DayContext from the parent service."""
        return self.service.day_ctx

    def can_handle(self, event: DomainEvent) -> bool:
        """Check if this handler can handle the given event."""
        return isinstance(
            event,
            TaskStatusChangedEvent | TaskCompletedEvent | TaskActionRecordedEvent,
        )

    async def handle(self, event: DomainEvent) -> None:
        """Handle a task domain event."""
        if isinstance(event, TaskStatusChangedEvent | TaskCompletedEvent):
            await self._handle_status_change(event)
        elif isinstance(event, TaskActionRecordedEvent):
            await self._handle_action_recorded(event)

    async def _handle_status_change(
        self,
        event: TaskStatusChangedEvent | TaskCompletedEvent,
    ) -> None:
        """Handle task status change by reloading the task from the database.

        Args:
            event: The task status change event
        """
        task_id = event.task_id

        # Check if this task is in our context
        task_in_ctx = next((t for t in self.day_ctx.tasks if t.id == task_id), None)
        if task_in_ctx is None:
            # Task not in our day's context, ignore
            return

        # Reload the task from database to get updated state
        uow = self._uow_factory.create(self._user_id)
        async with uow:
            try:
                updated_task = await uow.tasks.get(task_id)
                self._update_task_in_context(updated_task)
                logger.debug(f"Updated task {task_id} in DayService cache")
            except NotFoundError:
                # Task was deleted, remove from context
                self._remove_task_from_context(task_id)
                logger.debug(f"Removed deleted task {task_id} from DayService cache")

    async def _handle_action_recorded(
        self,
        event: TaskActionRecordedEvent,
    ) -> None:
        """Handle task action recorded by reloading the task.

        Args:
            event: The task action recorded event
        """
        task_id = event.task_id

        # Check if this task is in our context
        task_in_ctx = next((t for t in self.day_ctx.tasks if t.id == task_id), None)
        if task_in_ctx is None:
            return

        # Reload the task from database
        uow = self._uow_factory.create(self._user_id)
        async with uow:
            try:
                updated_task = await uow.tasks.get(task_id)
                self._update_task_in_context(updated_task)
                logger.debug(f"Updated task {task_id} after action in DayService cache")
            except NotFoundError:
                self._remove_task_from_context(task_id)

    def _update_task_in_context(self, updated_task: objects.Task) -> None:
        """Update a task in the context, maintaining sort order.

        Args:
            updated_task: The updated task to put in the context
        """
        # Remove old version and add updated one
        self.day_ctx.tasks = [t for t in self.day_ctx.tasks if t.id != updated_task.id]
        self.day_ctx.tasks.append(updated_task)
        # Re-sort by start time
        self.day_ctx.tasks.sort(
            key=lambda x: x.schedule.start_time
            if x.schedule and x.schedule.start_time
            else DEFAULT_END_OF_DAY_TIME,
        )

    def _remove_task_from_context(self, task_id: UUID) -> None:
        """Remove a task from the context.

        Args:
            task_id: The ID of the task to remove
        """
        self.day_ctx.tasks = [t for t in self.day_ctx.tasks if t.id != task_id]
