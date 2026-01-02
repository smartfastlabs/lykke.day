"""Command to record an action on a task."""

from dataclasses import dataclass
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import Action, Task

from .base import Command, CommandHandler


@dataclass(frozen=True)
class RecordTaskActionCommand(Command):
    """Command to record an action on a task.

    The task's record_action method enforces business rules
    and emits domain events.
    """

    user_id: UUID
    task_id: UUID
    action: Action


class RecordTaskActionHandler(CommandHandler[RecordTaskActionCommand, Task]):
    """Handles RecordTaskActionCommand."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def handle(self, cmd: RecordTaskActionCommand) -> Task:
        """Record an action on a task.

        Args:
            cmd: The command containing task_id and action

        Returns:
            The updated Task entity
        """
        async with self._uow_factory.create(cmd.user_id) as uow:
            # Get the task
            task = await uow.tasks.get(cmd.task_id)

            # Use domain method to record action (enforces business rules, emits events)
            task.record_action(cmd.action)

            # Save and commit
            await uow.tasks.put(task)
            await uow.commit()

            return task

