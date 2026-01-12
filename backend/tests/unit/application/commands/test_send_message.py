"""Unit tests for SendMessageHandler command."""

from uuid import uuid4

import pytest

from lykke.application.commands.chatbot import SendMessageHandler
from lykke.domain import value_objects
from lykke.domain.entities import ConversationEntity, MessageEntity
from lykke.domain.events.ai_chat_events import ConversationUpdatedEvent


class _FakeConversationReadOnlyRepo:
    """Fake conversation repository for testing."""

    def __init__(self, conversation: ConversationEntity | None = None) -> None:
        self._conversation = conversation

    async def get(self, conversation_id: str) -> ConversationEntity | None:
        """Get conversation by ID."""
        if self._conversation and str(self._conversation.id) == str(conversation_id):
            return self._conversation
        return None


class _FakeReadOnlyRepos:
    """Fake read-only repositories container."""

    def __init__(self, conversation_repo: _FakeConversationReadOnlyRepo) -> None:
        fake = object()
        self.auth_token_ro_repo = fake
        self.bot_personality_ro_repo = fake
        self.calendar_entry_ro_repo = fake
        self.calendar_entry_series_ro_repo = fake
        self.calendar_ro_repo = fake
        self.conversation_ro_repo = conversation_repo
        self.day_ro_repo = fake
        self.day_template_ro_repo = fake
        self.factoid_ro_repo = fake
        self.message_ro_repo = fake
        self.push_subscription_ro_repo = fake
        self.routine_ro_repo = fake
        self.task_definition_ro_repo = fake
        self.task_ro_repo = fake
        self.time_block_definition_ro_repo = fake
        self.user_ro_repo = fake


class _FakeUoW:
    """Fake unit of work for testing."""

    def __init__(self) -> None:
        self.added: list = []
        self.committed = False

    def add(self, entity: object) -> None:
        """Add entity to UoW."""
        self.added.append(entity)

    async def create(self, entity: object) -> None:
        """Create entity (mark for insertion)."""
        # Mark entity as created and add to tracking
        if hasattr(entity, "create"):
            entity.create()
        self.added.append(entity)

    async def commit(self) -> None:
        """Commit transaction."""
        self.committed = True

    async def rollback(self) -> None:
        """Rollback transaction."""
        pass


class _FakeUoWFactory:
    """Fake UoW factory for testing."""

    def __init__(self) -> None:
        self.uow = _FakeUoW()

    def create(self, user_id: str) -> "_FakeUoWContextManager":
        """Create a UoW instance (returns async context manager)."""
        return _FakeUoWContextManager(self.uow)


class _FakeUoWContextManager:
    """Async context manager wrapper for fake UoW."""

    def __init__(self, uow: _FakeUoW) -> None:
        self._uow = uow

    async def __aenter__(self) -> _FakeUoW:
        """Context manager entry."""
        return self._uow

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[no-untyped-def]
        """Context manager exit."""
        if exc_type is None:
            await self._uow.commit()


@pytest.fixture
def conversation() -> ConversationEntity:
    """Create a test conversation."""
    return ConversationEntity(
        id=uuid4(),
        user_id=uuid4(),
        bot_personality_id=uuid4(),
        channel=value_objects.ConversationChannel.IN_APP,
        status=value_objects.ConversationStatus.ACTIVE,
        llm_provider=value_objects.LLMProvider.ANTHROPIC,
    )


@pytest.mark.asyncio
async def test_send_message_creates_user_message(conversation: ConversationEntity) -> None:
    """Test that sending a message creates a user message entity."""
    conversation_repo = _FakeConversationReadOnlyRepo(conversation)
    ro_repos = _FakeReadOnlyRepos(conversation_repo)
    uow_factory = _FakeUoWFactory()
    handler = SendMessageHandler(ro_repos, uow_factory, conversation.user_id)

    content = "Hello, how are you?"
    user_message, _ = await handler.run(
        conversation_id=conversation.id,
        content=content,
    )

    assert isinstance(user_message, MessageEntity)
    assert user_message.conversation_id == conversation.id
    assert user_message.role == value_objects.MessageRole.USER
    assert user_message.content == content


@pytest.mark.asyncio
async def test_send_message_generates_assistant_response(
    conversation: ConversationEntity,
) -> None:
    """Test that sending a message may generate an assistant response."""
    conversation_repo = _FakeConversationReadOnlyRepo(conversation)
    ro_repos = _FakeReadOnlyRepos(conversation_repo)
    uow_factory = _FakeUoWFactory()
    handler = SendMessageHandler(ro_repos, uow_factory, conversation.user_id)

    _, assistant_message = await handler.run(
        conversation_id=conversation.id,
        content="Test message",
    )

    # Currently returns dummy response (50% of the time)
    # If present, verify it's correct
    if assistant_message is not None:
        assert isinstance(assistant_message, MessageEntity)
        assert assistant_message.conversation_id == conversation.id
        assert assistant_message.role == value_objects.MessageRole.ASSISTANT


