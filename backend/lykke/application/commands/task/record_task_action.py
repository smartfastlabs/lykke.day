"""Command to record an action on a task."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.repositories import (
    DayRepositoryReadOnlyProtocol,
    TaskRepositoryReadOnlyProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, TaskEntity


@dataclass(frozen=True)
class RecordTaskActionCommand(Command):
    """Command to record an action on a task."""

    task_id: UUID
    action: value_objects.Action


class RecordTaskActionHandler(BaseCommandHandler[RecordTaskActionCommand, TaskEntity]):
    """Records an action on a task."""

    task_ro_repo: TaskRepositoryReadOnlyProtocol
    day_ro_repo: DayRepositoryReadOnlyProtocol

    async def handle(self, command: RecordTaskActionCommand) -> TaskEntity:
        """Record an action on a task through the Day aggregate root.

        Args:
            command: The command containing the task ID and action to record

        Returns:
            The updated Task entity

        Raises:
            NotFoundError: If the task or day is not found
        """
        async with self.new_uow() as uow:
            # Get the task to find its scheduled_date
            task = await self.task_ro_repo.get(command.task_id)

            # Get the Day aggregate root using the task's scheduled_date
            day_id = DayEntity.id_from_date_and_user(task.scheduled_date, self.user.id)
            day = await self.day_ro_repo.get(day_id)

            # Use Day aggregate root method to record action
            # This ensures proper aggregate boundaries and domain event handling
            # The method mutates the task in place and returns the updated task
            # Audit logs are automatically created by the UOW for audited events
            updated_task = day.record_task_action(task, command.action)

            # Add Day for events; add Task only if it emitted domain events
            uow.add(day)
            if updated_task.has_events():
                uow.add(updated_task)

            return updated_task
