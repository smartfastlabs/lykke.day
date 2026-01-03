from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .. import value_objects
from .base import BaseConfigObject


@dataclass(kw_only=True)
class ActionEntity(BaseConfigObject):
    type: value_objects.ActionType
    data: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
