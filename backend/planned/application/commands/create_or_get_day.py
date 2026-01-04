"""Command to get an existing day or create a new one."""

from datetime import date
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.core.exceptions import NotFoundError
from planned.domain.entities import DayEntity


class CreateOrGetDayHandler:
    """Gets an existing day or creates a new one."""

    def __init__(self, uow_factory: UnitOfWorkFactory, user_id: UUID) -> None:
        self._uow_factory = uow_factory
        self.user_id = user_id

    async def create_or_get_day(self, date: date) -> DayEntity:
        """Get an existing day or create a new one.

        Args:
            date: The date

        Returns:
            An existing Day if found, otherwise a newly created and saved Day
        """
        async with self._uow_factory.create(self.user_id) as uow:
            day_id = DayEntity.id_from_date_and_user(date, self.user_id)
            try:
                return await uow.day_rw_repo.get(day_id)
            except NotFoundError:
                # Day doesn't exist, create it
                user = await uow.user_rw_repo.get(self.user_id)
                template_slug = user.settings.template_defaults[date.weekday()]
                template = await uow.day_template_rw_repo.get_by_slug(template_slug)
                day = DayEntity.create_for_date(
                    date,
                    user_id=self.user_id,
                    template=template,
                )
                result = await uow.day_rw_repo.put(day)
                await uow.commit()
                return result

