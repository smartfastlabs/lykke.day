import datetime
from zoneinfo import ZoneInfo

import pytest
import pytest_asyncio

from planned import objects, settings
from planned.infrastructure.repositories import EventRepository


@pytest_asyncio.fixture
async def test_event(test_date, test_user):
    from uuid import UUID
    repo = EventRepository(user_uuid=UUID(test_user.id))

    # Create event on test_date
    starts_at_today = datetime.datetime.combine(
        test_date,
        datetime.time(hour=2),
        tzinfo=ZoneInfo(settings.TIMEZONE),
    )
    event_today = objects.Event(
        user_uuid=UUID(test_user.id),
        name="Test Event",
        frequency="ONCE",
        calendar_id="test-calendar",
        platform_id="test-id",
        platform="testing",
        status="status",
        starts_at=starts_at_today,
    )
    return await repo.put(event_today)


@pytest.mark.asyncio
@pytest.mark.skip
async def test_get_today(test_client, test_date, test_event):
    result = test_client.get(
        "/events/today",
    )

    events = result.json()

    assert result.json() == [
        {
            "name": test_event.name,
            "platform_id": test_event.platform_id,
            "calendar_id": test_event.calendar_id,
            "platform": test_event.platform,
            "status": test_event.status,
            "starts_at": test_event.starts_at,
            "ends_at": test_event.ends_at,
            "created_at": test_event.created_at,
            "updated_at": test_event.updated_at,
            "date": test_event.date,
            "id": test_event.id,
            "frequency": test_event.frequency,
            "people": test_event.people,
            "actions": test_event.actions,
        }
    ]
