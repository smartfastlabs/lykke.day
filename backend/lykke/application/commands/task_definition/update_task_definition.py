"""Command to update an existing task definition."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.repositories import TaskDefinitionRepositoryReadOnlyProtocol
from lykke.domain.entities import TaskDefinitionEntity
from lykke.domain.events.task_events import TaskDefinitionUpdatedEvent
from lykke.domain.value_objects import TaskDefinitionUpdateObject


@dataclass(frozen=True)
class UpdateTaskDefinitionCommand(Command):
    """Command to update an existing task definition."""

    task_definition_id: UUID
    update_data: TaskDefinitionUpdateObject


class UpdateTaskDefinitionHandler(
    BaseCommandHandler[UpdateTaskDefinitionCommand, TaskDefinitionEntity]
):
    """Updates an existing task definition."""

    task_definition_ro_repo: TaskDefinitionRepositoryReadOnlyProtocol

    async def handle(
        self, command: UpdateTaskDefinitionCommand
    ) -> TaskDefinitionEntity:
        """Update an existing task definition.

        Args:
            command: The command containing the task definition ID and update data

        Returns:
            The updated task definition entity

        Raises:
            NotFoundError: If task definition not found
        """
        async with self.new_uow() as uow:
            # Get the existing task definition
            task_definition = await self.task_definition_ro_repo.get(
                command.task_definition_id
            )

            # Apply updates using domain method (adds EntityUpdatedEvent)
            task_definition = task_definition.apply_update(
                command.update_data, TaskDefinitionUpdatedEvent
            )

            # Add entity to UoW for saving
            return uow.add(task_definition)
