from dataclasses import dataclass, field
from datetime import UTC, date as dt_date, datetime
from uuid import UUID

from lykke.core.exceptions import DomainError
from lykke.domain import data_objects, value_objects
from lykke.domain.events.task_events import TaskStateUpdatedEvent

from .base import BaseEntityObject


@dataclass(kw_only=True)
class TaskEntity(BaseEntityObject):
    user_id: UUID
    scheduled_date: dt_date
    name: str
    status: value_objects.TaskStatus
    task_definition: data_objects.TaskDefinition
    category: value_objects.TaskCategory
    frequency: value_objects.TaskFrequency
    completed_at: datetime | None = None
    schedule: value_objects.TaskSchedule | None = None
    routine_id: UUID | None = None
    tags: list[value_objects.TaskTag] = field(default_factory=list)
    actions: list[value_objects.Action] = field(default_factory=list)

    def record_action(self, action: value_objects.Action) -> value_objects.TaskStatus:
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

        # Record a task-level event so persistence is tied to a domain event
        self._add_event(
            TaskStateUpdatedEvent(
                task_id=self.id,
                action_type=action.type.value,
                old_status=old_status.value,
                new_status=self.status.value,
                completed_at=self.completed_at.isoformat()
                if self.completed_at
                else None,
            )
        )

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
