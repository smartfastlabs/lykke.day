from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from .base import BaseValueObject


class ActionType(str, Enum):
    COMPLETE = "COMPLETE"
    DELETE = "DELETE"
    EDIT = "EDIT"
    NOTIFY = "NOTIFY"
    PAUSE = "PAUSE"
    PUNT = "PUNT"
    RESUME = "RESUME"
    SNOOZE = "SNOOZE"
    START = "START"
    VIEW = "VIEW"


@dataclass(kw_only=True)
class Action(BaseValueObject):
    """Value object representing an action taken on a task or calendar entry."""

    type: ActionType
    data: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
