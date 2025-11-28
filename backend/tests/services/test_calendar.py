import asyncio
from datetime import UTC, datetime, timedelta

import equals
import pytest
from dobles import expect

from planned.services import calendar_svc
from planned.services.calendar import auth_token_repo, google


@pytest.mark.asyncio
async def test_run():
    expect(calendar_svc).sync_all().once()

    task = asyncio.create_task(calendar_svc.run())
    await asyncio.sleep(0.1)

    calendar_svc.stop()
    await task


@pytest.mark.asyncio
async def test_sync(test_calendar):
    expect(calendar_svc).sync_google(
        test_calendar,
        lookback=equals.anything,
    ).and_return(
        ([1], [2]),
    )
    events, deleted_events = await calendar_svc.sync(test_calendar)
    assert events == [1]
    assert deleted_events == [2]
    assert test_calendar.last_sync_at


@pytest.mark.asyncio
async def test_google(
    test_calendar,
    test_auth_token,
    test_event,
    test_deleted_event,
):
    lookback: datetime = datetime.now(UTC) - timedelta(days=1)

    expect(google).load_calendar_events(
        test_calendar,
        lookback=lookback,
        token=test_auth_token,
    ).and_return(
        [
            test_event,
            test_deleted_event,
        ]
    )
    expect(auth_token_repo).get(
        test_calendar.auth_token_uuid,
    ).and_return(test_auth_token)

    (
        events,
        deleted_events,
    ) = await calendar_svc.sync_google(
        calendar=test_calendar,
        lookback=lookback,
    )

    assert events == [test_event]
    assert deleted_events == [test_deleted_event]
