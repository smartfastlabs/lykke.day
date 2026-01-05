"""Command to get an existing day or create a new one."""

from datetime import date

from planned.application.commands.base import BaseCommandHandler
from planned.core.exceptions import NotFoundError
from planned.domain.entities import DayEntity


class CreateOrGetDayHandler(BaseCommandHandler):
    """Gets an existing day or creates a new one."""

    async def create_or_get_day(self, date: date) -> DayEntity:
        """Get an existing day or create a new one.

        Args:
            date: The date

        Returns:
            An existing Day if found, otherwise a newly created and saved Day
        """
        async with self.new_uow() as uow:
            day_id = DayEntity.id_from_date_and_user(date, self.user_id)
            try:
                return await uow.day_ro_repo.get(day_id)
            except NotFoundError:
                # Day doesn't exist, create it
                user = await uow.user_ro_repo.get(self.user_id)
                template_slug = user.settings.template_defaults[date.weekday()]
                template = await uow.day_template_ro_repo.get_by_slug(template_slug)
                day = DayEntity.create_for_date(
                    date,
                    user_id=self.user_id,
                    template=template,
                )
                await uow.create(day)
                return day

