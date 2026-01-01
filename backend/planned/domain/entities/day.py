import uuid
from datetime import UTC, date as dt_date, datetime
from uuid import UUID

from pydantic import Field, model_validator

from planned.core.exceptions import DomainError

from ..events.base import BaseAggregateRoot
from ..events.day_events import DayCompletedEvent, DayScheduledEvent, DayUnscheduledEvent
from ..value_objects.day import DayStatus, DayTag
from .alarm import Alarm
from .day_template import DayTemplate


class Day(BaseAggregateRoot):
    id: UUID = Field(default_factory=uuid.uuid4)
    user_id: UUID
    date: dt_date
    alarm: Alarm | None = None
    status: DayStatus = DayStatus.UNSCHEDULED
    scheduled_at: datetime | None = None

    tags: list[DayTag] = Field(default_factory=list)
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
            status=DayStatus.UNSCHEDULED,
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
        if self.status != DayStatus.UNSCHEDULED:
            raise DomainError(
                f"Cannot schedule day in {self.status.value} status. "
                "Only unscheduled days can be scheduled."
            )

        self.template = template
        self.alarm = template.alarm
        self.status = DayStatus.SCHEDULED
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
        if self.status != DayStatus.SCHEDULED:
            raise DomainError(
                f"Cannot unschedule day in {self.status.value} status. "
                "Only scheduled days can be unscheduled."
            )

        self.status = DayStatus.UNSCHEDULED
        self.scheduled_at = None
        self._add_event(DayUnscheduledEvent(day_id=self.id, date=self.date))

    def complete(self) -> None:
        """Mark the day as complete.

        This method enforces the business rule that only scheduled days
        can be completed.

        Raises:
            DomainError: If the day is not in SCHEDULED status
        """
        if self.status != DayStatus.SCHEDULED:
            raise DomainError(
                f"Cannot complete day in {self.status.value} status. "
                "Only scheduled days can be completed."
            )

        self.status = DayStatus.COMPLETE
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
