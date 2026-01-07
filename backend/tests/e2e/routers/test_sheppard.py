"""E2E tests for sheppard router endpoints."""

import pytest
from dobles import expect

from lykke.core.utils import youtube


@pytest.mark.asyncio
async def test_prompts_endpoint(authenticated_client):
    """Test prompts endpoint."""
    client, user = await authenticated_client()

    response = client.put("/sheppard/prompts/test-prompt")

    assert response.status_code == 200
    data = response.text
    assert "placeholder" in data.lower() or "test-prompt" in data.lower()


@pytest.mark.asyncio
async def test_stop_alarm(authenticated_client):
    """Test stopping alarm."""
    client, user = await authenticated_client()

    expect(youtube).kill_current_player.and_return(None)

    response = client.put("/sheppard/stop-alarm")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_start_alarm(authenticated_client):
    """Test starting alarm."""
    client, user = await authenticated_client()

    expect(youtube).play_audio("https://www.youtube.com/watch?v=Gcv7re2dEVg").and_return(None)

    response = client.get("/sheppard/start-alarm")

    assert response.status_code == 200

