"""Filtering utilities for tasks."""

import datetime
from zoneinfo import ZoneInfo

from planned.core.config import settings
from planned.domain import entities
from planned.infrastructure.utils.dates import get_current_datetime, get_current_time


def is_task_eligible_for_upcoming(
    task: entities.Task,
    now: datetime.time,
    cutoff_time: datetime.time,
) -> bool:
    """Check if a task is eligible to be included in upcoming tasks.

    Args:
        task: The task to check
        now: Current time
        cutoff_time: The cutoff time for the look-ahead window

    Returns:
        True if the task should be included, False otherwise
    """
    # Exclude tasks that are not in eligible statuses
    if task.status not in (
        entities.TaskStatus.PENDING,
        entities.TaskStatus.NOT_STARTED,
        entities.TaskStatus.READY,
    ):
        return False

    # Exclude tasks that are already completed
    if task.completed_at:
        return False

    # Exclude tasks without a schedule
    if not task.schedule:
        return False

    # Check available_time - task must be available
    if task.schedule.available_time:
        if task.schedule.available_time > now:
            return False

    # Check start_time - task must start before cutoff
    elif task.schedule.start_time:
        if cutoff_time < task.schedule.start_time:
            return False

    # Check end_time - task must not have ended
    if task.schedule.end_time and now > task.schedule.end_time:
        return False

    return True


def calculate_cutoff_time(look_ahead: datetime.timedelta) -> datetime.time:
    """Calculate the cutoff time for the look-ahead window.

    Args:
        look_ahead: The time window to look ahead

    Returns:
        The cutoff time in the configured timezone
    """
    cutoff_datetime_utc = get_current_datetime() + look_ahead
    cutoff_datetime_local = cutoff_datetime_utc.astimezone(
        ZoneInfo(settings.TIMEZONE)
    )
    return cutoff_datetime_local.time()


def filter_upcoming_tasks(
    tasks: list[entities.Task],
    look_ahead: datetime.timedelta,
) -> list[entities.Task]:
    """Filter tasks to only include those that are upcoming within the look-ahead window.

    Args:
        tasks: List of tasks to filter
        look_ahead: The time window to look ahead

    Returns:
        List of tasks that are upcoming within the look-ahead window
    """
    now: datetime.time = get_current_time()
    cutoff_time = calculate_cutoff_time(look_ahead)

    # If cutoff is before now, it means we're looking at tomorrow
    if cutoff_time < now:
        return tasks

    result: list[entities.Task] = []
    for task in tasks:
        if is_task_eligible_for_upcoming(task, now, cutoff_time):
            result.append(task)

    return result

