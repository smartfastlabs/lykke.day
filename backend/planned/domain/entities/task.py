from datetime import UTC
from datetime import date as dt_date
from datetime import datetime
from uuid import UUID

from planned.core.exceptions import DomainError
from pydantic import Field

from ..value_objects.action import ActionType
from ..value_objects.task import (
    TaskCategory,
    TaskFrequency,
    TaskSchedule,
    TaskStatus,
    TaskTag,
)
from .action import Action
from .base import BaseDateObject
from .task_definition import TaskDefinition


class Task(BaseDateObject):
    user_id: UUID
    scheduled_date: dt_date
    name: str
    status: TaskStatus
    task_definition: TaskDefinition
    category: TaskCategory
    frequency: TaskFrequency
    completed_at: datetime | None = None
    schedule: TaskSchedule | None = None
    routine_id: UUID | None = None
    tags: list[TaskTag] = Field(default_factory=list)
    actions: list[Action] = Field(default_factory=list)

    def _get_date(self) -> dt_date:
        return self.scheduled_date

    def _get_datetime(self) -> datetime:
        """Get datetime for this task (not used since _get_date is implemented)."""
        # This is required by BaseDateObject but not used since _get_date is implemented
        return datetime.combine(self.scheduled_date, datetime.min.time())

    def record_action(self, action: Action) -> TaskStatus:
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
        if action.type == ActionType.COMPLETE:
            if self.status == TaskStatus.COMPLETE:
                raise DomainError("Task is already complete")
            self.status = TaskStatus.COMPLETE
            self.completed_at = datetime.now(UTC)
        elif action.type == ActionType.PUNT:
            if self.status == TaskStatus.PUNT:
                raise DomainError("Task is already punted")
            self.status = TaskStatus.PUNT
        elif action.type == ActionType.NOTIFY:
            # Notification doesn't change status, just records the action
            pass
        else:
            # Other action types don't change status
            pass

        # Return the old status so the aggregate root can raise events if needed
        return old_status

    def mark_pending(self) -> TaskStatus:
        """Mark the task as pending (ready to be worked on).

        This is typically called when a task's scheduled time arrives.

        Returns:
            The old status before the change
        """
        if self.status == TaskStatus.PENDING:
            return self.status  # Already pending

        old_status = self.status
        self.status = TaskStatus.PENDING
        return old_status

    def mark_ready(self) -> TaskStatus:
        """Mark the task as ready (available to be worked on).

        This is typically called when a task becomes available based on
        its schedule or dependencies.

        Returns:
            The old status before the change
        """
        if self.status == TaskStatus.READY:
            return self.status  # Already ready

        old_status = self.status
        self.status = TaskStatus.READY
        return old_status
