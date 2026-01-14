"""Activity type enum for audit log entries."""

from enum import Enum


class ActivityType(str, Enum):
    """Enumeration of user activity types tracked in audit logs."""

    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_PUNTED = "TASK_PUNTED"
    MESSAGE_SENT = "MESSAGE_SENT"
    MESSAGE_RECEIVED = "MESSAGE_RECEIVED"
