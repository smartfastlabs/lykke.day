import datetime
from datetime import time
from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4

from .base import BaseValueObject
from .task import TaskFrequency, TaskSchedule


class DayOfWeek(int, Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


@dataclass(kw_only=True)
class RecurrenceSchedule(BaseValueObject):
    frequency: TaskFrequency
    weekdays: list[DayOfWeek] | None = None
    day_number: int | None = (
        None  # Day of month (1-31) for MONTHLY, day of year (1-365) for YEARLY
    )

    def is_active_for_date(self, target_date: datetime.date) -> bool:
        """Check if this recurrence schedule is active for the given date.

        Args:
            target_date: The date to check

        Returns:
            True if the schedule is active for the date, False otherwise
        """
        # Handle MONTHLY frequency with day_number
        if self.frequency == TaskFrequency.MONTHLY:
            if self.day_number is not None:
                # Check if the day of month matches (handling months with fewer days)
                max_day = (
                    target_date.replace(month=target_date.month % 12 + 1, day=1)
                    - datetime.timedelta(days=1)
                ).day
                day_to_check = min(self.day_number, max_day)
                return target_date.day == day_to_check
            # If no day_number specified, check weekdays if provided
            if self.weekdays:
                return target_date.weekday() in self.weekdays
            return True

        # Handle YEARLY frequency with day_number
        if self.frequency == TaskFrequency.YEARLY:
            if self.day_number is not None:
                # Check if the day of year matches
                day_of_year = (
                    target_date - datetime.date(target_date.year, 1, 1)
                ).days + 1
                return day_of_year == self.day_number
            # If no day_number specified, check weekdays if provided
            if self.weekdays:
                return target_date.weekday() in self.weekdays
            return True

        # Handle CUSTOM_WEEKLY with weekdays
        if self.frequency == TaskFrequency.CUSTOM_WEEKLY:
            if self.weekdays:
                return target_date.weekday() in self.weekdays
            return True

        # Handle WORK_DAYS
        if self.frequency == TaskFrequency.WEEK_DAYS:
            return target_date.weekday() < 5  # Monday (0) to Friday (4)

        # Handle WEEKENDS
        if self.frequency == TaskFrequency.WEEKEND_DAYS:
            return target_date.weekday() >= 5  # Saturday (5) or Sunday (6)

        # Handle DAILY, WEEKLY, BI_WEEKLY, ONCE
        # For these, weekdays are optional filters
        if self.weekdays:
            return target_date.weekday() in self.weekdays

        return True


@dataclass(kw_only=True)
class TimeWindow(BaseValueObject):
    available_time: time | None = None
    start_time: time | None = None
    end_time: time | None = None
    cutoff_time: time | None = None


@dataclass(kw_only=True)
class RoutineTask(BaseValueObject):
    id: UUID = field(default_factory=uuid4)
    task_definition_id: UUID
    name: str | None = None
    schedule: TaskSchedule | None = None
    task_schedule: RecurrenceSchedule | None = None
    time_window: TimeWindow | None = None
