"""Utility functions for building notification payloads."""

import datetime
import random
from typing import Any

from lykke.core.utils.dates import resolve_timezone
from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntryEntity, TaskEntity


def build_notification_payload_for_tasks(
    tasks: list[TaskEntity],
) -> value_objects.NotificationPayload:
    """Build a notification payload for one or more tasks.

    Args:
        tasks: List of tasks to include in the notification

    Returns:
        A NotificationPayload with task information
    """
    if len(tasks) == 1:
        task = tasks[0]
        title = task.name
        body = f"Task ready: {task.name}"
    else:
        title = f"{len(tasks)} tasks ready"
        body = f"You have {len(tasks)} tasks ready"

    # Include task information in the data field
    task_data = [
        {
            "id": str(task.id),
            "name": task.name,
            "status": task.status,
            "category": task.category,
        }
        for task in tasks
    ]

    return value_objects.NotificationPayload(
        title=title,
        body=body,
        actions=[
            value_objects.NotificationAction(
                action="view",
                title="View Tasks",
                icon="🔍",
            ),
        ],
        data={
            "type": "tasks",
            "task_ids": [str(task.id) for task in tasks],
            "tasks": task_data,
        },
    )


def build_notification_payload_for_calendar_entries(
    calendar_entries: list[CalendarEntryEntity],
) -> value_objects.NotificationPayload:
    """Build a notification payload for one or more calendar entries.

    Args:
        calendar_entries: List of calendar entries to include in the notification

    Returns:
        A NotificationPayload with calendar entry information
    """
    if len(calendar_entries) == 1:
        calendar_entry = calendar_entries[0]
        title = calendar_entry.name
        body = f"Event starting soon: {calendar_entry.name}"
    else:
        title = f"{len(calendar_entries)} events starting soon"
        body = f"You have {len(calendar_entries)} events starting soon"

    # Include calendar entry information in the data field
    calendar_entry_data = [
        {
            "id": str(calendar_entry.id),
            "name": calendar_entry.name,
            "starts_at": calendar_entry.starts_at.isoformat(),
            "ends_at": calendar_entry.ends_at.isoformat()
            if calendar_entry.ends_at
            else None,
            "calendar_id": str(calendar_entry.calendar_id),
            "platform_id": calendar_entry.platform_id,
            "status": calendar_entry.status,
        }
        for calendar_entry in calendar_entries
    ]

    return value_objects.NotificationPayload(
        title=title,
        body=body,
        actions=[
            value_objects.NotificationAction(
                action="view",
                title="View Events",
                icon="📅",
            ),
        ],
        data={
            "type": "calendar_entries",
            "calendar_entry_ids": [
                str(calendar_entry.id) for calendar_entry in calendar_entries
            ],
            "calendar_entries": calendar_entry_data,
        },
    )


def build_notification_payload_for_calendar_entry_reminder(
    entry: CalendarEntryEntity,
    message: str,
    *,
    minutes_before: int,
    scheduled_for: datetime.datetime,
) -> value_objects.NotificationPayload:
    """Build a notification payload for a calendar entry reminder."""
    return value_objects.NotificationPayload(
        title=entry.name,
        body=message,
        actions=[
            value_objects.NotificationAction(
                action="view",
                title="View Events",
                icon="📅",
            ),
        ],
        data={
            "type": "calendar_entry_reminder",
            "calendar_entry_id": str(entry.id),
            "starts_at": entry.starts_at.isoformat(),
            "minutes_before": minutes_before,
            "scheduled_for": scheduled_for.isoformat(),
        },
    )


