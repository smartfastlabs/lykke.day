"""Command to create a new routine."""

from planned.application.commands.base import BaseCommandHandler
from planned.domain.entities import RoutineEntity


class CreateRoutineHandler(BaseCommandHandler):
    """Creates a new routine."""

    async def run(self, routine: RoutineEntity) -> RoutineEntity:
        """Create a new routine.

        Args:
            routine: The routine entity to create.

        Returns:
            The created routine entity.
        """
        async with self.new_uow() as uow:
            await uow.create(routine)
            return routine


