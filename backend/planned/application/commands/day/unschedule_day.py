"""Command to unschedule a day, removing routine tasks."""

from datetime import date

from planned.application.commands.base import BaseCommandHandler
from planned.core.exceptions import NotFoundError
from planned.domain import value_objects
from planned.domain.entities import DayEntity


class UnscheduleDayHandler(BaseCommandHandler):
    """Unschedules a day, removing routine tasks."""

    async def unschedule_day(self, date: date) -> DayEntity:
        """Unschedule a day, removing routine tasks and marking day as unscheduled.

        Args:
            date: The date to unschedule

        Returns:
            The updated Day entity
        """
        async with self.new_uow() as uow:
            # Get all tasks for the date, filter for routine tasks, then delete them
            tasks = await uow.task_ro_repo.search_query(value_objects.DateQuery(date=date))
            routine_tasks = [t for t in tasks if t.routine_id is not None]
            for task in routine_tasks:
                await uow.delete(task)

            # Get or create the day
            day_id = DayEntity.id_from_date_and_user(date, self.user_id)
            day_was_created = False
            try:
                day = await uow.day_ro_repo.get(day_id)
            except NotFoundError:
                # Day doesn't exist, create it
                user = await uow.user_ro_repo.get(self.user_id)
                template_slug = user.settings.template_defaults[date.weekday()]
                template = await uow.day_template_ro_repo.get_by_slug(template_slug)
                day = DayEntity.create_for_date(
                    date, user_id=self.user_id, template=template
                )
                await uow.create(day)
                day_was_created = True

            # Unschedule the day using domain method
            day.unschedule()
            # Only add if we didn't create it (create() already adds it)
            if not day_was_created:
                uow.add(day)
            return day

