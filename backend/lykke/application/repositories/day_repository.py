"""Protocol for DayRepository."""

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity


class DayRepositoryReadOnlyProtocol(ReadOnlyRepositoryProtocol[DayEntity]):
    """Read-only protocol defining the interface for day repositories."""

    Query = value_objects.DayQuery


class DayRepositoryReadWriteProtocol(ReadWriteRepositoryProtocol[DayEntity]):
    """Read-write protocol defining the interface for day repositories."""

    Query = value_objects.DayQuery
