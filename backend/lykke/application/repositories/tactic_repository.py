"""Protocol for TacticRepository."""

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import TacticEntity


class TacticRepositoryReadOnlyProtocol(ReadOnlyRepositoryProtocol[TacticEntity]):
    """Read-only protocol defining the interface for tactic repositories."""

    Query = value_objects.TacticQuery


class TacticRepositoryReadWriteProtocol(ReadWriteRepositoryProtocol[TacticEntity]):
    """Read-write protocol defining the interface for tactic repositories."""

    Query = value_objects.TacticQuery
