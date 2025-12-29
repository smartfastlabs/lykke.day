"""E2E tests for auth router endpoints."""

from uuid import uuid4

import pytest
from passlib.context import CryptContext

from planned.domain.entities import User
from planned.domain.value_objects.user import UserSetting
from planned.infrastructure.repositories import UserRepository


@pytest.mark.asyncio
async def test_register(test_client):
    """Test user registration."""
    username = f"testuser_{uuid4().hex[:8]}"
    email = f"test-{uuid4()}@example.com"
    password = "password123"

    response = test_client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
            "confirm_password": password,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert "id" in data


@pytest.mark.asyncio
async def test_register_with_phone_number(test_client):
    """Test user registration with phone number."""
    username = f"testuser_{uuid4().hex[:8]}"
    email = f"test-{uuid4()}@example.com"
    password = "password123"
    phone_number = "+1234567890"

    response = test_client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "phone_number": phone_number,
            "password": password,
            "confirm_password": password,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(test_client):
    """Test registering with duplicate email fails."""
    username1 = f"testuser_{uuid4().hex[:8]}"
    username2 = f"testuser_{uuid4().hex[:8]}"
    email = f"test-{uuid4()}@example.com"
    password = "password123"

    # Create user first via register endpoint
    test_client.post(
        "/auth/register",
        json={
            "username": username1,
            "email": email,
            "password": password,
            "confirm_password": password,
        },
    )

    # Try to register again with same email
    response = test_client.post(
        "/auth/register",
        json={
            "username": username2,
            "email": email,
            "password": password,
            "confirm_password": password,
        },
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login(test_client):
    """Test user login."""
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user_repo = UserRepository()
    email = f"test-{uuid4()}@example.com"
    password = "password123"
    password_hash = pwd_context.hash(password)

    # Create user with hashed password
    username = f"testuser_{uuid4().hex[:8]}"
    user = User(
        id=str(uuid4()),
        username=username,
        email=email,
        password_hash=password_hash,
        settings=UserSetting(),
    )
    await user_repo.put(user)

    response = test_client.put(
        "/auth/login",
        json={"email": email, "password": password},
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_login_wrong_password(test_client):
    """Test login with wrong password fails."""
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user_repo = UserRepository()
    email = f"test-{uuid4()}@example.com"
    password_hash = pwd_context.hash("correct_password")

    username = f"testuser_{uuid4().hex[:8]}"
    user = User(
        id=str(uuid4()),
        username=username,
        email=email,
        password_hash=password_hash,
        settings=UserSetting(),
    )
    await user_repo.put(user)

    response = test_client.put(
        "/auth/login",
        json={"email": email, "password": "wrong_password"},
    )

    assert response.status_code == 403
