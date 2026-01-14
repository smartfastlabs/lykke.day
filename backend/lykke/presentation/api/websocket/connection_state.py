"""Connection state management for WebSocket chatbot connections."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.unit_of_work import (
    ReadOnlyRepositories,
    UnitOfWorkFactory,
    UnitOfWorkProtocol,
)
from lykke.domain.entities import BotPersonalityEntity, ConversationEntity, UserEntity


@dataclass
class ConnectionState:
    """State management for a single WebSocket connection.

    This holds cached entities that are loaded once at connection time
    and reused throughout the connection lifetime to minimize database queries.

    Note: This is NOT a value object - it's mutable, stateful, and presentation-layer specific.
    It manages the lifecycle and cached state of a single WebSocket connection.
    """

    # Cached entities (loaded once)
    user: UserEntity
    conversation: ConversationEntity
    bot_personality: BotPersonalityEntity

    # Factories for operations
    ro_repos: ReadOnlyRepositories
    uow_factory: UnitOfWorkFactory

    # Connection metadata
    conversation_id: UUID
    user_id: UUID

    @classmethod
    async def create(
        cls,
        conversation_id: UUID,
        user: UserEntity,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
    ) -> "ConnectionState":
        """Create a new ConnectionState by loading required entities.

        Args:
            conversation_id: ID of the conversation
            user: Authenticated user entity
            ro_repos: Read-only repository factory
            uow_factory: Unit of work factory

        Returns:
            Initialized ConnectionState with all entities loaded

        Raises:
            NotFoundError: If conversation or bot personality doesn't exist
        """
        # Load conversation
        conversation = await ro_repos.conversation_ro_repo.get(conversation_id)

        # Load bot personality
        bot_personality = await ro_repos.bot_personality_ro_repo.get(
            conversation.bot_personality_id
        )

        return cls(
            user=user,
            conversation=conversation,
            bot_personality=bot_personality,
            ro_repos=ro_repos,
            uow_factory=uow_factory,
            conversation_id=conversation_id,
            user_id=user.id,
        )

    def new_uow(self) -> UnitOfWorkProtocol:
        """Create a new Unit of Work for this connection's user."""
        return self.uow_factory.create(self.user_id)
