import uuid
from datetime import UTC
from datetime import date as dt_date
from datetime import datetime
from uuid import UUID

from planned.core.exceptions import DomainError
from pydantic import Field, model_validator

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
from .action import Action
from .alarm import Alarm
from .day_template import DayTemplate
from .task import Task


class Day(BaseAggregateRoot):
    id: UUID = Field(default_factory=uuid.uuid4)
    user_id: UUID
    date: dt_date
    alarm: Alarm | None = None
    status: value_objects.DayStatus = value_objects.DayStatus.UNSCHEDULED
    scheduled_at: datetime | None = None

    tags: list[value_objects.DayTag] = Field(default_factory=list)
    template: DayTemplate | None = None

    @model_validator(mode="after")
    def generate_id(self) -> "Day":
        """Generate deterministic UUID5 based on date and user_id.

        This ensures that Days with the same date and user_id always have
        the same ID, making lookups stable and deterministic.
        """
        self.id = self.id_from_date_and_user(self.date, self.user_id)
        return self

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
        template: DayTemplate,
    ) -> "Day":
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

    def schedule(self, template: DayTemplate) -> None:
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

    def update_template(self, template: DayTemplate) -> None:
        """Update the day's template.

        Args:
            template: The new template to use
        """
        self.template = template
        # Update alarm if template has one
        if template.alarm:
            self.alarm = template.alarm

    def record_task_action(self, task: Task, action: Action) -> Task:
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
