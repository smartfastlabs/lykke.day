"""Utility for serializing DayContext to JSON for LLM consumption."""

import json
from datetime import UTC, datetime
from typing import Any

from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.domain import value_objects
from lykke.domain.services.timing_status import TimingStatusService


def serialize_day_context(
    context: value_objects.DayContext,
    current_time: datetime,
) -> dict[str, Any]:
    """Serialize DayContext to a JSON-serializable dict for LLM evaluation.

    Args:
        context: The day context to serialize
        current_time: Current datetime for time-based context

    Returns:
        Dictionary with serialized day context data
    """
    day = context.day

    # Serialize tasks
    tasks = []
    for task in context.tasks:
        timing_info = TimingStatusService.task_status(task, current_time)
        task_data: dict[str, Any] = {
            "id": str(task.id),
            "name": task.name,
            "status": task.status.value,
            "type": task.type.value,
            "category": task.category.value,
            "scheduled_date": task.scheduled_date.isoformat(),
            "timing_status": timing_info.status.value,
        }

        if task.description:
            task_data["description"] = task.description

        if task.time_window:
            time_window_data: dict[str, Any] = {}
            if task.time_window.start_time:
                time_window_data["start_time"] = task.time_window.start_time.isoformat()
            if task.time_window.end_time:
                time_window_data["end_time"] = task.time_window.end_time.isoformat()
            if task.time_window.available_time:
                time_window_data["available_time"] = (
                    task.time_window.available_time.isoformat()
                )
            if task.time_window.cutoff_time:
                time_window_data["cutoff_time"] = (
                    task.time_window.cutoff_time.isoformat()
                )
            if time_window_data:
                task_data["time_window"] = time_window_data

        if task.completed_at:
            task_data["completed_at"] = task.completed_at.isoformat()
        if task.snoozed_until:
            task_data["snoozed_until"] = task.snoozed_until.isoformat()
        if timing_info.next_available_time:
            task_data["next_available_time"] = (
                timing_info.next_available_time.isoformat()
            )

        # Calculate time until task (if scheduled)
        if task.time_window and task.time_window.start_time:
            task_datetime = datetime.combine(
                task.scheduled_date, task.time_window.start_time
            )
            if task_datetime.tzinfo is None:
                task_datetime = task_datetime.replace(tzinfo=current_time.tzinfo or UTC)
            time_until = (task_datetime - current_time).total_seconds() / 60  # minutes
            task_data["minutes_until_start"] = int(time_until)

        tasks.append(task_data)

    routines = []
    for routine in context.routines:
        timing_info = TimingStatusService.routine_status(
            routine, context.tasks, current_time
        )
        routine_data: dict[str, Any] = {
            "id": str(routine.id),
            "name": routine.name,
            "status": routine.status.value,
            "category": routine.category.value,
            "date": routine.date.isoformat(),
            "timing_status": timing_info.status.value,
        }
        if routine.description:
            routine_data["description"] = routine.description
        if routine.snoozed_until:
            routine_data["snoozed_until"] = routine.snoozed_until.isoformat()
        if routine.time_window:
            routine_window: dict[str, Any] = {}
            if routine.time_window.start_time:
                routine_window["start_time"] = (
                    routine.time_window.start_time.isoformat()
                )
            if routine.time_window.end_time:
                routine_window["end_time"] = routine.time_window.end_time.isoformat()
            if routine.time_window.available_time:
                routine_window["available_time"] = (
                    routine.time_window.available_time.isoformat()
                )
            if routine.time_window.cutoff_time:
                routine_window["cutoff_time"] = (
                    routine.time_window.cutoff_time.isoformat()
                )
            if routine_window:
                routine_data["time_window"] = routine_window
        if timing_info.next_available_time:
            routine_data["next_available_time"] = (
                timing_info.next_available_time.isoformat()
            )
        routines.append(routine_data)

    # Serialize calendar entries
    calendar_entries = []
    for entry in context.calendar_entries:
        entry_data: dict[str, Any] = {
            "id": str(entry.id),
            "name": entry.name,
            "starts_at": entry.starts_at.isoformat(),
            "status": entry.status,
        }

        if entry.ends_at:
            entry_data["ends_at"] = entry.ends_at.isoformat()

        # Calculate time until event
        time_until = (entry.starts_at - current_time).total_seconds() / 60  # minutes
        entry_data["minutes_until_start"] = int(time_until)

        calendar_entries.append(entry_data)

    # Serialize brain dump items
    brain_dump_items = []
    for item in context.brain_dump_items:
        item_data: dict[str, Any] = {
            "id": str(item.id),
            "text": item.text,
            "status": item.status.value,
        }
        if item.created_at:
            item_data["created_at"] = item.created_at.isoformat()
        brain_dump_items.append(item_data)

    # Build final context
    result: dict[str, Any] = {
        "current_time": current_time.isoformat(),
        "day": {
            "id": str(day.id),
            "date": day.date.isoformat(),
            "status": day.status.value,
            "tags": [tag.value for tag in day.tags],
        },
        "tasks": tasks,
        "routines": routines,
        "calendar_entries": calendar_entries,
        "brain_dump_items": brain_dump_items,
    }

    if day.high_level_plan:
        result["high_level_plan"] = {
            "title": day.high_level_plan.title,
            "text": day.high_level_plan.text,
            "intentions": day.high_level_plan.intentions,
        }

    if isinstance(context, value_objects.LLMPromptContext):
        result["factoids"] = [
            {
                "id": str(factoid.id),
                "content": factoid.content,
                "factoid_type": factoid.factoid_type.value,
                "criticality": factoid.criticality.value,
                "ai_suggested": factoid.ai_suggested,
                "user_confirmed": factoid.user_confirmed,
                "created_at": factoid.created_at.isoformat(),
            }
            for factoid in context.factoids
        ]

        result["messages"] = [
            {
                "id": str(message.id),
                "user_id": str(message.user_id),
                "role": message.role.value,
                "content": message.content,
                "meta": message.meta,
                "created_at": message.created_at.isoformat(),
            }
            for message in context.messages
        ]

        push_notifications: list[dict[str, Any]] = []
        for notification in context.push_notifications:
            try:
                content = json.loads(notification.content)
            except (TypeError, json.JSONDecodeError):
                content = notification.content

            notification_data: dict[str, Any] = {
                "id": str(notification.id),
                "push_subscription_ids": [
                    str(subscription_id)
                    for subscription_id in notification.push_subscription_ids
                ],
                "content": content,
                "status": notification.status,
                "sent_at": notification.sent_at.isoformat(),
            }

            if notification.error_message:
                notification_data["error_message"] = notification.error_message
            if notification.message:
                notification_data["message"] = notification.message
            if notification.priority:
                notification_data["priority"] = notification.priority
            if notification.triggered_by:
                notification_data["triggered_by"] = notification.triggered_by
            if notification.llm_snapshot:
                notification_data["llm_snapshot"] = dataclass_to_json_dict(
                    notification.llm_snapshot
                )

            push_notifications.append(notification_data)

        result["push_notifications"] = push_notifications

    return result
