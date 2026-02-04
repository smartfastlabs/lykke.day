"""E2E tests for calendar entry series router endpoints."""

from uuid import UUID, uuid4

import pytest

from lykke.domain.entities import (
    AuthTokenEntity,
    CalendarEntity,
    CalendarEntrySeriesEntity,
    UserEntity,
)
from lykke.domain.value_objects.task import EventCategory, TaskFrequency
from lykke.infrastructure.repositories import (
    AuthTokenRepository,
    CalendarEntrySeriesRepository,
    CalendarRepository,
)


async def create_calendar_for_user(user: UserEntity, calendar_id: UUID) -> CalendarEntity:
    auth_token_repo = AuthTokenRepository(user=user)
    auth_token = AuthTokenEntity(
        user_id=user.id,
        platform="google",
        token="test-token",
    )
    auth_token = await auth_token_repo.put(auth_token)

    calendar_repo = CalendarRepository(user=user)
    calendar = CalendarEntity(
        id=calendar_id,
        user_id=user.id,
        name="Test Calendar",
        auth_token_id=auth_token.id,
        platform_id=f"calendar-{calendar_id}",
        platform="google",
    )
    return await calendar_repo.put(calendar)


@pytest.mark.asyncio
async def test_list_calendar_entry_series(authenticated_client):
    client, user = await authenticated_client()
    repo = CalendarEntrySeriesRepository(user=user)
    calendar_id = uuid4()
    await create_calendar_for_user(user, calendar_id)
    series = CalendarEntrySeriesEntity(
        user_id=user.id,
        calendar_id=calendar_id,
        name="Morning Standup",
        platform_id="series-1",
        platform="google",
        frequency=TaskFrequency.WEEKLY,
        event_category=EventCategory.WORK,
    )
    await repo.put(series)

    response = client.post("/calendar-entry-series/", json={"limit": 50, "offset": 0})

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(item["id"] == str(series.id) for item in data["items"])


@pytest.mark.asyncio
async def test_get_and_update_calendar_entry_series(authenticated_client):
    client, user = await authenticated_client()
    repo = CalendarEntrySeriesRepository(user=user)
    calendar_id = uuid4()
    await create_calendar_for_user(user, calendar_id)
    series = CalendarEntrySeriesEntity(
        user_id=user.id,
        calendar_id=calendar_id,
        name="Weekly Planning",
        platform_id="series-2",
        platform="google",
        frequency=TaskFrequency.WEEKLY,
        event_category=EventCategory.PERSONAL,
    )
    series = await repo.put(series)

    get_response = client.get(f"/calendar-entry-series/{series.id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Weekly Planning"

    update_response = client.put(
        f"/calendar-entry-series/{series.id}",
        json={"name": "Weekly Review", "event_category": "WORK"},
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["name"] == "Weekly Review"
    assert updated["event_category"] == "WORK"

    stored = await repo.get(series.id)
    assert stored.name == "Weekly Review"
    assert stored.event_category == EventCategory.WORK


@pytest.mark.asyncio
async def test_search_calendar_entry_series_by_calendar(authenticated_client):
    client, user = await authenticated_client()
    repo = CalendarEntrySeriesRepository(user=user)
    target_calendar_id = uuid4()
    other_calendar_id = uuid4()

    await create_calendar_for_user(user, target_calendar_id)
    await create_calendar_for_user(user, other_calendar_id)

    matching_series = CalendarEntrySeriesEntity(
        user_id=user.id,
        calendar_id=target_calendar_id,
        name="Yoga Sessions",
        platform_id="series-3",
        platform="google",
        frequency=TaskFrequency.DAILY,
        event_category=EventCategory.PERSONAL,
    )
    other_series = CalendarEntrySeriesEntity(
        user_id=user.id,
        calendar_id=other_calendar_id,
        name="Non Matching",
        platform_id="series-4",
        platform="google",
        frequency=TaskFrequency.DAILY,
    )

    await repo.put(matching_series)
    await repo.put(other_series)

    response = client.post(
        "/calendar-entry-series/",
        json={
            "limit": 50,
            "offset": 0,
            "filters": {"calendar_id": str(target_calendar_id)},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert all(item["calendar_id"] == str(target_calendar_id) for item in data["items"])
