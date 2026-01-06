"""Utility functions for routine-related business logic."""

import datetime

from planned.domain import value_objects


def is_routine_active(schedule: value_objects.RoutineSchedule, target_date: datetime.date) -> bool:
    """Check if a routine is active for the given date.

    Args:
        schedule: The routine schedule to check
        target_date: The date to check

    Returns:
        True if the routine is active for the date, False otherwise
    """
    frequency = schedule.frequency
    
    # Handle MONTHLY frequency with day_number
    if frequency == value_objects.TaskFrequency.MONTHLY:
        if schedule.day_number is not None:
            # Check if the day of month matches (handling months with fewer days)
            max_day = (target_date.replace(month=target_date.month % 12 + 1, day=1) - datetime.timedelta(days=1)).day
            day_to_check = min(schedule.day_number, max_day)
            return target_date.day == day_to_check
        # If no day_number specified, check weekdays if provided
        if schedule.weekdays:
            return target_date.weekday() in schedule.weekdays
        return True
    
    # Handle YEARLY frequency with day_number
    if frequency == value_objects.TaskFrequency.YEARLY:
        if schedule.day_number is not None:
            # Check if the day of year matches
            day_of_year = (target_date - datetime.date(target_date.year, 1, 1)).days + 1
            return day_of_year == schedule.day_number
        # If no day_number specified, check weekdays if provided
        if schedule.weekdays:
            return target_date.weekday() in schedule.weekdays
        return True
    
    # Handle CUSTOM_WEEKLY with weekdays
    if frequency == value_objects.TaskFrequency.CUSTOM_WEEKLY:
        if schedule.weekdays:
            return target_date.weekday() in schedule.weekdays
        return True
    
    # Handle WORK_DAYS
    if frequency == value_objects.TaskFrequency.WEEK_DAYS:
        return target_date.weekday() < 5  # Monday (0) to Friday (4)
    
    # Handle WEEKENDS
    if frequency == value_objects.TaskFrequency.WEEKEND_DAYS:
        return target_date.weekday() >= 5  # Saturday (5) or Sunday (6)
    
    # Handle DAILY, WEEKLY, BI_WEEKLY, ONCE
    # For these, weekdays are optional filters
    if schedule.weekdays:
        return target_date.weekday() in schedule.weekdays
    
    return True

