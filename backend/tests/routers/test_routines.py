import pytest
from planned.utils.dates import get_current_date


@pytest.mark.asyncio
async def test_get_todays_instances(test_client, test_date):
    result = test_client.get("/routines/instances/today")
    assert result.json() == []
