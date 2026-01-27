from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .base import BaseValueObject


class TimingStatus(str, Enum):
    HIDDEN = "hidden"
    INACTIVE = "inactive"
    AVAILABLE = "available"
    ACTIVE = "active"
    PAST_DUE = "past-due"


@dataclass(kw_only=True)
class TimingStatusInfo(BaseValueObject):
    status: TimingStatus
    next_available_time: datetime | None = None
