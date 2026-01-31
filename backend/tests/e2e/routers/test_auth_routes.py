"""E2E tests for auth router endpoints using fastapi-users."""

from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_register(test_client):
    """Test user registration via fastapi-users."""
    uid = uuid4()
    email = f"test-{uid}@example.com"
    password = "password123"
    phone_number = f"+1555{uid.hex[:7]}"

    response = test_client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "phone_number": phone_number,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == email
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(test_client):
    """Test registering with duplicate email fails."""
    uid = uuid4()
    email = f"test-{uid}@example.com"
    password = "password123"
    phone_number = f"+1555{uid.hex[:7]}"

    # Register first user
    test_client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "phone_number": phone_number,
        },
    )

    # Try to register again with same email (different phone)
    response = test_client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "phone_number": f"+1555{uuid4().hex[:7]}",
        },
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login(test_client):
    """Test user login via fastapi-users."""
    uid = uuid4()
    email = f"test-{uid}@example.com"
    password = "password123"
    phone_number = f"+1555{uid.hex[:7]}"

    # Register user first
    test_client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "phone_number": phone_number,
        },
    )

    # Login
    response = test_client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 204
    # Check that auth cookie is set
    assert "lykke_auth" in response.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(test_client):
    """Test login with wrong password fails."""
    uid = uuid4()
    email = f"test-{uid}@example.com"
    password = "correct_password"
    phone_number = f"+1555{uid.hex[:7]}"

    # Register user
    test_client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "phone_number": phone_number,
        },
    )

    # Try wrong password
    response = test_client.post(
        "/auth/login",
        data={"username": email, "password": "wrong_password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_logout(test_client):
    """Test user logout."""
    uid = uuid4()
    email = f"test-{uid}@example.com"
    password = "password123"
    phone_number = f"+1555{uid.hex[:7]}"

    # Register and login
    test_client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "phone_number": phone_number,
        },
    )
    test_client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    # Logout
    response = test_client.post("/auth/logout")

    assert response.status_code == 204
