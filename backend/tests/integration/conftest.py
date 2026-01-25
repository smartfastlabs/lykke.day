"""Fixtures for integration tests - uses real database with per-test user isolation."""

from datetime import time
from uuid import UUID, uuid4

import pytest
import pytest_asyncio

from lykke.domain.entities import (
    AuthTokenEntity,
    BotPersonalityEntity,
    CalendarEntity,
    ConversationEntity,
    UserEntity,
)
from lykke.domain.entities.day_template import DayTemplateEntity
from lykke.domain.value_objects.ai_chat import ConversationChannel, LLMProvider
from lykke.domain.value_objects.user import UserSetting
from lykke.infrastructure.repositories import (
    AuditLogRepository,
    AuthTokenRepository,
    BotPersonalityRepository,
    BrainDumpRepository,
    CalendarEntryRepository,
    CalendarRepository,
    ConversationRepository,
    DayRepository,
    DayTemplateRepository,
    FactoidRepository,
    MessageRepository,
    PushSubscriptionRepository,
    RoutineDefinitionRepository,
    TaskDefinitionRepository,
    TaskRepository,
    TimeBlockDefinitionRepository,
    UserRepository,
)


@pytest_asyncio.fixture
async def create_test_user():
    """Factory to create unique test users."""

    async def _create_user(email: str | None = None, **kwargs) -> UserEntity:
        """Create a test user with unique email."""
        if email is None:
            email = f"test-{uuid4()}@example.com"

        user = UserEntity(
            email=email,
            hashed_password="test_hash",
            settings=kwargs.pop("settings", UserSetting()),
            **kwargs,
        )
        user_repo = UserRepository()
        return await user_repo.put(user)

    return _create_user


@pytest_asyncio.fixture
async def test_user(create_test_user):
    """Create a unique user for each test."""
    return await create_test_user(
        settings=UserSetting(
            template_defaults=[
                "default",
                "default",
                "default",
                "default",
                "default",
                "weekend",
                "weekend",
            ],
        ),
    )


async def _setup_day_templates_for_user(user: UserEntity) -> None:
    """Helper function to create default day templates for a user."""
    repo = DayTemplateRepository(user_id=user.id)

    # Create default template (UUID will be auto-generated from slug + user_id)
    default_template = DayTemplateEntity(
        user_id=user.id,
        slug="default",
    )
    await repo.put(default_template)

    # Create weekend template (UUID will be auto-generated from slug + user_id)
    weekend_template = DayTemplateEntity(
        user_id=user.id,
        slug="weekend",
    )
    await repo.put(weekend_template)


@pytest.fixture
def setup_day_templates(test_user):
    """Create default and weekend day templates for tests."""
    return _setup_day_templates_for_user(test_user)


# Repository fixtures - all scoped to test_user
@pytest_asyncio.fixture
async def user_repo():
    """UserRepository - not user-scoped."""
    return UserRepository()


@pytest_asyncio.fixture
async def day_repo(test_user):
    """DayRepository scoped to test_user."""
    return DayRepository(user_id=test_user.id)


@pytest_asyncio.fixture
async def brain_dump_repo(test_user):
    """BrainDumpRepository scoped to test_user."""
    return BrainDumpRepository(user_id=test_user.id)


@pytest_asyncio.fixture
async def day_template_repo(test_user):
    """DayTemplateRepository scoped to test_user."""
    return DayTemplateRepository(user_id=test_user.id)


@pytest_asyncio.fixture
async def calendar_entry_repo(test_user):
    """CalendarEntryRepository scoped to test_user."""
    return CalendarEntryRepository(user_id=test_user.id)


@pytest_asyncio.fixture
async def task_repo(test_user):
    """TaskRepository scoped to test_user."""
    return TaskRepository(user_id=test_user.id)


@pytest_asyncio.fixture
async def calendar_repo(test_user):
    """CalendarRepository scoped to test_user."""
    return CalendarRepository(user_id=test_user.id)


@pytest_asyncio.fixture
async def create_calendar(calendar_repo, create_auth_token):
    """Factory to create calendars with valid auth tokens."""

    async def _create_calendar(
        *,
        user_id: UUID,
        auth_token_id: UUID | None = None,
        calendar_id: UUID | None = None,
        name: str = "Test Calendar",
        platform: str = "google",
        platform_id: str | None = None,
    ) -> CalendarEntity:
        if auth_token_id is None:
            auth_token = await create_auth_token(user_id=user_id, platform=platform)
            auth_token_id = auth_token.id

        if platform_id is None:
            platform_id = f"calendar-{uuid4()}"

        calendar = CalendarEntity(
            id=calendar_id,
            user_id=user_id,
            name=name,
            auth_token_id=auth_token_id,
            platform=platform,
            platform_id=platform_id,
        )
        return await calendar_repo.put(calendar)

    return _create_calendar


