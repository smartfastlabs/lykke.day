"""E2E tests for days router endpoints."""

import datetime
from zoneinfo import ZoneInfo

import pytest

from planned.core.config import settings
from planned.domain.value_objects.day import DayStatus


@pytest.mark.asyncio
async def test_schedule_today(authenticated_client, test_date):
    """Test scheduling today."""
    client, user = await authenticated_client()

    response = client.put("/days/today/schedule")

    assert response.status_code == 200
    data = response.json()
    assert "day" in data
    assert data["day"]["date"] == test_date.isoformat()


@pytest.mark.asyncio
async def test_get_context_today(authenticated_client, test_date):
    """Test getting context for today."""
    client, user = await authenticated_client()

    response = client.get("/days/today/context")

    assert response.status_code == 200
    data = response.json()
    assert "day" in data
    assert "tasks" in data
    assert "events" in data
    assert "messages" in data
    assert data["day"]["date"] == test_date.isoformat()


@pytest.mark.asyncio
async def test_get_context_tomorrow(authenticated_client, test_date_tomorrow):
    """Test getting context for tomorrow."""
    client, user = await authenticated_client()

    response = client.get("/days/tomorrow/context")

    assert response.status_code == 200
    data = response.json()
    assert "day" in data
    assert data["day"]["date"] == test_date_tomorrow.isoformat()


@pytest.mark.asyncio
async def test_get_context_specific_date(authenticated_client):
    """Test getting context for a specific date."""
    client, user = await authenticated_client()

    date = datetime.date(2024, 6, 15)
    response = client.get(f"/days/{date.isoformat()}/context")

    assert response.status_code == 200
    data = response.json()
    assert "day" in data
    assert data["day"]["date"] == date.isoformat()


@pytest.mark.asyncio
async def test_get_context_invalid_date_string(authenticated_client):
    """Test getting context with invalid date string."""
    client, user = await authenticated_client()

    response = client.get("/days/invalid-date/context")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_day(authenticated_client, test_date):
    """Test updating a day."""
    client, user = await authenticated_client()

    # First schedule the day
    client.put("/days/today/schedule")

    # Update the day status
    response = client.patch(
        f"/days/{test_date.isoformat()}",
        json={"status": "COMPLETE"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETE"


@pytest.mark.asyncio
async def test_update_day_template(authenticated_client, test_date):
    """Test updating a day's template."""
    client, user = await authenticated_client()

    # First schedule the day
    client.put("/days/today/schedule")

    # Update the template
    response = client.patch(
        f"/days/{test_date.isoformat()}",
        json={"template_id": "gym"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["template_id"] == "gym"


@pytest.mark.asyncio
async def test_get_templates(authenticated_client):
    """Test getting day templates."""
    client, user = await authenticated_client()

    response = client.get("/days/templates")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should have at least the default template
    assert len(data) > 0
