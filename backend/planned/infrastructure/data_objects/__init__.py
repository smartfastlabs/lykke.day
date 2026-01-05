"""Backwards-compatible re-export of domain data objects.

Data objects now live in `planned.domain.data_objects`.
"""

from planned.domain.data_objects import (  # noqa: F401
    AuthToken,
    DayTemplate,
    PushSubscription,
    TaskDefinition,
)

__all__ = [
    "AuthToken",
    "DayTemplate",
    "PushSubscription",
    "TaskDefinition",
]

