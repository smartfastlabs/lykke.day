"""Integration tests for MessageRepository."""

import datetime
from datetime import UTC
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from planned.core.config import settings
from planned.core.exceptions import exceptions
from planned.domain.entities import Message
from planned.infrastructure.repositories import MessageRepository
from planned.domain.value_objects.query import DateQuery


@pytest.mark.asyncio
async def test_get(message_repo, test_user, test_date):
    """Test getting a message by ID."""
    sent_at = datetime.datetime.combine(
        test_date,
        datetime.time(hour=10),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    message = Message(
        uuid=uuid4(),
        user_uuid=test_user.uuid,
        author="system",
        content="Test message",
        sent_at=sent_at,
    )
    await message_repo.put(message)
    
    result = await message_repo.get(message.uuid)
    
    assert result.uuid == message.uuid
    assert result.content == "Test message"


@pytest.mark.asyncio
async def test_get_not_found(message_repo):
    """Test getting a non-existent message raises NotFoundError."""
    with pytest.raises(exceptions.NotFoundError):
        await message_repo.get(uuid4())


@pytest.mark.asyncio
async def test_put(message_repo, test_user, test_date):
    """Test creating a new message."""
    sent_at = datetime.datetime.combine(
        test_date,
        datetime.time(hour=10),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    message = Message(
        uuid=uuid4(),
        user_uuid=test_user.uuid,
        author="user",
        content="New message",
        sent_at=sent_at,
    )
    
    result = await message_repo.put(message)
    
    assert result.content == "New message"
    assert result.author == "user"


@pytest.mark.asyncio
async def test_search_query(message_repo, test_user, test_date, test_date_tomorrow):
    """Test searching messages with DateQuery."""
    sent_at1 = datetime.datetime.combine(
        test_date,
        datetime.time(hour=10),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    sent_at2 = datetime.datetime.combine(
        test_date_tomorrow,
        datetime.time(hour=14),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    
    message1 = Message(
        uuid=uuid4(),
        user_uuid=test_user.uuid,
        author="system",
        content="Message Today",
        sent_at=sent_at1,
    )
    message2 = Message(
        uuid=uuid4(),
        user_uuid=test_user.uuid,
        author="user",
        content="Message Tomorrow",
        sent_at=sent_at2,
    )
    await message_repo.put(message1)
    await message_repo.put(message2)
    
    # Search for specific date
    results = await message_repo.search_query(DateQuery(date=test_date))
    
    assert len(results) == 1
    assert results[0].content == "Message Today"


@pytest.mark.asyncio
async def test_user_isolation(message_repo, test_user, create_test_user, test_date):
    """Test that different users' messages are properly isolated."""
    sent_at = datetime.datetime.combine(
        test_date,
        datetime.time(hour=10),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    ).astimezone(UTC)
    
    message = Message(
        uuid=uuid4(),
        user_uuid=test_user.uuid,
        author="system",
        content="User1 Message",
        sent_at=sent_at,
    )
    await message_repo.put(message)
    
    # Create another user
    user2 = await create_test_user()
    message_repo2 = MessageRepository(user_uuid=user2.uuid)
    
    # User2 should not see user1's message
    with pytest.raises(exceptions.NotFoundError):
        await message_repo2.get(message.uuid)

