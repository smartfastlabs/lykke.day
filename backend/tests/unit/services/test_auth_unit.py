"""Unit tests for AuthService."""

from uuid import UUID, uuid4

import pytest
from dobles import allow
from passlib.context import CryptContext

from planned.application.services import AuthService
from planned.core.exceptions import exceptions
from planned.domain.entities import User
from planned.domain.value_objects.user import UserSetting

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.mark.asyncio
async def test_create_user(mock_user_repo):
    """Test creating a new user."""
    email = "test@example.com"
    password = "password123"

    # Mock get_by_email to return None (user doesn't exist)
    allow(mock_user_repo).get_by_email(email).and_return(None)

    # Mock put to return the created user
    expected_user = User(
        uuid=uuid4(),
        email=email,
        password_hash=pwd_context.hash(password),
        settings=UserSetting(),
    )
    allow(mock_user_repo).put.and_return(expected_user)

    service = AuthService(user_repo=mock_user_repo)
    result = await service.create_user(email=email, password=password)

    assert result.email == email
    assert result.uuid == expected_user.uuid
    # Verify password was hashed (not plain text)
    assert result.password_hash != password
    assert pwd_context.verify(password, result.password_hash)


@pytest.mark.asyncio
async def test_create_user_duplicate_email(mock_user_repo):
    """Test creating a user with duplicate email raises BadRequestError."""
    email = "existing@example.com"
    existing_user = User(
        uuid=uuid4(),
        email=email,
        password_hash="hash",
        settings=UserSetting(),
    )

    # Mock get_by_email to return existing user
    allow(mock_user_repo).get_by_email(email).and_return(existing_user)

    service = AuthService(user_repo=mock_user_repo)

    with pytest.raises(exceptions.BadRequestError):
        await service.create_user(email=email, password="password123")


@pytest.mark.asyncio
async def test_get_user(mock_user_repo):
    """Test getting a user by UUID."""
    user_uuid = uuid4()
    expected_user = User(
        uuid=user_uuid,
        email="test@example.com",
        password_hash="hash",
        settings=UserSetting(),
    )

    allow(mock_user_repo).get(user_uuid).and_return(expected_user)

    service = AuthService(user_repo=mock_user_repo)
    result = await service.get_user(user_uuid)

    assert result.uuid == user_uuid
    assert result.email == "test@example.com"


@pytest.mark.asyncio
async def test_authenticate_user_success(mock_user_repo):
    """Test successful user authentication."""
    email = "test@example.com"
    password = "password123"
    password_hash = pwd_context.hash(password)

    user = User(
        uuid=uuid4(),
        email=email,
        password_hash=password_hash,
        settings=UserSetting(),
    )

    allow(mock_user_repo).get_by_email(email).and_return(user)

    service = AuthService(user_repo=mock_user_repo)
    result = await service.authenticate_user(email, password)

    assert result is not None
    assert result.email == email


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(mock_user_repo):
    """Test authentication with wrong password returns None."""
    email = "test@example.com"
    password_hash = pwd_context.hash("correct_password")

    user = User(
        uuid=uuid4(),
        email=email,
        password_hash=password_hash,
        settings=UserSetting(),
    )

    allow(mock_user_repo).get_by_email(email).and_return(user)

    service = AuthService(user_repo=mock_user_repo)
    result = await service.authenticate_user(email, "wrong_password")

    assert result is None


@pytest.mark.asyncio
async def test_authenticate_user_not_found(mock_user_repo):
    """Test authentication with non-existent user returns None."""
    email = "nonexistent@example.com"

    allow(mock_user_repo).get_by_email(email).and_return(None)

    service = AuthService(user_repo=mock_user_repo)
    result = await service.authenticate_user(email, "password")

    assert result is None


@pytest.mark.asyncio
async def test_set_password(mock_user_repo):
    """Test setting a new password for a user."""
    user = User(
        uuid=uuid4(),
        email="test@example.com",
        password_hash="old_hash",
        settings=UserSetting(),
    )
    new_password = "new_password123"

    # Mock put to return updated user
    allow(mock_user_repo).put.and_return(user)

    service = AuthService(user_repo=mock_user_repo)
    await service.set_password(user, new_password)

    # Verify password was hashed
    assert user.password_hash != new_password
    assert pwd_context.verify(new_password, user.password_hash)
