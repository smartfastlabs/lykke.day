"""E2E tests for auth router endpoints."""

import pytest
import pytest_asyncio


@pytest.mark.asyncio
async def test_register(test_client):
    """Test user registration."""
    from uuid import uuid4
    
    email = f"test-{uuid4()}@example.com"
    password = "password123"
    
    response = test_client.post(
        "/api/auth/register",
        json={"email": email, "password": password},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(test_client):
    """Test registering with duplicate email fails."""
    email = f"test-{uuid4()}@example.com"
    password = "password123"
    
    # Create user first via register endpoint
    from uuid import uuid4
    
    test_client.post(
        "/api/auth/register",
        json={"email": email, "password": password},
    )
    user = User(
        id=str(uuid4()),
        email=email,
        password_hash=password_hash,
        settings=UserSetting(),
    )
    
    # Try to register again
    response = test_client.post(
        "/api/auth/register",
        json={"email": email, "password": password},
    )
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login(test_client):
    """Test user login."""
    from passlib.context import CryptContext
    from planned.infrastructure.repositories import UserRepository
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user_repo = UserRepository()
    email = f"test-{uuid4()}@example.com"
    password = "password123"
    password_hash = pwd_context.hash(password)
    
    # Create user with hashed password
    from planned.domain.entities import User
    from planned.domain.value_objects.user import UserSetting
    user = User(
        id=str(uuid4()),
        email=email,
        password_hash=password_hash,
        settings=UserSetting(),
    )
    await user_repo.put(user)
    
    response = test_client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_login_wrong_password(test_client):
    """Test login with wrong password fails."""
    from passlib.context import CryptContext
    from uuid import uuid4
    from planned.infrastructure.repositories import UserRepository
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user_repo = UserRepository()
    email = f"test-{uuid4()}@example.com"
    password_hash = pwd_context.hash("correct_password")
    
    from planned.domain.entities import User
    from planned.domain.value_objects.user import UserSetting
    user = User(
        id=str(uuid4()),
        email=email,
        password_hash=password_hash,
        settings=UserSetting(),
    )
    await user_repo.put(user)
    
    response = test_client.post(
        "/api/auth/login",
        json={"email": email, "password": "wrong_password"},
    )
    
    assert response.status_code == 401

