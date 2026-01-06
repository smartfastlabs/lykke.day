"""Command to update an existing routine."""

from uuid import UUID

from planned.application.commands.base import BaseCommandHandler
from planned.domain.entities import RoutineEntity
from planned.domain.events.routine import RoutineUpdatedEvent
from planned.domain.value_objects import RoutineUpdateObject


class UpdateRoutineHandler(BaseCommandHandler):
    """Updates an existing routine."""

    async def run(
        self,
        routine_id: UUID,
        update_data: RoutineUpdateObject,
    ) -> RoutineEntity:
        """Update an existing routine.

        Args:
            routine_id: The ID of the routine to update.
            update_data: The update data containing optional fields.

        Returns:
            The updated routine entity.
        """
        async with self.new_uow() as uow:
            # Get the existing routine
            routine = await uow.routine_ro_repo.get(routine_id)

            # Apply updates using domain method (adds RoutineUpdatedEvent)
            routine = routine.apply_update(update_data, RoutineUpdatedEvent)

            # Add entity to UoW for saving
            uow.add(routine)
            return routine
