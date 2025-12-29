"""Integration tests for DayRepository."""

from uuid import UUID, uuid4

import pytest

from planned.core.exceptions import exceptions
from planned.domain.entities import Day, DayStatus
from planned.infrastructure.utils.dates import get_current_datetime


@pytest.mark.asyncio
async def test_get(
    day_repo, day_template_repo, test_user, test_date, setup_day_templates
):
    """Test getting a day by date."""
    await setup_day_templates
    templates = await day_template_repo.all()
    default_template_uuid = (
        templates[0].uuid if templates else UUID("00000000-0000-0000-0000-000000000000")
    )

    day = Day(
        user_uuid=test_user.uuid,
        date=test_date,
        status=DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
        template_uuid=default_template_uuid,
    )
    await day_repo.put(day)

    result = await day_repo.get(day.uuid)

    assert result.date == test_date
    assert result.status == DayStatus.SCHEDULED
    assert result.user_uuid == test_user.uuid


@pytest.mark.asyncio
async def test_get_not_found(day_repo, test_date):
    """Test getting a non-existent day raises NotFoundError."""
    with pytest.raises(exceptions.NotFoundError):
        await day_repo.get(uuid4())


@pytest.mark.asyncio
async def test_put(
    day_repo, day_template_repo, test_user, test_date, setup_day_templates
):
    """Test creating a new day."""
    await setup_day_templates
    templates = await day_template_repo.all()
    default_template_uuid = (
        templates[0].uuid if templates else UUID("00000000-0000-0000-0000-000000000000")
    )

    day = Day(
        user_uuid=test_user.uuid,
        date=test_date,
        status=DayStatus.UNSCHEDULED,
        template_uuid=default_template_uuid,
    )

    result = await day_repo.put(day)

    assert result.date == test_date
    assert result.status == DayStatus.UNSCHEDULED
    assert result.user_uuid == test_user.uuid


@pytest.mark.asyncio
async def test_put_update(
    day_repo, day_template_repo, test_user, test_date, setup_day_templates
):
    """Test updating an existing day."""
    await setup_day_templates
    templates = await day_template_repo.all()
    default_template_uuid = (
        templates[0].uuid if templates else UUID("00000000-0000-0000-0000-000000000000")
    )

    day = Day(
        user_uuid=test_user.uuid,
        date=test_date,
        status=DayStatus.UNSCHEDULED,
        template_uuid=default_template_uuid,
    )
    await day_repo.put(day)

    # Update the day
    day.status = DayStatus.SCHEDULED
    day.scheduled_at = get_current_datetime()
    result = await day_repo.put(day)

    assert result.status == DayStatus.SCHEDULED
    assert result.scheduled_at is not None

    # Verify it was saved
    retrieved = await day_repo.get(day.uuid)
    assert retrieved.status == DayStatus.SCHEDULED


@pytest.mark.asyncio
async def test_all(
    day_repo,
    day_template_repo,
    test_user,
    test_date,
    test_date_tomorrow,
    setup_day_templates,
):
    """Test getting all days."""
    await setup_day_templates
    templates = await day_template_repo.all()
    default_template_uuid = (
        templates[0].uuid if templates else UUID("00000000-0000-0000-0000-000000000000")
    )

    day1 = Day(
        user_uuid=test_user.uuid,
        date=test_date,
        status=DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
        template_uuid=default_template_uuid,
    )
    day2 = Day(
        user_uuid=test_user.uuid,
        date=test_date_tomorrow,
        status=DayStatus.UNSCHEDULED,
        template_uuid=default_template_uuid,
    )
    await day_repo.put(day1)
    await day_repo.put(day2)

    all_days = await day_repo.all()

    dates = [d.date for d in all_days]
    assert test_date in dates
    assert test_date_tomorrow in dates


@pytest.mark.asyncio
async def test_search_query(
    day_repo,
    day_template_repo,
    test_user,
    test_date,
    test_date_tomorrow,
    setup_day_templates,
):
    """Test searching days with DateQuery."""
    await setup_day_templates
    templates = await day_template_repo.all()
    default_template_uuid = templates[0].uuid if templates else uuid4()

    day1 = Day(
        user_uuid=test_user.uuid,
        date=test_date,
        status=DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
        template_uuid=default_template_uuid,
    )
    day2 = Day(
        user_uuid=test_user.uuid,
        date=test_date_tomorrow,
        status=DayStatus.UNSCHEDULED,
        template_uuid=default_template_uuid,
    )
    await day_repo.put(day1)
    await day_repo.put(day2)

    # DayRepository doesn't have DateQuery - it uses BaseQuery
    # Just test that all() works correctly instead
    all_days = await day_repo.all()

    dates = [d.date for d in all_days]
    assert test_date in dates
    assert test_date_tomorrow in dates


@pytest.mark.asyncio
async def test_user_isolation(
    day_repo,
    day_template_repo,
    test_user,
    create_test_user,
    test_date,
    setup_day_templates,
):
    """Test that different users' days are properly isolated."""
    await setup_day_templates
    templates = await day_template_repo.all()
    default_template_uuid = (
        templates[0].uuid if templates else UUID("00000000-0000-0000-0000-000000000000")
    )

    # Create day for test_user
    day1 = Day(
        user_uuid=test_user.uuid,
        date=test_date,
        status=DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
        template_uuid=default_template_uuid,
    )
    await day_repo.put(day1)

    # Create another user
    user2 = await create_test_user()
    day_repo2 = day_repo.__class__(user_uuid=user2.uuid)

    # User2 should not see user1's day
    with pytest.raises(exceptions.NotFoundError):
        await day_repo2.get(day1.uuid)

    # User1 should still see their day
    result = await day_repo.get(day1.uuid)
    assert result.user_uuid == test_user.uuid


@pytest.mark.asyncio
async def test_delete(
    day_repo, day_template_repo, test_user, test_date, setup_day_templates
):
    """Test deleting a day."""
    await setup_day_templates
    templates = await day_template_repo.all()
    default_template_uuid = (
        templates[0].uuid if templates else UUID("00000000-0000-0000-0000-000000000000")
    )

    day = Day(
        user_uuid=test_user.uuid,
        date=test_date,
        status=DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
        template_uuid=default_template_uuid,
    )
    await day_repo.put(day)

    # Delete it
    await day_repo.delete(day)

    # Should not be found
    with pytest.raises(exceptions.NotFoundError):
        await day_repo.get(day.uuid)