def build_notification_payload_for_calendar_entry_change(
    change_type: str,
    entry_data: dict[str, Any] | CalendarEntryEntity,
) -> value_objects.NotificationPayload:
    """Build a notification payload for a calendar entry change (created/edited/deleted).

    Args:
        change_type: Type of change - "created", "edited", or "deleted"
        entry_data: Either a CalendarEntryEntity or a dict snapshot of entry data

    Returns:
        A NotificationPayload with calendar entry change information
    """
    # Extract entry name - handle both entity and dict
    if isinstance(entry_data, CalendarEntryEntity):
        entry_name = entry_data.name
        entry_id = str(entry_data.id)
        entry_dict = {
            "id": entry_id,
            "name": entry_data.name,
            "starts_at": entry_data.starts_at.isoformat(),
            "ends_at": entry_data.ends_at.isoformat() if entry_data.ends_at else None,
            "calendar_id": str(entry_data.calendar_id),
            "platform_id": entry_data.platform_id,
            "status": entry_data.status,
        }
    else:
        entry_name = entry_data.get("name", "Event")
        entry_id = str(entry_data.get("id", ""))
        entry_dict = {
            "id": entry_id,
            "name": entry_data.get("name", "Event"),
            "starts_at": entry_data.get("starts_at", ""),
            "ends_at": entry_data.get("ends_at"),
            "calendar_id": str(entry_data.get("calendar_id", "")),
            "platform_id": entry_data.get("platform_id", ""),
            "status": entry_data.get("status", ""),
        }

    # Build title and body based on change type (copy set C)
    if change_type == "created":
        title = "Calendar event created"
        body = entry_name
    elif change_type == "edited":
        title = "Calendar event edited"
        body = entry_name
    elif change_type == "deleted":
        title = "Calendar event deleted"
        body = entry_name
    else:
        # Fallback
        title = "Calendar event changed"
        body = entry_name

    return value_objects.NotificationPayload(
        title=title,
        body=body,
        actions=[
            value_objects.NotificationAction(
                action="view",
                title="View Events",
                icon="📅",
            ),
        ],
        data={
            "type": "calendar_entry_change",
            "change_type": change_type,
            "calendar_entry_id": entry_id,
            "calendar_entry": entry_dict,
        },
    )


def format_calendar_entry_time(
    entry: CalendarEntryEntity, timezone: str | None
) -> str:
    """Format calendar entry start time for display."""
    local_dt = entry.starts_at.astimezone(resolve_timezone(timezone))
    formatted = local_dt.strftime("%I:%M %p")
    return formatted.lstrip("0")


def format_calendar_entry_when(minutes_before: int) -> str:
    """Format the relative time string for reminders."""
    if minutes_before <= 0:
        return "now"
    if minutes_before == 1:
        return "in 1 minute"
    return f"in {minutes_before} minutes"


_PUSH_TEMPLATES = [
    "{title} starts {when} ({time}).",
    "Upcoming: {title} at {time} ({when}).",
    "Calendar reminder: {title} ({when}).",
    "{title} kicks off {when} at {time}.",
    "Event alert: {title} {when} ({time}).",
]

_TEXT_TEMPLATES = [
    "Reminder: {title} starts {when} ({time}).",
    "Heads up: {title} at {time} ({when}).",
    "{title} begins {when} at {time}.",
    "Calendar: {title} {when} ({time}).",
    "Upcoming meeting: {title} at {time} ({when}).",
]

_KIOSK_TEMPLATES = [
    "{title} starts {when}.",
    "Meeting time: {title} {when}.",
    "Event now: {title}.",
    "{title} is starting {when}.",
    "Calendar alert: {title} {when}.",
]


def pick_calendar_entry_message_template(
    channel: value_objects.CalendarEntryNotificationChannel,
    seed: str,
) -> str:
    """Pick a deterministic template for a calendar entry reminder."""
    rng = random.Random(seed)
    if channel == value_objects.CalendarEntryNotificationChannel.TEXT:
        return rng.choice(_TEXT_TEMPLATES)
    if channel == value_objects.CalendarEntryNotificationChannel.KIOSK_ALARM:
        return rng.choice(_KIOSK_TEMPLATES)
    return rng.choice(_PUSH_TEMPLATES)


def build_notification_payload_for_smart_notification(
    decision: value_objects.NotificationDecision,
) -> value_objects.NotificationPayload:
    """Build a notification payload for a smart notification from LLM.

    Args:
        decision: The LLM's notification decision

    Returns:
        A NotificationPayload with the LLM-generated message
    """
    return value_objects.NotificationPayload(
        title="Smart Notification",
        body=decision.message,
        actions=[
            value_objects.NotificationAction(
                action="view",
                title="View Day",
                icon="📅",
            ),
        ],
        data={
            "type": "smart_notification",
            "priority": decision.priority,
            "reason": decision.reason,
        },
    )
