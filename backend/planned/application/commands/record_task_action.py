"""Command to record an action on a task."""

from dataclasses import dataclass
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.core.exceptions import NotFoundError
from planned.domain.entities import ActionEntity, DayEntity, TaskEntity

from .base import Command, CommandHandler


@dataclass(frozen=True)
class RecordTaskActionCommand(Command):
    """Command to record an action on a task.

    This command works through the Day aggregate root to ensure
    proper aggregate boundaries and domain event handling.
    """

    user_id: UUID
    task_id: UUID
    action: ActionEntity


class RecordTaskActionHandler(CommandHandler[RecordTaskActionCommand, TaskEntity]):
    """Handles RecordTaskActionCommand."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def handle(self, cmd: RecordTaskActionCommand) -> TaskEntity:
        """Record an action on a task through the Day aggregate root.

        Args:
            cmd: The command containing task_id and action

        Returns:
            The updated Task entity

        Raises:
            NotFoundError: If the task or day is not found
        """
        async with self._uow_factory.create(cmd.user_id) as uow:
            # Get the task to find its scheduled_date
            task = await uow.tasks.get(cmd.task_id)

            # Get the Day aggregate root using the task's scheduled_date
            day_id = DayEntity.id_from_date_and_user(
                task.scheduled_date, cmd.user_id
            )
            try:
                day = await uow.days.get(day_id)
            except NotFoundError:
                # Day doesn't exist yet - this shouldn't happen if task exists
                # but we'll create it to maintain consistency
                user = await uow.users.get(cmd.user_id)
                template_slug = user.settings.template_defaults[
                    task.scheduled_date.weekday()
                ]
                template = await uow.day_templates.get_by_slug(template_slug)
                day = DayEntity.create_for_date(
                    task.scheduled_date,
                    user_id=cmd.user_id,
                    template=template,
                )

            # Use Day aggregate root method to record action
            # This ensures proper aggregate boundaries and domain event handling
            # The method mutates the task in place and returns the updated task
            updated_task = day.record_task_action(task, cmd.action)

            # Save both Day (for events) and Task (for state changes)
            await uow.days.put(day)
            await uow.tasks.put(updated_task)
            await uow.commit()

            return updated_task
