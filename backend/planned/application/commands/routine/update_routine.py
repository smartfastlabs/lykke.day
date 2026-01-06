"""Command to update an existing routine."""

from dataclasses import asdict
from uuid import UUID

from planned.application.commands.base import BaseCommandHandler
from planned.domain.value_objects import RoutineUpdateObject
from planned.domain.entities import RoutineEntity


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
            routine = await uow.routine_ro_repo.get(routine_id)

            update_dict = {k: v for k, v in asdict(update_data).items() if v is not None}
            updated_routine = routine.clone(**update_dict)

            uow.add(updated_routine)
            return updated_routine


