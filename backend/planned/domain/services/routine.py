"""Domain service for routine-related business logic."""

import datetime

from planned.domain.value_objects.routine import RoutineSchedule


class RoutineService:
    """Domain service for routine-related business logic.

    Contains pure business logic that doesn't depend on infrastructure.
    """

    @staticmethod
    def is_routine_active(schedule: RoutineSchedule, target_date: datetime.date) -> bool:
        """Check if a routine is active for the given date.

        Args:
            schedule: The routine schedule to check
            target_date: The date to check

        Returns:
            True if the routine is active for the date, False otherwise
        """
        if not schedule.weekdays:
            return True
        return target_date.weekday() in schedule.weekdays

