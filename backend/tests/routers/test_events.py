import equals
import pytest

from planned.utils.dates import get_current_date


@pytest.mark.asyncio
async def test_get_today(test_client, test_date):
    result = test_client.get(
        "/health",
        cookies={
            "session": "eyJsb2dnZWRfaW5fYXQiOiAiMjAyNS0xMS0zMCAxMjoyMzozNy4zMTQxMzctMDY6MDAifQ==.aSyNiQ.mTEp-AIEJCZubmsZMpWHT70rX_U",
        },
    )
    result = test_client.get(
        "/events/today",
        cookies={
            "session": "eyJsb2dnZWRfaW5fYXQiOiAiMjAyNS0xMS0zMCAxMjoyMzozNy4zMTQxMzctMDY6MDAifQ==.aSyNiQ.mTEp-AIEJCZubmsZMpWHT70rX_U",
        },
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
            "id": "google:gcal-family-004-family-thanksgiving-2025",
        }
    ]
