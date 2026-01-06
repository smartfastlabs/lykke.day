"""Client for enqueueing background tasks."""

from uuid import UUID

from planned.presentation.workers.tasks import (
    example_triggered_task,
    schedule_all_users_week_task,
    schedule_user_week_task,
    sync_calendar_task,
)


async def enqueue_sync_calendar(user_id: UUID) -> None:
    """Enqueue a calendar sync task for a user.

    Args:
        user_id: The user ID to sync calendars for.
    """
    # In Taskiq, calling the decorated task function enqueues it
    # Dependencies are injected automatically, only pass user_id
    await sync_calendar_task.kiq(user_id=user_id)  # type: ignore[call-overload]


async def enqueue_schedule_all_users_week() -> None:
    """Enqueue the parent task that schedules all users for the week.

    This will load all users and create sub-tasks for each user.
    """
    await schedule_all_users_week_task.kiq()  # type: ignore[call-overload]


async def enqueue_schedule_user_week(user_id: UUID) -> None:
    """Enqueue a task to schedule a specific user's week.

    Args:
        user_id: The user ID to schedule the week for.
    """
    await schedule_user_week_task.kiq(user_id=user_id)  # type: ignore[call-overload]


async def enqueue_example_task(message: str) -> None:
    """Enqueue an example task that can be triggered via API.

    Args:
        message: A message to include in the task.
    """
    await example_triggered_task.kiq(message=message)
