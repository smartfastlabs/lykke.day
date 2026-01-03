import uuid
from dataclasses import dataclass, field
from datetime import UTC
from datetime import date as dt_date
from datetime import datetime
from uuid import UUID

from planned.core.exceptions import DomainError

from .. import value_objects
from ..events.base import BaseAggregateRoot
from ..events.day_events import (
    DayCompletedEvent,
    DayScheduledEvent,
    DayUnscheduledEvent,
)
from ..events.task_events import (
    TaskActionRecordedEvent,
    TaskCompletedEvent,
    TaskStatusChangedEvent,
)
from .action import ActionEntity
from .day_template import DayTemplateEntity
from .task import TaskEntity


@dataclass(kw_only=True)
class DayEntity(BaseAggregateRoot):
    user_id: UUID
    date: dt_date
    alarm: value_objects.Alarm | None = None
    status: value_objects.DayStatus = value_objects.DayStatus.UNSCHEDULED
    scheduled_at: datetime | None = None
    tags: list[value_objects.DayTag] = field(default_factory=list)
    template: DayTemplateEntity | None = None
    id: UUID = field(default=None, init=True)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Generate deterministic UUID5 based on date and user_id.

        This ensures that Days with the same date and user_id always have
        the same ID, making lookups stable and deterministic.
        Only generates if id was not explicitly provided.
        """
        # Check if id needs to be generated (mypy doesn't understand field override)
        current_id = object.__getattribute__(self, "id")
        if current_id is None:
            generated_id = self.id_from_date_and_user(self.date, self.user_id)
            object.__setattr__(self, "id", generated_id)
        # After this point, self.id is guaranteed to be a UUID

    @classmethod
    def id_from_date_and_user(cls, date: dt_date, user_id: UUID) -> UUID:
        """Generate deterministic UUID5 from date and user_id.

        This can be used to generate the ID for looking up a Day by date
        without creating a Day instance.
        """
        namespace = uuid.uuid5(uuid.NAMESPACE_DNS, "planned.day")
        name = f"{user_id}:{date.isoformat()}"
        return uuid.uuid5(namespace, name)

    @classmethod
    def create_for_date(
        cls,
        date: dt_date,
        user_id: UUID,
        template: "DayTemplateEntity",
    ) -> "DayEntity":
        """Create a new day for the given date and user.

        Factory method for creating days. This is the preferred way to create
        Day instances as it ensures proper initialization.

        Args:
            date: The date for the day
            user_id: The user ID for the day
            template: The template to use for the day

        Returns:
            A new Day instance with UNSCHEDULED status
        """
        return cls(
            user_id=user_id,
            date=date,
            status=value_objects.DayStatus.UNSCHEDULED,
            template=template,
            alarm=template.alarm,
        )

    def schedule(self, template: "DayTemplateEntity") -> None:
        """Schedule the day with the given template.

        This method enforces the business rule that only unscheduled days
        can be scheduled.

        Args:
            template: The template to use for scheduling

        Raises:
            DomainError: If the day is not in UNSCHEDULED status
        """
        if self.status != value_objects.DayStatus.UNSCHEDULED:
            raise DomainError(
                f"Cannot schedule day in {self.status.value} status. "
                "Only unscheduled days can be scheduled."
            )

        self.template = template
        self.alarm = template.alarm
        self.status = value_objects.DayStatus.SCHEDULED
        self.scheduled_at = datetime.now(UTC)
        self._add_event(
            DayScheduledEvent(
                day_id=self.id,
                date=self.date,
                template_id=template.id if template else None,
            )
        )

    def unschedule(self) -> None:
        """Unschedule the day.

        This method enforces the business rule that only scheduled days
        can be unscheduled.

        Raises:
            DomainError: If the day is not in SCHEDULED status
        """
        if self.status != value_objects.DayStatus.SCHEDULED:
            raise DomainError(
                f"Cannot unschedule day in {self.status.value} status. "
                "Only scheduled days can be unscheduled."
            )

        self.status = value_objects.DayStatus.UNSCHEDULED
        self.scheduled_at = None
        self._add_event(DayUnscheduledEvent(day_id=self.id, date=self.date))

    def complete(self) -> None:
        """Mark the day as complete.

        This method enforces the business rule that only scheduled days
        can be completed.

        Raises:
            DomainError: If the day is not in SCHEDULED status
        """
        if self.status != value_objects.DayStatus.SCHEDULED:
            raise DomainError(
                f"Cannot complete day in {self.status.value} status. "
                "Only scheduled days can be completed."
            )

        self.status = value_objects.DayStatus.COMPLETE
        self._add_event(DayCompletedEvent(day_id=self.id, date=self.date))

    def update_template(self, template: "DayTemplateEntity") -> None:
        """Update the day's template.

        Args:
            template: The new template to use
        """
        self.template = template
        # Update alarm if template has one
        if template.alarm:
            self.alarm = template.alarm

    def record_task_action(
        self, task: "TaskEntity", action: "ActionEntity"
    ) -> "TaskEntity":
        """Record an action on a task within this day aggregate.

        This method ensures all task modifications go through the Day aggregate root.
        It validates the task belongs to this day, calls the task's domain method,
        and raises domain events on behalf of the aggregate.

        Args:
            task: The task to record the action on
            action: The action to record

        Returns:
            The updated Task entity

        Raises:
            DomainError: If the task doesn't belong to this day or if the action is invalid
        """
        # Validate task belongs to this day
        if task.scheduled_date != self.date:
            raise DomainError(
                f"Task scheduled_date {task.scheduled_date} does not match day date {self.date}"
            )
        if task.user_id != self.user_id:
            raise DomainError(
                f"Task user_id {task.user_id} does not match day user_id {self.user_id}"
            )

        # Call task's domain method (business logic stays in Task)
        # This mutates the task in place (modifies self.actions, self.status, etc.)
        old_status = task.record_action(action)

        # Raise domain events on behalf of the aggregate
        if action.type == value_objects.ActionType.COMPLETE and task.completed_at:
            self._add_event(
                TaskCompletedEvent(
                    task_id=task.id,
                    completed_at=task.completed_at.isoformat(),
                )
            )

        # Record status change event if status changed
        if old_status != task.status:
            self._add_event(
                TaskStatusChangedEvent(
                    task_id=task.id,
                    old_status=old_status.value,
                    new_status=task.status.value,
                )
            )

        # Record action event
        self._add_event(
            TaskActionRecordedEvent(
                task_id=task.id,
                action_type=action.type.value,
            )
        )

        # Return the updated task (mutated in place by record_action)
        return task
