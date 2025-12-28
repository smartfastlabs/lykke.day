import equals
import pytest

from planned.infrastructure.utils.dates import get_current_date


@pytest.mark.asyncio
async def test_get_today(test_client, test_date, load_test_data):
    result = test_client.get(
        "/events/today",
    )

    assert result.json() == [
        {
            "name": "Sifleet Family Thanksgiving",
            "platform_id": "family-thanksgiving-2025",
            "calendar_id": "gcal-family-004",
            "platform": "google_calendar",
            "status": "confirmed",
            "starts_at": "2025-11-27T16:30:00Z",
            "ends_at": None,
            "created_at": "2025-11-05T11:15:00Z",
            "updated_at": "2025-11-05T11:15:00Z",
            "date": "2025-11-27",
            "id": "google:family-thanksgiving-2025",
            "frequency": "YEARLY",
            "people": [],
            "actions": [],
        }
    ]
