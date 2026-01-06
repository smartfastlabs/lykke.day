"""Core utility functions."""

from .dates import (
    get_current_date,
    get_current_datetime,
    get_current_time,
    get_time_between,
    get_tomorrows_date,
)
from .event_filters import filter_upcoming_calendar_entries
from .notifications import (
    build_notification_payload_for_calendar_entries,
    build_notification_payload_for_tasks,
)
from .printing import generate_pdf_from_page, send_pdf_to_printer
from .routine import is_routine_active
from .serialization import dataclass_to_json_dict
from .strings import normalize_email, normalize_phone_number, slugify
from .task_filters import filter_upcoming_tasks
from .templates import render
from .youtube import kill_current_player, play_audio

__all__ = [
    "build_notification_payload_for_calendar_entries",
    "build_notification_payload_for_tasks",
    "dataclass_to_json_dict",
    "filter_upcoming_calendar_entries",
    "filter_upcoming_tasks",
    "generate_pdf_from_page",
    "get_current_date",
    "get_current_datetime",
    "get_current_time",
    "get_time_between",
    "get_tomorrows_date",
    "is_routine_active",
    "kill_current_player",
    "normalize_email",
    "normalize_phone_number",
    "play_audio",
    "render",
    "send_pdf_to_printer",
    "slugify",
]

