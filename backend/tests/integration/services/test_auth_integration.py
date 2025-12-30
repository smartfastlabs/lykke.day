"""Integration tests for AuthService with real UserRepository."""

from uuid import uuid4

import pytest
from passlib.context import CryptContext

from planned.application.services import AuthService

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.mark.asyncio
async def test_create_user(user_repo):
    """Test creating a new user with real repository."""
    service = AuthService(user_repo=user_repo)
    
    email = f"test-{uuid4()}@example.com"
    password = "password123"
    
    user = await service.create_user(email, password)
    
    assert user.email == email
    assert user.hashed_password != password
    assert pwd_context.verify(password, user.hashed_password)


@pytest.mark.asyncio
async def test_authenticate_user_success(user_repo):
    """Test successful authentication with real repository."""
    service = AuthService(user_repo=user_repo)
    
    email = f"test-{uuid4()}@example.com"
    password = "password123"
    
    # Create user
    user = await service.create_user(email, password)
    
    # Authenticate
    authenticated = await service.authenticate_user(email, password)
    
    assert authenticated is not None
    assert authenticated.id == user.id


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(user_repo):
    """Test authentication with wrong password."""
    service = AuthService(user_repo=user_repo)
    
    email = f"test-{uuid4()}@example.com"
    
    # Create user
    await service.create_user(email, "correct_password")
    
    # Try wrong password
    authenticated = await service.authenticate_user(email, "wrong_password")
    
    assert authenticated is None

