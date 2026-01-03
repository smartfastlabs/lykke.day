from dataclasses import dataclass, field
from datetime import UTC
from datetime import date as dt_date
from datetime import datetime
from uuid import UUID

from planned.core.exceptions import DomainError

from .. import value_objects
from .action import ActionEntity
from .base import BaseDateObject
from .task_definition import TaskDefinitionEntity


@dataclass(kw_only=True)
class TaskEntity(BaseDateObject):
    user_id: UUID
    scheduled_date: dt_date
    name: str
    status: value_objects.TaskStatus
    task_definition: TaskDefinitionEntity
    category: value_objects.TaskCategory
    frequency: value_objects.TaskFrequency
    completed_at: datetime | None = None
    schedule: value_objects.TaskSchedule | None = None
    routine_id: UUID | None = None
    tags: list[value_objects.TaskTag] = field(default_factory=list)
    actions: list[ActionEntity] = field(default_factory=list)

    def _get_date(self) -> dt_date:
        return self.scheduled_date

    def _get_datetime(self) -> datetime:
        """Get datetime for this task (not used since _get_date is implemented)."""
        # This is required by BaseDateObject but not used since _get_date is implemented
        return datetime.combine(self.scheduled_date, datetime.min.time())

    def record_action(self, action: ActionEntity) -> value_objects.TaskStatus:
        """Record an action on this task.

        This method handles action recording and status transitions based on
        the action type. It enforces business rules about which actions are
        valid in which states.

        Note: This method should be called through the Day aggregate root,
        which will raise domain events on behalf of the aggregate.

        Args:
            action: The action to record

        Returns:
            The old status before the change (for event raising by aggregate root)

        Raises:
            DomainError: If the action is invalid for the current state
        """
        # Add the action
        self.actions.append(action)

        # Handle status transitions based on action type
        old_status = self.status
        if action.type == value_objects.ActionType.COMPLETE:
            if self.status == value_objects.TaskStatus.COMPLETE:
                raise DomainError("Task is already complete")
            self.status = value_objects.TaskStatus.COMPLETE
            self.completed_at = datetime.now(UTC)
        elif action.type == value_objects.ActionType.PUNT:
            if self.status == value_objects.TaskStatus.PUNT:
                raise DomainError("Task is already punted")
            self.status = value_objects.TaskStatus.PUNT
        elif action.type == value_objects.ActionType.NOTIFY:
            # Notification doesn't change status, just records the action
            pass
        else:
            # Other action types don't change status
            pass

        # Return the old status so the aggregate root can raise events if needed
        return old_status

    def mark_pending(self) -> value_objects.TaskStatus:
        """Mark the task as pending (ready to be worked on).

        This is typically called when a task's scheduled time arrives.

        Returns:
            The old status before the change
        """
        if self.status == value_objects.TaskStatus.PENDING:
            return self.status  # Already pending

        old_status = self.status
        self.status = value_objects.TaskStatus.PENDING
        return old_status

    def mark_ready(self) -> value_objects.TaskStatus:
        """Mark the task as ready (available to be worked on).

        This is typically called when a task becomes available based on
        its schedule or dependencies.

        Returns:
            The old status before the change
        """
        if self.status == value_objects.TaskStatus.READY:
            return self.status  # Already ready

        old_status = self.status
        self.status = value_objects.TaskStatus.READY
        return old_status
