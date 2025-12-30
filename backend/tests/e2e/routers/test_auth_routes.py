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
    email = f"test-{uuid4()}@example.com"
    password = "password123"

    response = test_client.post(
        "/auth/register",
        json={
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
    email = f"test-{uuid4()}@example.com"
    password = "password123"
    phone_number = "+1234567890"

    response = test_client.post(
        "/auth/register",
        json={
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
    email = f"test-{uuid4()}@example.com"
    password = "password123"

    # Create user first via register endpoint
    test_client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "confirm_password": password,
        },
    )

    # Try to register again with same email
    response = test_client.post(
        "/auth/register",
        json={
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
    hashed_password = pwd_context.hash(password)

    # Create user with hashed password
    user = User(
        uuid=uuid4(),
        email=email,
        hashed_password=hashed_password,
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
    hashed_password = pwd_context.hash("correct_password")

    user = User(
        uuid=uuid4(),
        email=email,
        hashed_password=hashed_password,
        settings=UserSetting(),
    )
    await user_repo.put(user)

    response = test_client.put(
        "/auth/login",
        json={"email": email, "password": "wrong_password"},
    )

    assert response.status_code == 403
