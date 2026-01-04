"""Command to save a day to the database."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import DayEntity


class SaveDayHandler:
    """Saves a day to the database."""

    def __init__(self, uow_factory: UnitOfWorkFactory, user_id: UUID) -> None:
        self._uow_factory = uow_factory
        self.user_id = user_id

    async def save_day(self, day: DayEntity) -> DayEntity:
        """Save a day to the database.

        Args:
            day: The day entity to save

        Returns:
            The saved Day entity
        """
        async with self._uow_factory.create(self.user_id) as uow:
            await uow.day_rw_repo.put(day)
            await uow.commit()
            return day

