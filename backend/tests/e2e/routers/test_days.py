"""E2E tests for days router endpoints."""

import datetime

import pytest


@pytest.mark.asyncio
async def test_get_context_today(authenticated_client, test_date):
    """Test getting context for today."""
    client, user = await authenticated_client()

    response = client.get("/days/today/context")

    assert response.status_code == 200
    data = response.json()
    assert "day" in data
    assert "tasks" in data
    assert "calendar_entries" in data
    assert data["day"]["date"] == test_date.isoformat()
    assert data["day"]["status"] == "SCHEDULED"
    assert data["day"]["scheduled_at"] is not None


