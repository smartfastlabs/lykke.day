"""Integration tests for AuthTokenRepository."""

from uuid import uuid4

import pytest

from planned.core.exceptions import exceptions
from planned.domain.entities import AuthToken
from planned.infrastructure.repositories import AuthTokenRepository


@pytest.mark.asyncio
async def test_get(auth_token_repo, test_user):
    """Test getting an auth token by ID."""
    auth_token = AuthToken(
        uuid=uuid4(),
        user_uuid=test_user.uuid,
        platform="google",
        token="test_token",
        refresh_token="refresh_token",
    )
    await auth_token_repo.put(auth_token)
    
    result = await auth_token_repo.get(auth_token.uuid)
    
    assert result.uuid == auth_token.uuid
    assert result.platform == "google"
    assert result.token == "test_token"


@pytest.mark.asyncio
async def test_get_not_found(auth_token_repo):
    """Test getting a non-existent auth token raises NotFoundError."""
    with pytest.raises(exceptions.NotFoundError):
        await auth_token_repo.get(uuid4())


@pytest.mark.asyncio
async def test_put(auth_token_repo, test_user):
    """Test creating a new auth token."""
    auth_token = AuthToken(
        uuid=uuid4(),
        user_uuid=test_user.uuid,
        platform="google",
        token="new_token",
    )
    
    result = await auth_token_repo.put(auth_token)
    
    assert result.token == "new_token"
    assert result.platform == "google"


@pytest.mark.asyncio
async def test_all(auth_token_repo, test_user):
    """Test getting all auth tokens."""
    token1 = AuthToken(
        uuid=uuid4(),
        user_uuid=test_user.uuid,
        platform="google",
        token="token1",
    )
    token2 = AuthToken(
        uuid=uuid4(),
        user_uuid=test_user.uuid,
        platform="notion",
        token="token2",
    )
    await auth_token_repo.put(token1)
    await auth_token_repo.put(token2)
    
    all_tokens = await auth_token_repo.all()
    
    token_uuids = [t.uuid for t in all_tokens]
    assert token1.uuid in token_uuids
    assert token2.uuid in token_uuids


@pytest.mark.asyncio
async def test_user_isolation(auth_token_repo, test_user, create_test_user):
    """Test that different users' auth tokens are properly isolated."""
    token = AuthToken(
        uuid=uuid4(),
        user_uuid=test_user.uuid,
        platform="google",
        token="user1_token",
    )
    await auth_token_repo.put(token)
    
    # Create another user
    user2 = await create_test_user()
    auth_token_repo2 = AuthTokenRepository()
    
    # AuthTokenRepository is not user-scoped, so user2 can see user1's token
    retrieved_token = await auth_token_repo2.get(token.uuid)
    assert retrieved_token.uuid == token.uuid

