"""Protocol for BrainDumpRepository."""

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import BrainDumpEntity


class BrainDumpRepositoryReadOnlyProtocol(
    ReadOnlyRepositoryProtocol[BrainDumpEntity]
):
    """Read-only protocol defining the interface for brain dump repositories."""

    Query = value_objects.BrainDumpQuery


class BrainDumpRepositoryReadWriteProtocol(
    ReadWriteRepositoryProtocol[BrainDumpEntity]
):
    """Read-write protocol defining the interface for brain dump repositories."""

    Query = value_objects.BrainDumpQuery
