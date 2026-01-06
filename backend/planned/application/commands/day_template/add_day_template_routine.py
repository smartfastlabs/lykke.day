"""Command to attach a routine to a day template."""

from uuid import UUID

from planned.application.commands.base import BaseCommandHandler
from planned.domain.entities.day_template import DayTemplateEntity


class AddDayTemplateRoutineHandler(BaseCommandHandler):
    """Attach a routine to a day template."""

    async def run(self, day_template_id: UUID, routine_id: UUID) -> DayTemplateEntity:
        """Attach a routine to the day template.

        Args:
            day_template_id: ID of the day template to update.
            routine_id: ID of the routine to attach.

        Returns:
            The updated day template entity.
        """
        async with self.new_uow() as uow:
            day_template = await uow.day_template_ro_repo.get(day_template_id)
            updated = day_template.add_routine(routine_id)
            uow.add(updated)
            return updated

