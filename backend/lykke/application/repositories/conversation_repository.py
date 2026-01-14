"""Protocol for ConversationRepository."""

from lykke.application.repositories.base import (
    ReadOnlyRepositoryProtocol,
    ReadWriteRepositoryProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import ConversationEntity


class ConversationRepositoryReadOnlyProtocol(ReadOnlyRepositoryProtocol[ConversationEntity]):
    """Read-only protocol defining the interface for conversation repositories."""

    Query = value_objects.ConversationQuery


class ConversationRepositoryReadWriteProtocol(ReadWriteRepositoryProtocol[ConversationEntity]):
    """Read-write protocol defining the interface for conversation repositories."""

    Query = value_objects.ConversationQuery
