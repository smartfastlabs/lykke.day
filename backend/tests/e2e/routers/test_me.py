"""E2E tests for the /me endpoints."""

import pytest


@pytest.mark.asyncio
async def test_get_current_user_profile(authenticated_client):
    client, user = await authenticated_client()

    response = client.get("/me")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(user.id)
    assert data["email"] == user.email
    assert data["settings"]["template_defaults"] == user.settings.template_defaults


@pytest.mark.asyncio
async def test_update_current_user_profile(authenticated_client):
    client, user = await authenticated_client()

    phone_number = f"123-456-{user.id.hex[:6]}"
    payload = {
        "phone_number": phone_number,
        "status": "new-lead",
        "is_active": True,
        "is_superuser": False,
        "is_verified": True,
        "settings": {
          "template_defaults": ["m", "t", "w", "th", "f", "sa", "su"],
        },
    }

    response = client.put("/me", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["phone_number"] == phone_number
    assert data["status"] == "new-lead"
    assert data["is_verified"] is True
    assert data["settings"]["template_defaults"] == ["m", "t", "w", "th", "f", "sa", "su"]
    # email should remain unchanged
    assert data["email"] == user.email


@pytest.mark.asyncio
async def test_update_current_user_profile_requires_seven_defaults(authenticated_client):
    client, _ = await authenticated_client()

    payload = {
        "settings": {"template_defaults": ["only-one"]},
    }

    response = client.put("/me", json=payload)

    # Pydantic validation should fail with 422 Unprocessable Entity
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_current_user_persists_settings_and_updates_timestamp(
    authenticated_client,
):
    """Ensure settings changes persist to DB and updated_at is refreshed."""
    client, user = await authenticated_client()
    original_updated_at = user.updated_at

    phone_number = f"999-888-7777-{user.id.hex[:6]}"
    payload = {
        "phone_number": phone_number,
        "settings": {
            "template_defaults": ["x", "x", "x", "x", "x", "x", "x"],
        },
    }

    response = client.put("/me", json=payload)
    assert response.status_code == 200

    # Fetch fresh from repository to ensure persistence
    from lykke.infrastructure.repositories import UserRepository

    repo = UserRepository()
    updated_user = await repo.get(user.id)

    assert updated_user.settings.template_defaults == ["x"] * 7
    assert updated_user.phone_number == phone_number
    assert updated_user.updated_at is not None
    assert updated_user.updated_at != original_updated_at

