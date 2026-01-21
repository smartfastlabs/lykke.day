"""Protocol for BotPersonalityRepository."""

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import BotPersonalityEntity


class BotPersonalityRepositoryReadOnlyProtocol(ReadOnlyRepositoryProtocol[BotPersonalityEntity]):
    """Read-only protocol defining the interface for bot personality repositories."""

    Query = value_objects.BotPersonalityQuery


class BotPersonalityRepositoryReadWriteProtocol(ReadWriteRepositoryProtocol[BotPersonalityEntity]):
    """Read-write protocol defining the interface for bot personality repositories."""

    Query = value_objects.BotPersonalityQuery
