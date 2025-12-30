"""E2E tests for calendars router endpoints."""

from uuid import uuid4

import pytest

from planned.domain.entities import AuthToken, Calendar
from planned.infrastructure.repositories import AuthTokenRepository, CalendarRepository


@pytest.mark.asyncio
async def test_list_calendars(authenticated_client):
    """Test listing calendars."""
    client, user = await authenticated_client()

    # Create an auth token first (calendar depends on it)
    auth_token_repo = AuthTokenRepository()
    auth_token = AuthToken(
        uuid=uuid4(),
        user_uuid=user.uuid,
        platform="google",
        token="test_token",
        refresh_token="refresh_token",
    )
    auth_token = await auth_token_repo.put(auth_token)

    # Create a calendar via repository
    calendar_repo = CalendarRepository(user_uuid=user.uuid)
    calendar = Calendar(
        user_uuid=user.uuid,
        name="Test Calendar",
        auth_token_uuid=auth_token.uuid,
        platform="google",
        platform_id="test-platform-id",
    )
    await calendar_repo.put(calendar)

    response = client.get("/calendars/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) > 0


@pytest.mark.asyncio
async def test_get_calendar(authenticated_client):
    """Test getting a single calendar by UUID."""
    client, user = await authenticated_client()

    # Create an auth token first
    auth_token_repo = AuthTokenRepository()
    auth_token = AuthToken(
        uuid=uuid4(),
        user_uuid=user.uuid,
        platform="google",
        token="test_token",
        refresh_token="refresh_token",
    )
    auth_token = await auth_token_repo.put(auth_token)

    # Create a calendar via repository
    calendar_repo = CalendarRepository(user_uuid=user.uuid)
    calendar = Calendar(
        user_uuid=user.uuid,
        name="Get Test Calendar",
        auth_token_uuid=auth_token.uuid,
        platform="google",
        platform_id="test-platform-id",
    )
    calendar = await calendar_repo.put(calendar)

    # Get the specific calendar
    response = client.get(f"/calendars/{calendar.uuid}")

    assert response.status_code == 200
    data = response.json()
    assert data["uuid"] == str(calendar.uuid)
    assert data["name"] == "Get Test Calendar"
    assert data["user_uuid"] == str(user.uuid)


@pytest.mark.asyncio
async def test_get_calendar_not_found(authenticated_client):
    """Test getting a non-existent calendar returns 404."""
    client, user = await authenticated_client()

    fake_uuid = uuid4()
    response = client.get(f"/calendars/{fake_uuid}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_calendar(authenticated_client):
    """Test creating a new calendar."""
    client, user = await authenticated_client()

    # Create an auth token first
    auth_token_repo = AuthTokenRepository()
    auth_token = AuthToken(
        uuid=uuid4(),
        user_uuid=user.uuid,
        platform="google",
        token="test_token",
        refresh_token="refresh_token",
    )
    auth_token = await auth_token_repo.put(auth_token)

    calendar_data = {
        "user_uuid": str(user.uuid),
        "name": "New Calendar",
        "auth_token_uuid": str(auth_token.uuid),
        "platform": "google",
        "platform_id": "new-platform-id",
    }

    response = client.post("/calendars/", json=calendar_data)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Calendar"
    assert data["user_uuid"] == str(user.uuid)
    assert data["platform"] == "google"
    assert data["platform_id"] == "new-platform-id"


@pytest.mark.asyncio
async def test_update_calendar(authenticated_client):
    """Test updating an existing calendar."""
    client, user = await authenticated_client()

    # Create an auth token first
    auth_token_repo = AuthTokenRepository()
    auth_token = AuthToken(
        uuid=uuid4(),
        user_uuid=user.uuid,
        platform="google",
        token="test_token",
        refresh_token="refresh_token",
    )
    auth_token = await auth_token_repo.put(auth_token)

    # Create a calendar
    calendar_data = {
        "user_uuid": str(user.uuid),
        "name": "Update Test Calendar",
        "auth_token_uuid": str(auth_token.uuid),
        "platform": "google",
        "platform_id": "update-test-id",
    }
    create_response = client.post("/calendars/", json=calendar_data)
    assert create_response.status_code == 200
    calendar_uuid = create_response.json()["uuid"]

    # Update the calendar
    update_data = {
        "user_uuid": str(user.uuid),
        "name": "Updated Calendar Name",
        "auth_token_uuid": str(auth_token.uuid),
        "platform": "google",
        "platform_id": "update-test-id",
    }
    response = client.put(f"/calendars/{calendar_uuid}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["uuid"] == calendar_uuid
    assert data["name"] == "Updated Calendar Name"


@pytest.mark.asyncio
async def test_update_calendar_not_found(authenticated_client):
    """Test updating a non-existent calendar returns 404."""
    client, user = await authenticated_client()

    # Create an auth token first
    auth_token_repo = AuthTokenRepository()
    auth_token = AuthToken(
        uuid=uuid4(),
        user_uuid=user.uuid,
        platform="google",
        token="test_token",
        refresh_token="refresh_token",
    )
    auth_token = await auth_token_repo.put(auth_token)

    fake_uuid = uuid4()
    update_data = {
        "user_uuid": str(user.uuid),
        "name": "Does Not Exist",
        "auth_token_uuid": str(auth_token.uuid),
        "platform": "google",
        "platform_id": "test-id",
    }
    response = client.put(f"/calendars/{fake_uuid}", json=update_data)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_calendar(authenticated_client):
    """Test deleting a calendar."""
    client, user = await authenticated_client()

    # Create an auth token first
    auth_token_repo = AuthTokenRepository()
    auth_token = AuthToken(
        uuid=uuid4(),
        user_uuid=user.uuid,
        platform="google",
        token="test_token",
        refresh_token="refresh_token",
    )
    auth_token = await auth_token_repo.put(auth_token)

    # Create a calendar
    calendar_data = {
        "user_uuid": str(user.uuid),
        "name": "Delete Test Calendar",
        "auth_token_uuid": str(auth_token.uuid),
        "platform": "google",
        "platform_id": "delete-test-id",
    }
    create_response = client.post("/calendars/", json=calendar_data)
    assert create_response.status_code == 200
    calendar_uuid = create_response.json()["uuid"]

    # Delete the calendar
    response = client.delete(f"/calendars/{calendar_uuid}")

    assert response.status_code == 200

    # Verify it's gone
    get_response = client.get(f"/calendars/{calendar_uuid}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_calendar_not_found(authenticated_client):
    """Test deleting a non-existent calendar returns 404."""
    client, user = await authenticated_client()

    fake_uuid = uuid4()
    response = client.delete(f"/calendars/{fake_uuid}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_calendars_pagination(authenticated_client):
    """Test pagination parameters for listing calendars."""
    client, user = await authenticated_client()

    # Create an auth token first
    auth_token_repo = AuthTokenRepository()
    auth_token = AuthToken(
        uuid=uuid4(),
        user_uuid=user.uuid,
        platform="google",
        token="test_token",
        refresh_token="refresh_token",
    )
    auth_token = await auth_token_repo.put(auth_token)

    # Create multiple calendars
    calendar_repo = CalendarRepository(user_uuid=user.uuid)
    for i in range(3):
        calendar = Calendar(
            user_uuid=user.uuid,
            name=f"Pagination Test {i}",
            auth_token_uuid=auth_token.uuid,
            platform="google",
            platform_id=f"pagination-test-{i}",
        )
        await calendar_repo.put(calendar)

    # Test pagination
    response = client.get("/calendars/?limit=2&offset=0")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 2
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert "has_next" in data
    assert "has_previous" in data
