"""E2E tests for sheppard router endpoints."""

import pytest
import pytest_asyncio


@pytest.mark.asyncio
async def test_prompts_endpoint(authenticated_client):
    """Test prompts endpoint."""
    client, user = authenticated_client
    
    response = client.put("/sheppard/prompts/test-prompt")
    
    assert response.status_code == 200
    data = response.text
    assert "placeholder" in data.lower() or "test-prompt" in data.lower()


@pytest.mark.asyncio
async def test_stop_alarm(authenticated_client):
    """Test stopping alarm."""
    client, user = authenticated_client
    
    response = client.put("/sheppard/stop-alarm")
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_start_alarm(authenticated_client):
    """Test starting alarm."""
    client, user = authenticated_client
    
    response = client.get("/sheppard/start-alarm")
    
    assert response.status_code == 200

