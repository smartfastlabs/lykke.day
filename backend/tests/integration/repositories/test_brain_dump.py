"""Integration tests for BrainDumpRepository."""

from datetime import UTC, datetime
import pytest

from lykke.domain import value_objects
from lykke.domain.entities import BrainDumpEntity


@pytest.mark.asyncio
async def test_brain_dump_put_round_trip(brain_dump_repo, test_user, test_date):
    item = BrainDumpEntity(
        user_id=test_user.id,
        date=test_date,
        text="Remember to buy bread",
        status=value_objects.BrainDumpItemStatus.ACTIVE,
        type=value_objects.BrainDumpItemType.GENERAL,
        created_at=datetime.now(UTC),
    )
    await brain_dump_repo.put(item)

    retrieved = await brain_dump_repo.get(item.id)
    assert retrieved.text == item.text
    assert retrieved.status == value_objects.BrainDumpItemStatus.ACTIVE
    assert retrieved.type == value_objects.BrainDumpItemType.GENERAL
    assert retrieved.date == test_date


@pytest.mark.asyncio
async def test_brain_dump_search_by_date(
    brain_dump_repo, test_user, test_date, test_date_tomorrow
):
    item_today = BrainDumpEntity(
        user_id=test_user.id,
        date=test_date,
        text="Today item",
    )
    item_other = BrainDumpEntity(
        user_id=test_user.id,
        date=test_date_tomorrow,
        text="Other day",
    )
    await brain_dump_repo.put(item_today)
    await brain_dump_repo.put(item_other)

    results = await brain_dump_repo.search(value_objects.BrainDumpQuery(date=test_date))
    assert {item.id for item in results} == {item_today.id}
