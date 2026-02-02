from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, date as dt_date, datetime, time as dt_time
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from lykke.core.exceptions import DomainError
from lykke.domain import value_objects
from lykke.domain.entities.auditable import AuditableEntity
from lykke.domain.entities.day_template import DayTemplateEntity  # noqa: TC001
from lykke.domain.events.day_events import (
    AlarmAddedEvent,
    AlarmRemovedEvent,
    AlarmStatusChangedEvent,
    AlarmTriggeredEvent,
    DayCompletedEvent,
    DayScheduledEvent,
    DayUnscheduledEvent,
)
from lykke.domain.events.task_events import (
    TaskActionRecordedEvent,
    TaskCompletedEvent,
    TaskPuntedEvent,
    TaskStatusChangedEvent,
)
from lykke.domain.value_objects.update import DayUpdateObject

from .base import BaseEntityObject

if TYPE_CHECKING:
    from lykke.domain.events.day_events import DayUpdatedEvent

    from .task import TaskEntity


@dataclass(kw_only=True)
class DayEntity(BaseEntityObject[DayUpdateObject, "DayUpdatedEvent"], AuditableEntity):
    user_id: UUID
    date: dt_date
    status: value_objects.DayStatus = value_objects.DayStatus.UNSCHEDULED
    scheduled_at: datetime | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    tags: list[value_objects.DayTag] = field(default_factory=list)
    template: DayTemplateEntity | None = None
    time_blocks: list[value_objects.DayTimeBlock] = field(default_factory=list)
    active_time_block_id: UUID | None = None
    alarms: list[value_objects.Alarm] = field(default_factory=list)
    high_level_plan: value_objects.HighLevelPlan | None = None
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
        namespace = uuid.uuid5(uuid.NAMESPACE_DNS, "lykke.day")
        name = f"{user_id}:{date.isoformat()}"
        return uuid.uuid5(namespace, name)

    @classmethod
    def create_for_date(
        cls,
        date: dt_date,
        user_id: UUID,
        template: DayTemplateEntity,
    ) -> DayEntity:
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
        )

    def schedule(self, template: DayTemplateEntity) -> None:
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
        self.status = value_objects.DayStatus.SCHEDULED
        self.scheduled_at = datetime.now(UTC)
        self._add_event(
            DayScheduledEvent(
                user_id=self.user_id,
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
        self._add_event(
            DayUnscheduledEvent(user_id=self.user_id, day_id=self.id, date=self.date)
        )

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
        self._add_event(
            DayCompletedEvent(user_id=self.user_id, day_id=self.id, date=self.date)
        )

    def update_template(self, template: DayTemplateEntity) -> None:
        """Update the day's template.

        Args:
            template: The new template to use
        """
        self.template = template

    def record_task_action(
        self, task: TaskEntity, action: value_objects.Action
    ) -> TaskEntity:
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
        if (
            action.type == value_objects.ActionType.COMPLETE
            and old_status != value_objects.TaskStatus.COMPLETE
            and task.completed_at
        ):
            self._add_event(
                TaskCompletedEvent(
                    user_id=self.user_id,
                    task_id=task.id,
                    completed_at=task.completed_at,
                    task_scheduled_date=task.scheduled_date,
                    task_name=task.name,
                    task_type=task.type.value,
                    task_category=task.category.value,
                    entity_id=task.id,
                    entity_type="task",
                    entity_date=task.scheduled_date,
                )
            )

        # Record status change event if status changed
        if old_status != task.status:
            self._add_event(
                TaskStatusChangedEvent(
                    user_id=self.user_id,
                    task_id=task.id,
                    old_status=old_status.value,
                    new_status=task.status.value,
                )
            )

            # Emit specific event for PUNT status changes (for audit logging)
            if task.status == value_objects.TaskStatus.PUNT:
                self._add_event(
                    TaskPuntedEvent(
                        user_id=self.user_id,
                        task_id=task.id,
                        old_status=old_status.value,
                        new_status=task.status.value,
                        task_scheduled_date=task.scheduled_date,
                        task_name=task.name,
                        task_type=task.type.value,
                        task_category=task.category.value,
                        entity_id=task.id,
                        entity_type="task",
                        entity_date=task.scheduled_date,
                    )
                )

        # Record action event
        self._add_event(
            TaskActionRecordedEvent(
                user_id=self.user_id,
                task_id=task.id,
                action_type=action.type.value,
            )
        )

        # Return the updated task (mutated in place by record_action)
        return task

    def add_alarm(self, alarm: value_objects.Alarm) -> value_objects.Alarm:
        """Add an alarm to this day.

        Args:
            alarm: The alarm to add

        Returns:
            The created Alarm value object
        """
        # Create a new list with the new alarm (alarms list is immutable)
        self.alarms = [*list(self.alarms), alarm]

        self._add_event(
            AlarmAddedEvent(
                user_id=self.user_id,
                day_id=self.id,
                date=self.date,
                alarm_name=alarm.name,
                alarm_time=alarm.time,
                alarm_type=alarm.type,
                alarm_url=alarm.url,
                entity_id=self.id,
                entity_type="day",
                entity_date=self.date,
            )
        )

        return alarm

    def remove_alarm(
        self,
        name: str,
        time_value: dt_time,
        *,
        alarm_type: value_objects.AlarmType | None = None,
        url: str | None = None,
    ) -> value_objects.Alarm:
        """Remove an alarm from this day.

        Args:
            name: The name of the alarm to remove
            time_value: The time of the alarm to remove
            alarm_type: Optional alarm type to disambiguate
            url: Optional alarm url to disambiguate

        Raises:
            DomainError: If the alarm is not found
        """
        match_index = None
        removed_alarm = None
        for i, alarm in enumerate(self.alarms):
            if alarm.name != name or alarm.time != time_value:
                continue
            if alarm_type is not None and alarm.type != alarm_type:
                continue
            if url is not None and alarm.url != url:
                continue
            match_index = i
            removed_alarm = alarm
            break

        if match_index is None or removed_alarm is None:
            raise DomainError(
                f"Alarm with name {name} and time {time_value} not found in this day"
            )

        self.alarms = [alarm for i, alarm in enumerate(self.alarms) if i != match_index]

        self._add_event(
            AlarmRemovedEvent(
                user_id=self.user_id,
                day_id=self.id,
                date=self.date,
                alarm_name=removed_alarm.name,
                alarm_time=removed_alarm.time,
                alarm_type=removed_alarm.type,
                alarm_url=removed_alarm.url,
                entity_id=self.id,
                entity_type="day",
                entity_date=self.date,
            )
        )

        return removed_alarm

    def update_alarm_status(
        self,
        alarm_id: UUID,
        status: value_objects.AlarmStatus,
        *,
        snoozed_until: datetime | None = None,
    ) -> value_objects.Alarm:
        """Update the status of an alarm.

        Args:
            alarm_id: The ID of the alarm to update
            status: The new status for the alarm
            snoozed_until: Optional snoozed-until timestamp for snoozed alarms

        Raises:
            DomainError: If the alarm is not found or snoozed_until is missing
        """
        alarm_index = None
        old_alarm = None
        for i, alarm in enumerate(self.alarms):
            if alarm.id == alarm_id:
                alarm_index = i
                old_alarm = alarm
                break

        if alarm_index is None or old_alarm is None:
            raise DomainError(f"Alarm with id {alarm_id} not found in this day")

        if status == value_objects.AlarmStatus.SNOOZED and snoozed_until is None:
            raise DomainError("Snoozed alarms require snoozed_until")

        next_snoozed_until = (
            snoozed_until if status == value_objects.AlarmStatus.SNOOZED else None
        )

        if old_alarm.status == status and old_alarm.snoozed_until == next_snoozed_until:
            return old_alarm

        updated_alarm = value_objects.Alarm(
            id=old_alarm.id,
            name=old_alarm.name,
            time=old_alarm.time,
            datetime=old_alarm.datetime,
            type=old_alarm.type,
            url=old_alarm.url,
            status=status,
            snoozed_until=next_snoozed_until,
        )

        new_alarms = list(self.alarms)
        new_alarms[alarm_index] = updated_alarm
        self.alarms = new_alarms

        if status == value_objects.AlarmStatus.TRIGGERED:
            self._add_event(
                AlarmTriggeredEvent(
                    user_id=self.user_id,
                    day_id=self.id,
                    date=self.date,
                    alarm_id=updated_alarm.id,
                    alarm_name=updated_alarm.name,
                    alarm_time=updated_alarm.time,
                    alarm_type=updated_alarm.type,
                    alarm_url=updated_alarm.url,
                    entity_id=self.id,
                    entity_type="day",
                    entity_date=self.date,
                )
            )
        else:
            self._add_event(
                AlarmStatusChangedEvent(
                    user_id=self.user_id,
                    day_id=self.id,
                    date=self.date,
                    alarm_id=updated_alarm.id,
                    alarm_name=updated_alarm.name,
                    alarm_time=updated_alarm.time,
                    alarm_type=updated_alarm.type,
                    alarm_url=updated_alarm.url,
                    old_status=old_alarm.status,
                    new_status=status,
                    entity_id=self.id,
                    entity_type="day",
                    entity_date=self.date,
                )
            )

        return updated_alarm
