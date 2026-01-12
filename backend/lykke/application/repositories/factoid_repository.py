"""Protocol for FactoidRepository."""

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import FactoidEntity


class FactoidRepositoryReadOnlyProtocol(ReadOnlyRepositoryProtocol[FactoidEntity]):
    """Read-only protocol defining the interface for factoid repositories."""

    Query = value_objects.FactoidQuery


class FactoidRepositoryReadWriteProtocol(ReadWriteRepositoryProtocol[FactoidEntity]):
    """Read-write protocol defining the interface for factoid repositories."""

    Query = value_objects.FactoidQuery
