"""Command to record an action on a task."""

from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import AuditLogEntity, DayEntity, TaskEntity


class RecordTaskActionHandler(BaseCommandHandler):
    """Records an action on a task."""

    async def record_task_action(
        self, task_id: UUID, action: value_objects.Action
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
        async with self.new_uow() as uow:
            # Get the task to find its scheduled_date
            task = await uow.task_ro_repo.get(task_id)

            # Get the Day aggregate root using the task's scheduled_date
            day_id = DayEntity.id_from_date_and_user(task.scheduled_date, self.user_id)
            day_was_created = False
            try:
                day = await uow.day_ro_repo.get(day_id)
            except NotFoundError:
                # Day doesn't exist yet - this shouldn't happen if task exists
                # but we'll create it to maintain consistency
                user = await uow.user_ro_repo.get(self.user_id)
                template_slug = user.settings.template_defaults[
                    task.scheduled_date.weekday()
                ]
                template = await uow.day_template_ro_repo.search_one(
                    value_objects.DayTemplateQuery(slug=template_slug)
                )
                day = DayEntity.create_for_date(
                    task.scheduled_date,
                    user_id=self.user_id,
                    template=template,
                )
                await uow.create(day)
                day_was_created = True

            # Use Day aggregate root method to record action
            # This ensures proper aggregate boundaries and domain event handling
            # The method mutates the task in place and returns the updated task
            updated_task = day.record_task_action(task, action)

            # Create audit log entry for significant actions
            if action.type == value_objects.ActionType.COMPLETE:
                audit_log = AuditLogEntity(
                    user_id=self.user_id,
                    activity_type=value_objects.ActivityType.TASK_COMPLETED,
                    entity_id=task_id,
                    entity_type="task",
                    meta={"action_created_at": action.created_at.isoformat()},
                )
                await uow.create(audit_log)
            elif action.type == value_objects.ActionType.PUNT:
                audit_log = AuditLogEntity(
                    user_id=self.user_id,
                    activity_type=value_objects.ActivityType.TASK_PUNTED,
                    entity_id=task_id,
                    entity_type="task",
                    meta={"action_created_at": action.created_at.isoformat()},
                )
                await uow.create(audit_log)

            # Add both Day (for events) and Task (for state changes) to UoW
            # Only add day if we didn't create it (create() already adds it)
            if not day_was_created:
                uow.add(day)
            uow.add(updated_task)

            return updated_task
