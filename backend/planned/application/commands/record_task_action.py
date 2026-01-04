"""Command to record an action on a task."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.core.exceptions import NotFoundError
from planned.domain.entities import ActionEntity, DayEntity, TaskEntity


class RecordTaskActionHandler:
    """Records an action on a task."""

    def __init__(self, uow_factory: UnitOfWorkFactory, user_id: UUID) -> None:
        self._uow_factory = uow_factory
        self.user_id = user_id

    async def record_task_action(
        self, task_id: UUID, action: ActionEntity
    ) -> TaskEntity:
        """Record an action on a task through the Day aggregate root.

        Args:
            task_id: The task ID
            action: The action to record

        Returns:
            The updated Task entity

        Raises:
            NotFoundError: If the task or day is not found
        """
        async with self._uow_factory.create(self.user_id) as uow:
            # Get the task to find its scheduled_date
            task = await uow.task_rw_repo.get(task_id)

            # Get the Day aggregate root using the task's scheduled_date
            day_id = DayEntity.id_from_date_and_user(task.scheduled_date, self.user_id)
            try:
                day = await uow.day_rw_repo.get(day_id)
            except NotFoundError:
                # Day doesn't exist yet - this shouldn't happen if task exists
                # but we'll create it to maintain consistency
                user = await uow.user_rw_repo.get(self.user_id)
                template_slug = user.settings.template_defaults[
                    task.scheduled_date.weekday()
                ]
                template = await uow.day_template_rw_repo.get_by_slug(template_slug)
                day = DayEntity.create_for_date(
                    task.scheduled_date,
                    user_id=self.user_id,
                    template=template,
                )

            # Use Day aggregate root method to record action
            # This ensures proper aggregate boundaries and domain event handling
            # The method mutates the task in place and returns the updated task
            updated_task = day.record_task_action(task, action)

            # Save both Day (for events) and Task (for state changes)
            await uow.day_rw_repo.put(day)
            await uow.task_rw_repo.put(updated_task)
            await uow.commit()

            return updated_task
