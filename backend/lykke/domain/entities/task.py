from dataclasses import dataclass, field
from datetime import UTC, date as dt_date, datetime, time
from uuid import UUID

from lykke.core.exceptions import DomainError
from lykke.core.utils.dates import ensure_utc
from lykke.domain import value_objects
from lykke.domain.events.task_events import (
    TaskCreatedEvent,
    TaskStateUpdatedEvent,
    TaskUpdatedEvent,
)
from lykke.domain.value_objects.update import TaskUpdateObject

from .base import BaseEntityObject


@dataclass(kw_only=True)
class TaskEntity(BaseEntityObject):
    user_id: UUID
    scheduled_date: dt_date
    name: str
    status: value_objects.TaskStatus
    type: value_objects.TaskType
    description: str | None = None
    category: value_objects.TaskCategory
    frequency: value_objects.TaskFrequency
    completed_at: datetime | None = None
    snoozed_until: datetime | None = None
    time_window: value_objects.TimeWindow | None = None
    routine_definition_id: UUID | None = None
    tags: list[value_objects.TaskTag] = field(default_factory=list)
    actions: list[value_objects.Action] = field(default_factory=list)

    def create(self) -> "TaskEntity":
        """Mark this task as created and emit a user-facing event."""
        super().create()
        self._add_event(
            TaskCreatedEvent(
                user_id=self.user_id,
                task_id=self.id,
                name=self.name,
                entity_id=self.id,
                entity_type="task",
                entity_date=self.scheduled_date,
            )
        )
        return self

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
        old_status = self.status
        if (
            action.type == value_objects.ActionType.PUNT
            and self.status == value_objects.TaskStatus.PUNT
        ):
            return old_status

        self.actions.append(action)

        if action.type == value_objects.ActionType.COMPLETE:
            self.status = value_objects.TaskStatus.COMPLETE
            self.completed_at = datetime.now(UTC)
            self.snoozed_until = None
        elif action.type == value_objects.ActionType.PUNT:
            self.status = value_objects.TaskStatus.PUNT
            self.completed_at = None
            self.snoozed_until = None
        elif action.type == value_objects.ActionType.SNOOZE:
            snoozed_until = ensure_utc(action.data.get("snoozed_until"))
            if snoozed_until is None:
                raise DomainError("Snooze action requires snoozed_until")
            self.status = value_objects.TaskStatus.SNOOZE
            self.snoozed_until = snoozed_until
            self.completed_at = None
        elif action.type == value_objects.ActionType.NOTIFY:
            pass
        else:
            pass

        self._add_event(
            TaskStateUpdatedEvent(
                user_id=self.user_id,
                task_id=self.id,
                action_type=action.type.value,
                old_status=old_status.value,
                new_status=self.status.value,
                completed_at=self.completed_at,
                entity_id=self.id,
                entity_type="task",
                entity_date=self.scheduled_date,
            )
        )

        return old_status

    def reschedule(self, scheduled_date: dt_date) -> "TaskEntity":
        """Reschedule this task to a new date via an update event."""
        update = TaskUpdateObject(scheduled_date=scheduled_date)
        return self.apply_update(update, TaskUpdatedEvent)

    def mark_pending(self) -> value_objects.TaskStatus:
        """Mark the task as pending (ready to be worked on).

        This is typically called when a task's scheduled time arrives.

        Returns:
            The old status before the change
        """
        if self.status == value_objects.TaskStatus.PENDING:
            return self.status

        old_status = self.status
        self.status = value_objects.TaskStatus.PENDING
        self.completed_at = None
        self.snoozed_until = None
        return old_status

    def mark_ready(self) -> value_objects.TaskStatus:
        """Mark the task as ready (available to be worked on).

        This is typically called when a task becomes available based on
        its schedule or dependencies.

        Returns:
            The old status before the change
        """
        if self.status == value_objects.TaskStatus.READY:
            return self.status

        old_status = self.status
        self.status = value_objects.TaskStatus.READY
        self.completed_at = None
        self.snoozed_until = None
        return old_status

    def is_eligible_for_upcoming(
        self,
        now: time,
        cutoff_time: time,
    ) -> bool:
        """Check if this task is eligible to be included in upcoming tasks.

        Args:
            now: Current time
            cutoff_time: The cutoff time for the look-ahead window

        Returns:
            True if the task should be included, False otherwise
        """
        if self.status not in (
            value_objects.TaskStatus.PENDING,
            value_objects.TaskStatus.NOT_STARTED,
            value_objects.TaskStatus.READY,
        ):
            return False

        if self.completed_at:
            return False

        if not self.time_window:
            return False

        if self.time_window.available_time:
            if self.time_window.available_time > now:
                return False

        elif self.time_window.start_time and cutoff_time < self.time_window.start_time:
            return False

        return not (self.time_window.end_time and now > self.time_window.end_time)
