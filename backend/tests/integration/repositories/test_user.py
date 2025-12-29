"""Integration tests for UserRepository."""

from uuid import uuid4

import pytest

from planned.core.exceptions import exceptions
from planned.domain.entities import User
from planned.domain.value_objects.user import UserSetting


@pytest.mark.asyncio
async def test_get(user_repo, create_test_user):
    """Test getting a user by ID."""
    # Create a user
    user = await create_test_user()
    
    # Get it back
    result = await user_repo.get(user.id)
    
    assert result.id == user.id
    assert result.email == user.email
    assert result.password_hash == user.password_hash


@pytest.mark.asyncio
async def test_get_not_found(user_repo):
    """Test getting a non-existent user raises NotFoundError."""
    with pytest.raises(exceptions.NotFoundError):
        await user_repo.get(str(uuid4()))


@pytest.mark.asyncio
async def test_put(user_repo):
    """Test creating a new user."""
    user = User(
        id=str(uuid4()),
        username=f"testuser_{uuid4().hex[:8]}",
        email=f"test-{uuid4()}@example.com",
        password_hash="hashed_password",
        settings=UserSetting(),
    )
    
    result = await user_repo.put(user)
    
    assert result.id == user.id
    assert result.email == user.email
    assert result.password_hash == user.password_hash


@pytest.mark.asyncio
async def test_put_update(user_repo, create_test_user):
    """Test updating an existing user."""
    user = await create_test_user()
    
    # Update the user with a new unique email
    user.email = f"updated-{uuid4()}@example.com"
    result = await user_repo.put(user)
    
    assert result.email == user.email
    
    # Verify it was saved
    retrieved = await user_repo.get(user.id)
    assert retrieved.email == user.email


@pytest.mark.asyncio
async def test_get_by_email(user_repo, create_test_user):
    """Test getting a user by email."""
    email = f"specific-{uuid4()}@example.com"
    user = await create_test_user(email=email)
    
    result = await user_repo.get_by_email(email)
    
    assert result is not None
    assert result.id == user.id
    assert result.email == email


@pytest.mark.asyncio
async def test_get_by_email_not_found(user_repo):
    """Test getting a user by non-existent email returns None."""
    result = await user_repo.get_by_email("nonexistent@example.com")
    assert result is None


@pytest.mark.asyncio
async def test_all(user_repo, create_test_user):
    """Test getting all users."""
    # Create multiple users
    user1 = await create_test_user()
    user2 = await create_test_user()
    
    # Get all users
    all_users = await user_repo.all()
    
    # Should have at least our two users
    user_ids = [u.id for u in all_users]
    assert user1.id in user_ids
    assert user2.id in user_ids


@pytest.mark.asyncio
async def test_user_isolation(user_repo, create_test_user):
    """Test that different users are properly isolated."""
    user1 = await create_test_user(email=f"user1-{uuid4()}@example.com")
    user2 = await create_test_user(email=f"user2-{uuid4()}@example.com")
    
    # Each user should be retrievable independently
    retrieved1 = await user_repo.get(user1.id)
    retrieved2 = await user_repo.get(user2.id)
    
    assert retrieved1.id == user1.id
    assert retrieved1.email == user1.email
    assert retrieved2.id == user2.id
    assert retrieved2.email == user2.email
    assert retrieved1.id != retrieved2.id


@pytest.mark.asyncio
async def test_user_with_custom_settings(user_repo):
    """Test creating a user with custom settings."""
    settings = UserSetting(
        template_defaults=["custom", "custom", "custom", "custom", "custom", "custom", "custom"],
    )
    user = User(
        id=str(uuid4()),
        username=f"testuser_{uuid4().hex[:8]}",
        email=f"test-{uuid4()}@example.com",
        password_hash="hash",
        settings=settings,
    )
    
    result = await user_repo.put(user)
    
    assert result.settings.template_defaults == ["custom"] * 7
    
    # Verify persistence
    retrieved = await user_repo.get(user.id)
    assert retrieved.settings.template_defaults == ["custom"] * 7

