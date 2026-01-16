"""Command to add a goal to a day."""

from datetime import date

from lykke.application.commands.base import BaseCommandHandler
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity


class AddGoalToDayHandler(BaseCommandHandler):
    """Adds a goal to a day."""

    async def add_goal(self, date: date, name: str) -> DayEntity:
        """Add a goal to a day.

        Args:
            date: The date of the day to add the goal to
            name: The name of the goal to add

        Returns:
            The updated Day entity

        Raises:
            NotFoundError: If the day doesn't exist
        """
        async with self.new_uow() as uow:
            # Get the existing day
            day_id = DayEntity.id_from_date_and_user(date, self.user_id)
            try:
                day = await uow.day_ro_repo.get(day_id)
            except NotFoundError:
                # Create a new day if it doesn't exist
                user = await uow.user_ro_repo.get(self.user_id)
                template_slug = user.settings.template_defaults[date.weekday()]
                template = await uow.day_template_ro_repo.search_one(
                    value_objects.DayTemplateQuery(slug=template_slug)
                )
                day = DayEntity.create_for_date(
                    date, user_id=self.user_id, template=template
                )
                await uow.create(day)

            # Add the goal (this emits a domain event)
            day.add_goal(name)

            # Add entity to UoW for saving
            uow.add(day)
            return day
