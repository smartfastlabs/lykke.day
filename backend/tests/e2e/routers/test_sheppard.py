"""E2E tests for sheppard router endpoints."""

import pytest
from dobles import expect

from lykke.core.utils import youtube


@pytest.mark.asyncio
async def test_stop_alarm(authenticated_client):
    """Test stopping alarm."""
    client, user = await authenticated_client()

    expect(youtube).kill_current_player.and_return(None)

    response = client.put("/sheppard/stop-alarm")

    assert response.status_code == 200

