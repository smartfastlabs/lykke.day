"""E2E tests for google router endpoints."""

import pytest


@pytest.mark.asyncio
async def test_google_login_redirect(authenticated_client):
    """Test Google login redirects to authorization URL."""
    client, user = await authenticated_client()

    response = client.get("/google/login", follow_redirects=False)

    # Should redirect to Google OAuth
    assert response.status_code in [302, 307]
    assert "accounts.google.com" in response.headers.get("location", "")


@pytest.mark.asyncio
async def test_google_login_callback_missing_params(authenticated_client):
    """Test Google login callback with missing parameters."""
    client, user = await authenticated_client()

    response = client.get("/google/callback/login")

    # Should fail without state and code
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_google_login_callback_invalid_state(authenticated_client):
    """Test Google login callback with invalid state."""
    client, user = await authenticated_client()

    response = client.get(
        "/google/callback/login",
        params={"state": "invalid-state", "code": "test-code"},
    )

    # Should fail with invalid state
    assert response.status_code == 400

