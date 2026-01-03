"""Command to save a day to the database."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import DayEntity


class SaveDayHandler:
    """Saves a day to the database."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def save_day(self, user_id: UUID, day: DayEntity) -> DayEntity:
        """Save a day to the database.

        Args:
            user_id: The user ID
            day: The day entity to save

        Returns:
            The saved Day entity
        """
        async with self._uow_factory.create(user_id) as uow:
            await uow.days.put(day)
            await uow.commit()
            return day