@pytest.mark.asyncio
async def test_send_message_adds_messages_to_uow(conversation: ConversationEntity) -> None:
    """Test that messages are added to the unit of work."""
    conversation_repo = _FakeConversationReadOnlyRepo(conversation)
    ro_repos = _FakeReadOnlyRepos(conversation_repo)
    uow_factory = _FakeUoWFactory()
    handler = SendMessageHandler(ro_repos, uow_factory, conversation.user_id)

    await handler.run(
        conversation_id=conversation.id,
        content="Test",
    )

    # Should have added: user message, (maybe assistant message), updated conversation
    assert len(uow_factory.uow.added) >= 2  # At least user message + conversation
    
    # Check types
    messages = [e for e in uow_factory.uow.added if isinstance(e, MessageEntity)]
    conversations = [e for e in uow_factory.uow.added if isinstance(e, ConversationEntity)]
    
    assert len(messages) >= 1  # At least user message
    assert len(conversations) == 1  # Updated conversation


@pytest.mark.asyncio
async def test_send_message_updates_conversation_timestamp(
    conversation: ConversationEntity,
) -> None:
    """Test that sending a message updates conversation's last_message_at."""
    conversation_repo = _FakeConversationReadOnlyRepo(conversation)
    ro_repos = _FakeReadOnlyRepos(conversation_repo)
    uow_factory = _FakeUoWFactory()
    handler = SendMessageHandler(ro_repos, uow_factory, conversation.user_id)

    original_time = conversation.last_message_at

    await handler.run(
        conversation_id=conversation.id,
        content="Test",
    )

    # Find updated conversation in UoW
    updated_conversations = [
        e for e in uow_factory.uow.added if isinstance(e, ConversationEntity)
    ]
    assert len(updated_conversations) == 1
    
    updated_conv = updated_conversations[0]
    assert updated_conv.last_message_at >= original_time


@pytest.mark.asyncio
async def test_send_message_conversation_has_domain_events(
    conversation: ConversationEntity,
) -> None:
    """Test that updated conversation has domain events."""
    conversation_repo = _FakeConversationReadOnlyRepo(conversation)
    ro_repos = _FakeReadOnlyRepos(conversation_repo)
    uow_factory = _FakeUoWFactory()
    handler = SendMessageHandler(ro_repos, uow_factory, conversation.user_id)

    await handler.run(
        conversation_id=conversation.id,
        content="Test",
    )

    # Find updated conversation
    updated_conversations = [
        e for e in uow_factory.uow.added if isinstance(e, ConversationEntity)
    ]
    updated_conv = updated_conversations[0]

    # Should have domain events (this is what the bug fix ensures)
    assert updated_conv.has_events()
    events = updated_conv.collect_events()
    assert len(events) > 0
    assert any(isinstance(e, ConversationUpdatedEvent) for e in events)


@pytest.mark.asyncio
async def test_send_message_commits_transaction(conversation: ConversationEntity) -> None:
    """Test that the transaction is committed."""
    conversation_repo = _FakeConversationReadOnlyRepo(conversation)
    ro_repos = _FakeReadOnlyRepos(conversation_repo)
    uow_factory = _FakeUoWFactory()
    handler = SendMessageHandler(ro_repos, uow_factory, conversation.user_id)

    await handler.run(
        conversation_id=conversation.id,
        content="Test",
    )

    assert uow_factory.uow.committed is True


@pytest.mark.asyncio
async def test_send_message_with_empty_content(conversation: ConversationEntity) -> None:
    """Test sending a message with empty content."""
    conversation_repo = _FakeConversationReadOnlyRepo(conversation)
    ro_repos = _FakeReadOnlyRepos(conversation_repo)
    uow_factory = _FakeUoWFactory()
    handler = SendMessageHandler(ro_repos, uow_factory, conversation.user_id)

    user_message, _ = await handler.run(
        conversation_id=conversation.id,
        content="",
    )

    assert user_message.content == ""


@pytest.mark.asyncio
async def test_send_message_with_long_content(conversation: ConversationEntity) -> None:
    """Test sending a message with very long content."""
    conversation_repo = _FakeConversationReadOnlyRepo(conversation)
    ro_repos = _FakeReadOnlyRepos(conversation_repo)
    uow_factory = _FakeUoWFactory()
    handler = SendMessageHandler(ro_repos, uow_factory, conversation.user_id)

    long_content = "A" * 10000
    user_message, _ = await handler.run(
        conversation_id=conversation.id,
        content=long_content,
    )

    assert user_message.content == long_content
    assert len(user_message.content) == 10000


@pytest.mark.asyncio
async def test_send_message_preserves_conversation_properties(
    conversation: ConversationEntity,
) -> None:
    """Test that sending a message doesn't change conversation properties."""
    conversation_repo = _FakeConversationReadOnlyRepo(conversation)
    ro_repos = _FakeReadOnlyRepos(conversation_repo)
    uow_factory = _FakeUoWFactory()
    handler = SendMessageHandler(ro_repos, uow_factory, conversation.user_id)

    await handler.run(
        conversation_id=conversation.id,
        content="Test",
    )

    updated_conversations = [
        e for e in uow_factory.uow.added if isinstance(e, ConversationEntity)
    ]
    updated_conv = updated_conversations[0]

    # Properties should be preserved
    assert updated_conv.id == conversation.id
    assert updated_conv.user_id == conversation.user_id
    assert updated_conv.bot_personality_id == conversation.bot_personality_id
    assert updated_conv.channel == conversation.channel
    assert updated_conv.status == conversation.status
    assert updated_conv.llm_provider == conversation.llm_provider
