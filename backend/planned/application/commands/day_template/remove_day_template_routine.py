"""Command to detach a routine from a day template."""

from uuid import UUID

from planned.application.commands.base import BaseCommandHandler
from planned.domain.entities.day_template import DayTemplateEntity


class RemoveDayTemplateRoutineHandler(BaseCommandHandler):
    """Detach a routine from a day template."""

    async def run(
        self, day_template_id: UUID, routine_id: UUID
    ) -> DayTemplateEntity:
        """Remove an attached routine from the day template.

        Args:
            day_template_id: ID of the day template.
            routine_id: ID of the routine to detach.

        Returns:
            The updated day template entity.
        """
        async with self.new_uow() as uow:
            day_template = await uow.day_template_ro_repo.get(day_template_id)
            updated_day_template = day_template.remove_routine(routine_id)
            uow.add(updated_day_template)
            return updated_day_template

