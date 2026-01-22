"""Protocol for UseCaseConfigRepository."""

from typing import Protocol

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities.usecase_config import UseCaseConfigEntity


class UseCaseConfigRepositoryReadOnlyProtocol(
    ReadOnlyRepositoryProtocol[UseCaseConfigEntity], Protocol
):
    """Read-only protocol defining the interface for usecase config repositories."""

    Query: type[value_objects.UseCaseConfigQuery] = value_objects.UseCaseConfigQuery


class UseCaseConfigRepositoryReadWriteProtocol(
    ReadWriteRepositoryProtocol[UseCaseConfigEntity], Protocol
):
    """Read-write protocol defining the interface for usecase config repositories."""

    Query: type[value_objects.UseCaseConfigQuery] = value_objects.UseCaseConfigQuery
