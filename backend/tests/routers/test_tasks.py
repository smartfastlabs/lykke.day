import pytest


@pytest.mark.asyncio
async def test_get_todays(test_client, test_date, clear_repos):
    result = test_client.get("/tasks/today")
    assert result.json() == []
