"""Core utility functions."""

from .dates import (
    get_current_date,
    get_current_datetime,
    get_current_time,
    get_time_between,
    get_tomorrows_date,
)
from .printing import generate_pdf_from_page, send_pdf_to_printer
from .serialization import dataclass_to_json_dict
from .strings import normalize_email, normalize_phone_number, slugify
from .templates import render
from .youtube import kill_current_player, play_audio

__all__ = [
    "dataclass_to_json_dict",
    "generate_pdf_from_page",
    "get_current_date",
    "get_current_datetime",
    "get_current_time",
    "get_time_between",
    "get_tomorrows_date",
    "kill_current_player",
    "normalize_email",
    "normalize_phone_number",
    "play_audio",
    "render",
    "send_pdf_to_printer",
    "slugify",
]

