from datetime import UTC, date as dt_date, datetime
from uuid import UUID

from pydantic import Field

from planned.core.exceptions import DomainError

from ..events.base import BaseAggregateRoot
from ..events.task_events import (
    TaskActionRecordedEvent,
    TaskCompletedEvent,
    TaskStatusChangedEvent,
)
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


class Task(BaseDateObject, BaseAggregateRoot):
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

    def record_action(self, action: Action) -> None:
        """Record an action on this task.

        This method handles action recording and status transitions based on
        the action type. It enforces business rules about which actions are
        valid in which states.

        Args:
            action: The action to record

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
            self._add_event(
                TaskCompletedEvent(
                    task_id=self.id,
                    completed_at=self.completed_at.isoformat(),
                )
            )
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

        # Record status change event if status changed
        if old_status != self.status:
            self._add_event(
                TaskStatusChangedEvent(
                    task_id=self.id,
                    old_status=old_status.value,
                    new_status=self.status.value,
                )
            )

        # Record action event
        self._add_event(
            TaskActionRecordedEvent(
                task_id=self.id,
                action_type=action.type.value,
            )
        )

    def mark_pending(self) -> None:
        """Mark the task as pending (ready to be worked on).

        This is typically called when a task's scheduled time arrives.
        """
        if self.status == TaskStatus.PENDING:
            return  # Already pending

        old_status = self.status
        self.status = TaskStatus.PENDING

        if old_status != self.status:
            self._add_event(
                TaskStatusChangedEvent(
                    task_id=self.id,
                    old_status=old_status.value,
                    new_status=self.status.value,
                )
            )

    def mark_ready(self) -> None:
        """Mark the task as ready (available to be worked on).

        This is typically called when a task becomes available based on
        its schedule or dependencies.
        """
        if self.status == TaskStatus.READY:
            return  # Already ready

        old_status = self.status
        self.status = TaskStatus.READY

        if old_status != self.status:
            self._add_event(
                TaskStatusChangedEvent(
                    task_id=self.id,
                    old_status=old_status.value,
                    new_status=self.status.value,
                )
            )
