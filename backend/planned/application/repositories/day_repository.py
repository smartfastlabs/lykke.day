"""Protocol for DayRepository."""

from planned.application.repositories.base import (
    ReadOnlySimpleDateScopedRepositoryProtocol,
    SimpleDateScopedRepositoryProtocol,
)
from planned.domain.entities import DayEntity


class DayRepositoryReadOnlyProtocol(ReadOnlySimpleDateScopedRepositoryProtocol[DayEntity]):
    """Read-only protocol defining the interface for day repositories."""
    pass


class DayRepositoryReadWriteProtocol(SimpleDateScopedRepositoryProtocol[DayEntity]):
    """Read-write protocol defining the interface for day repositories."""
    pass

