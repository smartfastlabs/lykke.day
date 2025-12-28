import pytest


@pytest.mark.asyncio
@pytest.mark.skip
async def test_get_todays(test_client, test_date, test_user):
    from uuid import UUID

    # Set user_uuid in session for the test client
    with test_client.session_transaction() as session:
        session["user_uuid"] = str(test_user.id)

    result = test_client.get("/tasks/today")
    assert result.json() == []
