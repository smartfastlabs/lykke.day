"""E2E tests for calendars router endpoints."""

from uuid import uuid4

import pytest

from lykke.domain.entities import AuthTokenEntity, CalendarEntity
from lykke.infrastructure.repositories import AuthTokenRepository, CalendarRepository


@pytest.mark.asyncio
async def test_list_calendars(authenticated_client):
    """Test listing calendars."""
    client, user = await authenticated_client()

    # Create an auth token first (calendar depends on it)
    auth_token_repo = AuthTokenRepository(user=user)
    auth_token = AuthTokenEntity(
        id=uuid4(),
        user_id=user.id,
        platform="google",
        token="test_token",
        refresh_token="refresh_token",
    )
    auth_token = await auth_token_repo.put(auth_token)

    # Create a calendar via repository
    calendar_repo = CalendarRepository(user=user)
    calendar = CalendarEntity(
        user_id=user.id,
        name="Test Calendar",
        auth_token_id=auth_token.id,
        platform="google",
        platform_id="test-platform-id",
    )
    await calendar_repo.put(calendar)

    response = client.post("/calendars/", json={"limit": 50, "offset": 0})

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
    auth_token_repo = AuthTokenRepository(user=user)
    auth_token = AuthTokenEntity(
        id=uuid4(),
        user_id=user.id,
        platform="google",
        token="test_token",
        refresh_token="refresh_token",
    )
    auth_token = await auth_token_repo.put(auth_token)

    # Create a calendar via repository
    calendar_repo = CalendarRepository(user=user)
    calendar = CalendarEntity(
        user_id=user.id,
        name="Get Test Calendar",
        auth_token_id=auth_token.id,
        platform="google",
        platform_id="test-platform-id",
    )
    calendar = await calendar_repo.put(calendar)

    # Get the specific calendar
    response = client.get(f"/calendars/{calendar.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(calendar.id)
    assert data["name"] == "Get Test Calendar"
    assert data["user_id"] == str(user.id)


@pytest.mark.asyncio
async def test_get_calendar_not_found(authenticated_client):
    """Test getting a non-existent calendar returns 404."""
    client, _user = await authenticated_client()

    fake_id = uuid4()
    response = client.get(f"/calendars/{fake_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_calendar(authenticated_client):
    """Test creating a new calendar."""
    client, user = await authenticated_client()

    # Create an auth token first
    auth_token_repo = AuthTokenRepository(user=user)
    auth_token = AuthTokenEntity(
        id=uuid4(),
        user_id=user.id,
        platform="google",
        token="test_token",
        refresh_token="refresh_token",
    )
    auth_token = await auth_token_repo.put(auth_token)

    calendar_data = {
        "user_id": str(user.id),
        "name": "New Calendar",
        "auth_token_id": str(auth_token.id),
        "platform": "google",
        "platform_id": "new-platform-id",
    }

    response = client.post("/calendars/create", json=calendar_data)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Calendar"
    assert data["user_id"] == str(user.id)
    assert data["platform"] == "google"
    assert data["platform_id"] == "new-platform-id"


@pytest.mark.asyncio
async def test_update_calendar(authenticated_client):
    """Test updating an existing calendar."""
    client, user = await authenticated_client()

    # Create an auth token first
    auth_token_repo = AuthTokenRepository(user=user)
    auth_token = AuthTokenEntity(
        id=uuid4(),
        user_id=user.id,
        platform="google",
        token="test_token",
        refresh_token="refresh_token",
    )
    auth_token = await auth_token_repo.put(auth_token)

    # Create a calendar
    calendar_data = {
        "user_id": str(user.id),
        "name": "Update Test Calendar",
        "auth_token_id": str(auth_token.id),
        "platform": "google",
        "platform_id": "update-test-id",
    }
    create_response = client.post("/calendars/create", json=calendar_data)
    assert create_response.status_code == 200
    calendar_id = create_response.json()["id"]

    # Update the calendar
    update_data = {
        "user_id": str(user.id),
        "name": "Updated Calendar Name",
        "auth_token_id": str(auth_token.id),
        "platform": "google",
        "platform_id": "update-test-id",
    }
    response = client.put(f"/calendars/{calendar_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == calendar_id
    assert data["name"] == "Updated Calendar Name"


@pytest.mark.asyncio
async def test_update_calendar_not_found(authenticated_client):
    """Test updating a non-existent calendar returns 404."""
    client, user = await authenticated_client()

    # Create an auth token first
    auth_token_repo = AuthTokenRepository(user=user)
    auth_token = AuthTokenEntity(
        id=uuid4(),
        user_id=user.id,
        platform="google",
        token="test_token",
        refresh_token="refresh_token",
    )
    auth_token = await auth_token_repo.put(auth_token)

    fake_id = uuid4()
    update_data = {
        "user_id": str(user.id),
        "name": "Does Not Exist",
        "auth_token_id": str(auth_token.id),
        "platform": "google",
        "platform_id": "test-id",
    }
    response = client.put(f"/calendars/{fake_id}", json=update_data)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_calendar(authenticated_client):
    """Test deleting a calendar."""
    client, user = await authenticated_client()

    # Create an auth token first
    auth_token_repo = AuthTokenRepository(user=user)
    auth_token = AuthTokenEntity(
        id=uuid4(),
        user_id=user.id,
        platform="google",
        token="test_token",
        refresh_token="refresh_token",
    )
    auth_token = await auth_token_repo.put(auth_token)

    # Create a calendar
    calendar_data = {
        "user_id": str(user.id),
        "name": "Delete Test Calendar",
        "auth_token_id": str(auth_token.id),
        "platform": "google",
        "platform_id": "delete-test-id",
    }
    create_response = client.post("/calendars/create", json=calendar_data)
    assert create_response.status_code == 200
    calendar_id = create_response.json()["id"]

    # Delete the calendar
    response = client.delete(f"/calendars/{calendar_id}")

    assert response.status_code == 200

    # Verify it's gone
    get_response = client.get(f"/calendars/{calendar_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_calendar_not_found(authenticated_client):
    """Test deleting a non-existent calendar returns 404."""
    client, _user = await authenticated_client()

    fake_id = uuid4()
    response = client.delete(f"/calendars/{fake_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_calendars_pagination(authenticated_client):
    """Test pagination parameters for listing calendars."""
    client, user = await authenticated_client()

    # Create an auth token first
    auth_token_repo = AuthTokenRepository(user=user)
    auth_token = AuthTokenEntity(
        id=uuid4(),
        user_id=user.id,
        platform="google",
        token="test_token",
        refresh_token="refresh_token",
    )
    auth_token = await auth_token_repo.put(auth_token)

    # Create multiple calendars
    calendar_repo = CalendarRepository(user=user)
    for i in range(3):
        calendar = CalendarEntity(
            user_id=user.id,
            name=f"Pagination Test {i}",
            auth_token_id=auth_token.id,
            platform="google",
            platform_id=f"pagination-test-{i}",
        )
        await calendar_repo.put(calendar)

    # Test pagination
    response = client.post("/calendars/", json={"limit": 2, "offset": 0})

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 2
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert "has_next" in data
    assert "has_previous" in data
