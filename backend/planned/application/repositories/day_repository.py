"""Protocol for DayRepository."""

from planned.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from planned.domain.entities import DayEntity


class DayRepositoryReadOnlyProtocol(ReadOnlyRepositoryProtocol[DayEntity]):
    """Read-only protocol defining the interface for day repositories."""


class DayRepositoryReadWriteProtocol(ReadWriteRepositoryProtocol[DayEntity]):
    """Read-write protocol defining the interface for day repositories."""

