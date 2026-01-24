"""Command to update an existing routine definition."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities import RoutineDefinitionEntity
from lykke.domain.events.routine_definition import RoutineDefinitionUpdatedEvent
from lykke.domain.value_objects import RoutineDefinitionUpdateObject


@dataclass(frozen=True)
class UpdateRoutineDefinitionCommand(Command):
    """Command to update an existing routine definition."""

    routine_definition_id: UUID
    update_data: RoutineDefinitionUpdateObject


class UpdateRoutineDefinitionHandler(
    BaseCommandHandler[UpdateRoutineDefinitionCommand, RoutineDefinitionEntity]
):
    """Updates an existing routine definition."""

    async def handle(
        self, command: UpdateRoutineDefinitionCommand
    ) -> RoutineDefinitionEntity:
        """Update an existing routine definition.

        Args:
            command: The command containing the routine definition ID and update data.

        Returns:
            The updated routine definition entity.
        """
        async with self.new_uow() as uow:
            # Get the existing routine definition
            routine_definition = await uow.routine_definition_ro_repo.get(
                command.routine_definition_id
            )

            # Apply updates using domain method (adds RoutineDefinitionUpdatedEvent)
            routine_definition = routine_definition.apply_update(
                command.update_data, RoutineDefinitionUpdatedEvent
            )

            # Add entity to UoW for saving
            return uow.add(routine_definition)