@pytest_asyncio.fixture
async def auth_token_repo(test_user):
    """AuthTokenRepository (not user-scoped)."""
    return AuthTokenRepository()


@pytest_asyncio.fixture
async def create_auth_token(auth_token_repo):
    """Factory to create auth tokens for a user."""

    async def _create_auth_token(
        *,
        user_id: UUID,
        platform: str = "google",
        token: str = "test_token",
    ) -> AuthTokenEntity:
        auth_token = AuthTokenEntity(
            user_id=user_id,
            platform=platform,
            token=token,
        )
        return await auth_token_repo.put(auth_token)

    return _create_auth_token


@pytest_asyncio.fixture
async def push_subscription_repo(test_user):
    """PushSubscriptionRepository scoped to test_user."""
    return PushSubscriptionRepository(user_id=test_user.id)


@pytest_asyncio.fixture
async def routine_definition_repo(test_user):
    """RoutineDefinitionRepository scoped to test_user."""
    return RoutineDefinitionRepository(user_id=test_user.id)


@pytest_asyncio.fixture
async def task_definition_repo(test_user):
    """TaskDefinitionRepository scoped to test_user."""
    return TaskDefinitionRepository(user_id=test_user.id)


@pytest_asyncio.fixture
async def time_block_definition_repo(test_user):
    """TimeBlockDefinitionRepository scoped to test_user."""
    return TimeBlockDefinitionRepository(user_id=test_user.id)


# AI Chatbot repository fixtures
@pytest_asyncio.fixture
async def bot_personality_repo(test_user):
    """BotPersonalityRepository with user scoping."""
    return BotPersonalityRepository(user_id=test_user.id)


@pytest_asyncio.fixture
async def conversation_repo(test_user):
    """ConversationRepository scoped to test_user."""
    return ConversationRepository(user_id=test_user.id)


@pytest_asyncio.fixture
async def message_repo(test_user):
    """MessageRepository (not user-scoped directly)."""
    return MessageRepository(user_id=test_user.id)


@pytest_asyncio.fixture
async def factoid_repo(test_user):
    """FactoidRepository scoped to test_user."""
    return FactoidRepository(user_id=test_user.id)


@pytest_asyncio.fixture
async def audit_log_repo(test_user):
    """AuditLogRepository scoped to test_user."""
    return AuditLogRepository(user_id=test_user.id)


# AI Chatbot test data fixtures
@pytest_asyncio.fixture
async def bot_personality(bot_personality_repo, test_user):
    """Create a test bot personality."""
    personality = BotPersonalityEntity(
        id=uuid4(),
        user_id=test_user.id,
        name="Test Bot",
        system_prompt="You are a helpful test bot assistant.",
    )
    return await bot_personality_repo.put(personality)


@pytest_asyncio.fixture
async def create_bot_personality(bot_personality_repo, test_user):
    """Factory to create bot personalities for a user."""

    async def _create_bot_personality(
        *, user_id: UUID | None = None, **kwargs
    ) -> BotPersonalityEntity:
        if user_id is None:
            user_id = test_user.id
        personality = BotPersonalityEntity(user_id=user_id, **kwargs)
        return await bot_personality_repo.put(personality)

    return _create_bot_personality


@pytest_asyncio.fixture
async def conversation(conversation_repo, test_user, bot_personality):
    """Create a test conversation."""
    conv = ConversationEntity(
        id=uuid4(),
        user_id=test_user.id,
        bot_personality_id=bot_personality.id,
        channel=ConversationChannel.IN_APP,
        llm_provider=LLMProvider.ANTHROPIC,
    )
    return await conversation_repo.put(conv)


@pytest_asyncio.fixture
async def create_conversation(conversation_repo, test_user, bot_personality):
    """Factory to create conversations for a user."""

    async def _create_conversation(
        *,
        user_id: UUID | None = None,
        bot_personality_id: UUID | None = None,
        **kwargs,
    ) -> ConversationEntity:
        if user_id is None:
            user_id = test_user.id
        if bot_personality_id is None:
            bot_personality_id = bot_personality.id
        conv = ConversationEntity(
            user_id=user_id,
            bot_personality_id=bot_personality_id,
            **kwargs,
        )
        return await conversation_repo.put(conv)

    return _create_conversation
