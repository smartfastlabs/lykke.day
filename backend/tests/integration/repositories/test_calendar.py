"""Integration tests for CalendarRepository."""

from uuid import uuid4

import pytest

from planned.core.exceptions import exceptions
from planned.domain.entities import AuthToken, Calendar
from planned.infrastructure.repositories import CalendarRepository


@pytest.mark.asyncio
async def test_get(calendar_repo, test_user, auth_token_repo):
    """Test getting a calendar by ID."""
    # Create an auth token first (calendar depends on it)
    auth_token = AuthToken(
        id=uuid4(),
        user_id=test_user.id,
        platform="google",
        token="test_token",
        refresh_token="refresh_token",
    )
    auth_token = await auth_token_repo.put(auth_token)
    
    calendar = Calendar(
        user_id=test_user.id,
        name="Test Calendar",
        auth_token_id=str(auth_token.id),
        platform="google",
        platform_id="test-platform-id",
    )
    await calendar_repo.put(calendar)
    
    result = await calendar_repo.get(calendar.id)
    
    assert result.id == calendar.id
    assert result.name == "Test Calendar"
    assert result.user_id == test_user.id


@pytest.mark.asyncio
async def test_get_not_found(calendar_repo):
    """Test getting a non-existent calendar raises NotFoundError."""
    with pytest.raises(exceptions.NotFoundError):
        await calendar_repo.get(uuid4())


@pytest.mark.asyncio
async def test_put(calendar_repo, test_user, auth_token_repo):
    """Test creating a new calendar."""
    auth_token = await auth_token_repo.put(AuthToken(
        id=uuid4(),
        user_id=test_user.id,
        platform="google",
        token="test_token",
    ))
    
    calendar = Calendar(
        user_id=test_user.id,
        name="New Calendar",
        auth_token_id=str(auth_token.id),
        platform="google",
        platform_id="new-platform-id",
    )
    
    result = await calendar_repo.put(calendar)
    
    assert result.name == "New Calendar"
    assert result.platform == "google"


@pytest.mark.asyncio
async def test_all(calendar_repo, test_user, auth_token_repo):
    """Test getting all calendars."""
    auth_token = await auth_token_repo.put(AuthToken(
        id=uuid4(),
        user_id=test_user.id,
        platform="google",
        token="test_token",
    ))
    
    calendar1 = Calendar(
        user_id=test_user.id,
        name="Calendar 1",
        auth_token_id=str(auth_token.id),
        platform="google",
        platform_id="platform-id-1",
    )
    calendar2 = Calendar(
        user_id=test_user.id,
        name="Calendar 2",
        auth_token_id=str(auth_token.id),
        platform="google",
        platform_id="platform-id-2",
    )
    await calendar_repo.put(calendar1)
    await calendar_repo.put(calendar2)
    
    all_calendars = await calendar_repo.all()
    
    calendar_ids = [c.id for c in all_calendars]
    assert calendar1.id in calendar_ids
    assert calendar2.id in calendar_ids


@pytest.mark.asyncio
async def test_user_isolation(calendar_repo, test_user, create_test_user, auth_token_repo):
    """Test that different users' calendars are properly isolated."""
    auth_token = await auth_token_repo.put(AuthToken(
        id=uuid4(),
        user_id=test_user.id,
        platform="google",
        token="test_token",
    ))
    
    calendar = Calendar(
        user_id=test_user.id,
        name="User1 Calendar",
        auth_token_id=str(auth_token.id),
        platform="google",
        platform_id="platform-id",
    )
    await calendar_repo.put(calendar)
    
    # Create another user
    user2 = await create_test_user()
    calendar_repo2 = CalendarRepository(user_id=user2.id)
    
    # User2 should not see user1's calendar
    with pytest.raises(exceptions.NotFoundError):
        await calendar_repo2.get(calendar.id)

