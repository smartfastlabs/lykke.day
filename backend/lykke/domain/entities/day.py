from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, date as dt_date, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from lykke.core.exceptions import DomainError
from lykke.domain import value_objects
from lykke.domain.entities.auditable import AuditableEntity
from lykke.domain.entities.day_template import DayTemplateEntity
from lykke.domain.events.day_events import (
    BrainDumpItemAddedEvent,
    BrainDumpItemRemovedEvent,
    BrainDumpItemStatusChangedEvent,
    DayCompletedEvent,
    DayScheduledEvent,
    DayUnscheduledEvent,
    ReminderAddedEvent,
    ReminderRemovedEvent,
    ReminderStatusChangedEvent,
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
    reminders: list[value_objects.Reminder] = field(default_factory=list)
    brain_dump_items: list[value_objects.BrainDumpItem] = field(default_factory=list)
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
        if action.type == value_objects.ActionType.COMPLETE and task.completed_at:
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

    def add_reminder(self, name: str) -> value_objects.Reminder:
        """Add a reminder to this day.

        This method enforces the business rule that a day can have at most 5 active reminders.
        Active reminders are those with status INCOMPLETE (completed and punted reminders don't count).

        Args:
            name: The name of the reminder to add

        Returns:
            The created Reminder value object

        Raises:
            DomainError: If the day already has 5 active reminders
        """
        active_reminders = [
            reminder
            for reminder in self.reminders
            if reminder.status == value_objects.ReminderStatus.INCOMPLETE
        ]
        if len(active_reminders) >= 5:
            raise DomainError(
                "Cannot add reminder: a day can have at most 5 active reminders. "
                f"Current active reminder count: {len(active_reminders)}"
            )

        reminder = value_objects.Reminder(
            id=uuid4(),
            name=name,
            status=value_objects.ReminderStatus.INCOMPLETE,
            created_at=datetime.now(UTC),
        )

        # Create a new list with the new reminder (reminders list is immutable)
        self.reminders = [*list(self.reminders), reminder]

        self._add_event(
            ReminderAddedEvent(
                user_id=self.user_id,
                day_id=self.id,
                date=self.date,
                reminder_id=reminder.id,
                reminder_name=reminder.name,
                entity_id=self.id,
                entity_type="day",
                entity_date=self.date,
            )
        )

        return reminder

    def update_reminder_status(
        self, reminder_id: UUID, status: value_objects.ReminderStatus
    ) -> None:
        """Update the status of a reminder.

        Args:
            reminder_id: The ID of the reminder to update
            status: The new status for the reminder

        Raises:
            DomainError: If the reminder is not found
        """
        reminder_index = None
        old_reminder = None
        for i, reminder in enumerate(self.reminders):
            if reminder.id == reminder_id:
                reminder_index = i
                old_reminder = reminder
                break

        if reminder_index is None or old_reminder is None:
            raise DomainError(f"Reminder with id {reminder_id} not found in this day")

        if old_reminder.status == status:
            # No change needed
            return

        # Create updated reminder with new status
        updated_reminder = value_objects.Reminder(
            id=old_reminder.id,
            name=old_reminder.name,
            status=status,
            created_at=old_reminder.created_at,
        )

        # Create new list with updated reminder
        new_reminders = list(self.reminders)
        new_reminders[reminder_index] = updated_reminder
        self.reminders = new_reminders

        self._add_event(
            ReminderStatusChangedEvent(
                user_id=self.user_id,
                day_id=self.id,
                date=self.date,
                reminder_id=reminder_id,
                old_status=old_reminder.status,
                new_status=status,
                reminder_name=old_reminder.name,
                entity_id=self.id,
                entity_type="day",
                entity_date=self.date,
            )
        )

    def remove_reminder(self, reminder_id: UUID) -> None:
        """Remove a reminder from this day.

        Args:
            reminder_id: The ID of the reminder to remove

        Raises:
            DomainError: If the reminder is not found
        """
        reminder_to_remove = None
        for reminder in self.reminders:
            if reminder.id == reminder_id:
                reminder_to_remove = reminder
                break

        if reminder_to_remove is None:
            raise DomainError(f"Reminder with id {reminder_id} not found in this day")

        # Create new list without the removed reminder
        self.reminders = [
            reminder for reminder in self.reminders if reminder.id != reminder_id
        ]

        self._add_event(
            ReminderRemovedEvent(
                user_id=self.user_id,
                day_id=self.id,
                date=self.date,
                reminder_id=reminder_id,
                reminder_name=reminder_to_remove.name,
                entity_id=self.id,
                entity_type="day",
                entity_date=self.date,
            )
        )

    def add_brain_dump_item(self, text: str) -> value_objects.BrainDumpItem:
        """Add a brain dump item to this day."""
        item = value_objects.BrainDumpItem(
            id=uuid4(),
            text=text,
            status=value_objects.BrainDumpItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
        )

        self.brain_dump_items = [*list(self.brain_dump_items), item]

        self._add_event(
            BrainDumpItemAddedEvent(
                day_id=self.id,
                user_id=self.user_id,
                date=self.date,
                item_id=item.id,
                item_text=item.text,
                entity_id=self.id,
                entity_type="day",
                entity_date=self.date,
            )
        )

        return item

    def update_brain_dump_item_status(
        self, item_id: UUID, status: value_objects.BrainDumpItemStatus
    ) -> None:
        """Update the status of a brain dump item."""
        item_index = None
        old_item = None
        for i, item in enumerate(self.brain_dump_items):
            if item.id == item_id:
                item_index = i
                old_item = item
                break

        if item_index is None or old_item is None:
            raise DomainError(
                f"Brain dump item with id {item_id} not found in this day"
            )

        if old_item.status == status:
            return

        updated_item = value_objects.BrainDumpItem(
            id=old_item.id,
            text=old_item.text,
            status=status,
            created_at=old_item.created_at,
        )

        new_items = list(self.brain_dump_items)
        new_items[item_index] = updated_item
        self.brain_dump_items = new_items

        self._add_event(
            BrainDumpItemStatusChangedEvent(
                user_id=self.user_id,
                day_id=self.id,
                date=self.date,
                item_id=item_id,
                old_status=old_item.status,
                new_status=status,
                item_text=old_item.text,
                entity_id=self.id,
                entity_type="day",
                entity_date=self.date,
            )
        )

    def remove_brain_dump_item(self, item_id: UUID) -> None:
        """Remove a brain dump item from this day."""
        item_to_remove = None
        for item in self.brain_dump_items:
            if item.id == item_id:
                item_to_remove = item
                break

        if item_to_remove is None:
            raise DomainError(
                f"Brain dump item with id {item_id} not found in this day"
            )

        self.brain_dump_items = [
            item for item in self.brain_dump_items if item.id != item_id
        ]

        self._add_event(
            BrainDumpItemRemovedEvent(
                user_id=self.user_id,
                day_id=self.id,
                date=self.date,
                item_id=item_id,
                item_text=item_to_remove.text,
                entity_id=self.id,
                entity_type="day",
                entity_date=self.date,
            )
        )
