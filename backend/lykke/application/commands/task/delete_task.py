"""Command to delete a task."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.core.exceptions import NotFoundError
from lykke.domain.entities import TaskEntity


@dataclass(frozen=True)
class DeleteTaskCommand(Command):
    """Command to delete a task."""

    task_id: UUID


class DeleteTaskHandler(BaseCommandHandler[DeleteTaskCommand, None]):
    """Deletes a task."""

    async def handle(self, command: DeleteTaskCommand) -> None:
        """Delete a task.

        Args:
            command: The command containing the task ID to delete
        """
        async with self.new_uow() as uow:
            task = await uow.task_ro_repo.get(command.task_id)
            if task.user_id != self.user.id:
                raise NotFoundError(f"Task {command.task_id} not found")
            await uow.delete(task)
