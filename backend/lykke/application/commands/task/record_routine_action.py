"""Command to record an action on all tasks in a routine for today."""

from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler
from lykke.core.exceptions import NotFoundError
from lykke.core.utils.dates import get_current_date
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, TaskEntity


class RecordRoutineActionHandler(BaseCommandHandler):
    """Records an action on all tasks in a routine for today."""

    async def record_routine_action(
        self, routine_id: UUID, action: value_objects.Action
    ) -> list[TaskEntity]:
        """Record an action on all tasks in a routine for today.

        Args:
            routine_id: The routine ID
            action: The action to record (COMPLETE or PUNT)

        Returns:
            List of updated Task entities

        Raises:
            NotFoundError: If the day is not found
        """
        date = get_current_date()
        async with self.new_uow() as uow:
            # Get the Day aggregate root
            day_id = DayEntity.id_from_date_and_user(date, self.user_id)
            day_was_created = False
            try:
                day = await uow.day_ro_repo.get(day_id)
            except NotFoundError:
                # Day doesn't exist yet - create it to maintain consistency
                user = await uow.user_ro_repo.get(self.user_id)
                template_slug = user.settings.template_defaults[date.weekday()]
                template = await uow.day_template_ro_repo.search_one(
                    value_objects.DayTemplateQuery(slug=template_slug)
                )
                day = DayEntity.create_for_date(
                    date,
                    user_id=self.user_id,
                    template=template,
                )
                await uow.create(day)
                day_was_created = True

            # Find all tasks for this routine on today's date
            tasks = await uow.task_ro_repo.search(
                value_objects.TaskQuery(
                    date=date,
                    routine_ids=[routine_id],
                )
            )

            # Record the action on each task
            updated_tasks: list[TaskEntity] = []
            for task in tasks:
                updated_task = day.record_task_action(task, action)
                updated_tasks.append(updated_task)

            # Add both Day (for events) and Tasks (for state changes) to UoW
            # Only add day if we didn't create it (create() already adds it)
            if not day_was_created:
                uow.add(day)
            for task in updated_tasks:
                uow.add(task)

            return updated_tasks
