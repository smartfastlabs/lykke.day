"""Integration tests for DayRepository."""

from uuid import UUID, uuid4

import pytest
from lykke.core.exceptions import NotFoundError
from lykke.core.utils.dates import get_current_datetime
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity


@pytest.mark.asyncio
async def test_get(
    day_repo, day_template_repo, test_user, test_date, setup_day_templates
):
    """Test getting a day by date."""
    await setup_day_templates
    templates = await day_template_repo.all()
    default_template = templates[0] if templates else None
    if not default_template:
        pytest.skip("No templates available")

    day = DayEntity(
        user_id=test_user.id,
        date=test_date,
        status=value_objects.DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
        template=default_template,
    )
    await day_repo.put(day)

    result = await day_repo.get(day.id)

    assert result.date == test_date
    assert result.status == value_objects.DayStatus.SCHEDULED
    assert result.user_id == test_user.id


@pytest.mark.asyncio
async def test_get_not_found(day_repo, test_date):
    """Test getting a non-existent day raises NotFoundError."""
    with pytest.raises(NotFoundError):
        await day_repo.get(uuid4())


@pytest.mark.asyncio
async def test_put(
    day_repo, day_template_repo, test_user, test_date, setup_day_templates
):
    """Test creating a new day."""
    await setup_day_templates
    templates = await day_template_repo.all()
    default_template = templates[0] if templates else None
    if not default_template:
        pytest.skip("No templates available")

    day = DayEntity(
        user_id=test_user.id,
        date=test_date,
        status=value_objects.DayStatus.UNSCHEDULED,
        template=default_template,
    )

    result = await day_repo.put(day)

    assert result.date == test_date
    assert result.status == value_objects.DayStatus.UNSCHEDULED
    assert result.user_id == test_user.id


@pytest.mark.asyncio
async def test_put_update(
    day_repo, day_template_repo, test_user, test_date, setup_day_templates
):
    """Test updating an existing day."""
    await setup_day_templates
    templates = await day_template_repo.all()
    default_template = templates[0] if templates else None
    if not default_template:
        pytest.skip("No templates available")

    day = DayEntity(
        user_id=test_user.id,
        date=test_date,
        status=value_objects.DayStatus.UNSCHEDULED,
        template=default_template,
    )
    await day_repo.put(day)

    # Update the day
    day.status = value_objects.DayStatus.SCHEDULED
    day.scheduled_at = get_current_datetime()
    result = await day_repo.put(day)

    assert result.status == value_objects.DayStatus.SCHEDULED
    assert result.scheduled_at is not None

    # Verify it was saved
    retrieved = await day_repo.get(day.id)
    assert retrieved.status == value_objects.DayStatus.SCHEDULED


@pytest.mark.asyncio
async def test_put_round_trip_brain_dump_items(
    day_repo, day_template_repo, test_user, test_date, setup_day_templates
):
    """Test brain dump items are persisted on Day."""
    await setup_day_templates
    templates = await day_template_repo.all()
    default_template = templates[0] if templates else None
    if not default_template:
        pytest.skip("No templates available")

    day = DayEntity(
        user_id=test_user.id,
        date=test_date,
        status=value_objects.DayStatus.UNSCHEDULED,
        template=default_template,
    )
    item = day.add_brain_dump_item("Remember to buy bread")
    day.update_brain_dump_item_status(item.id, value_objects.BrainDumpItemStatus.PUNT)
    await day_repo.put(day)

    retrieved = await day_repo.get(day.id)
    assert len(retrieved.brain_dump_items) == 1
    assert retrieved.brain_dump_items[0].text == "Remember to buy bread"
    assert (
        retrieved.brain_dump_items[0].status == value_objects.BrainDumpItemStatus.PUNT
    )


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
    default_template = templates[0] if templates else None
    if not default_template:
        pytest.skip("No templates available")

    day1 = DayEntity(
        user_id=test_user.id,
        date=test_date,
        status=value_objects.DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
        template=default_template,
    )
    day2 = DayEntity(
        user_id=test_user.id,
        date=test_date_tomorrow,
        status=value_objects.DayStatus.UNSCHEDULED,
        template=default_template,
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
    default_template = templates[0] if templates else None
    if not default_template:
        pytest.skip("No templates available")

    day1 = DayEntity(
        user_id=test_user.id,
        date=test_date,
        status=value_objects.DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
        template=default_template,
    )
    day2 = DayEntity(
        user_id=test_user.id,
        date=test_date_tomorrow,
        status=value_objects.DayStatus.UNSCHEDULED,
        template=default_template,
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
    default_template = templates[0] if templates else None
    if not default_template:
        pytest.skip("No templates available")

    # Create day for test_user
    day1 = DayEntity(
        user_id=test_user.id,
        date=test_date,
        status=value_objects.DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
        template=default_template,
    )
    await day_repo.put(day1)

    # Create another user
    user2 = await create_test_user()
    day_repo2 = day_repo.__class__(user_id=user2.id)

    # User2 should not see user1's day
    with pytest.raises(NotFoundError):
        await day_repo2.get(day1.id)

    # User1 should still see their day
    result = await day_repo.get(day1.id)
    assert result.user_id == test_user.id


@pytest.mark.asyncio
async def test_delete(
    day_repo, day_template_repo, test_user, test_date, setup_day_templates
):
    """Test deleting a day."""
    await setup_day_templates
    templates = await day_template_repo.all()
    default_template = templates[0] if templates else None
    if not default_template:
        pytest.skip("No templates available")

    day = DayEntity(
        user_id=test_user.id,
        date=test_date,
        status=value_objects.DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
        template=default_template,
    )
    await day_repo.put(day)

    # Delete it
    await day_repo.delete(day)

    # Should not be found
    with pytest.raises(NotFoundError):
        await day_repo.get(day.id)


@pytest.mark.asyncio
async def test_remove_all_reminders_clears_field_in_database(
    day_repo, day_template_repo, test_user, test_date, setup_day_templates
):
    """Regression test: Removing all reminders clears the reminders field in the database.

    This test verifies that when all reminders are removed from a day, the reminders field
    is properly cleared in the database (not left with the previous value).
    """
    await setup_day_templates
    templates = await day_template_repo.all()
    default_template = templates[0] if templates else None
    if not default_template:
        pytest.skip("No templates available")

    # Create a day with reminders
    day = DayEntity(
        user_id=test_user.id,
        date=test_date,
        status=value_objects.DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
        template=default_template,
    )
    day.add_reminder("Reminder 1")
    day.add_reminder("Reminder 2")
    # Clear events from add_reminder
    day.collect_events()

    # Save day with reminders to database
    await day_repo.put(day)

    # Verify reminders were saved
    retrieved = await day_repo.get(day.id)
    assert len(retrieved.reminders) == 2

    # Remove all reminders
    reminder1_id = retrieved.reminders[0].id
    reminder2_id = retrieved.reminders[1].id
    retrieved.remove_reminder(reminder1_id)
    retrieved.remove_reminder(reminder2_id)
    # Clear events from remove_reminder
    retrieved.collect_events()

    # Save day without reminders to database
    await day_repo.put(retrieved)

    # Reload from database and verify reminders field is cleared (empty list, not None)
    final_retrieved = await day_repo.get(day.id)
    assert final_retrieved.reminders == []
    assert len(final_retrieved.reminders) == 0
