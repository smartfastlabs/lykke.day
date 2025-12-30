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
        id=uuid4(),
        email=email,
        hashed_password=pwd_context.hash(password),
        settings=UserSetting(),
    )
    allow(mock_user_repo).put.and_return(expected_user)

    service = AuthService(user_repo=mock_user_repo)
    result = await service.create_user(email=email, password=password)

    assert result.email == email
    assert result.id == expected_user.id
    # Verify password was hashed (not plain text)
    assert result.hashed_password != password
    assert pwd_context.verify(password, result.hashed_password)


@pytest.mark.asyncio
async def test_create_user_duplicate_email(mock_user_repo):
    """Test creating a user with duplicate email raises BadRequestError."""
    email = "existing@example.com"
    existing_user = User(
        id=uuid4(),
        email=email,
        hashed_password="hash",
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
    user_id = uuid4()
    expected_user = User(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=UserSetting(),
    )

    allow(mock_user_repo).get(user_id).and_return(expected_user)

    service = AuthService(user_repo=mock_user_repo)
    result = await service.get_user(user_id)

    assert result.id == user_id
    assert result.email == "test@example.com"


@pytest.mark.asyncio
async def test_authenticate_user_success(mock_user_repo):
    """Test successful user authentication."""
    email = "test@example.com"
    password = "password123"
    hashed_password = pwd_context.hash(password)

    user = User(
        id=uuid4(),
        email=email,
        hashed_password=hashed_password,
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
    hashed_password = pwd_context.hash("correct_password")

    user = User(
        id=uuid4(),
        email=email,
        hashed_password=hashed_password,
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
        id=uuid4(),
        email="test@example.com",
        hashed_password="old_hash",
        settings=UserSetting(),
    )
    new_password = "new_password123"

    # Mock put to return updated user
    allow(mock_user_repo).put.and_return(user)

    service = AuthService(user_repo=mock_user_repo)
    await service.set_password(user, new_password)

    # Verify password was hashed
    assert user.hashed_password != new_password
    assert pwd_context.verify(new_password, user.hashed_password)
