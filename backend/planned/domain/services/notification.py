"""Domain service for building notification payloads."""

from planned.domain import value_objects
from planned.domain.entities import CalendarEntity, CalendarEntryEntity, TaskEntity


class NotificationPayloadBuilder:
    """Domain service for building notification payloads.

    Contains pure business logic for constructing notification payloads
    from domain entities.
    """

    @staticmethod
    def build_for_tasks(tasks: list[TaskEntity]) -> value_objects.NotificationPayload:
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
                "status": task.status.value,
                "category": task.category.value,
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

    @staticmethod
    def build_for_calendar_entries(
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

