"""Command to record an action on a task."""

from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, TaskEntity


class RecordTaskActionHandler(BaseCommandHandler):
    """Records an action on a task."""

    async def record_task_action(
        self, task_id: UUID, action: value_objects.Action
    ) -> TaskEntity:
        """Record an action on a task through the Day aggregate root.

        Args:
            task_id: The task ID
            action: The action to record

        Returns:
            The updated Task entity

        Raises:
            NotFoundError: If the task or day is not found
        """
        async with self.new_uow() as uow:
            # Get the task to find its scheduled_date
            task = await uow.task_ro_repo.get(task_id)

            # Get the Day aggregate root using the task's scheduled_date
            day_id = DayEntity.id_from_date_and_user(task.scheduled_date, self.user_id)
            day = await uow.day_ro_repo.get(day_id)

            # Use Day aggregate root method to record action
            # This ensures proper aggregate boundaries and domain event handling
            # The method mutates the task in place and returns the updated task
            # Audit logs are automatically created by the UOW for audited events
            updated_task = day.record_task_action(task, action)

            # Add both Day (for events) and Task (for state changes) to UoW
            uow.add(day)
            uow.add(updated_task)

            return updated_task
