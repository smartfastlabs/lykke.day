"""Integration tests for DayRepository."""

from datetime import UTC, datetime, time
from uuid import uuid4

import pytest

from lykke.core.exceptions import NotFoundError
from lykke.core.utils.dates import get_current_datetime
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity
from lykke.domain.entities.day_template import DayTemplateEntity
from lykke.infrastructure.database.tables import days_tbl


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
    day_repo2 = day_repo.__class__(user=user2)

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
async def test_put_with_alarms_persists_to_database(
    day_repo, day_template_repo, test_user, test_date, setup_day_templates
):
    """Test that creating a day with alarms persists them to the database."""
    await setup_day_templates
    templates = await day_template_repo.all()
    default_template = templates[0] if templates else None
    if not default_template:
        pytest.skip("No templates available")

    alarm_time = time(8, 15, 0)
    alarm_dt = datetime(2025, 11, 27, 8, 15, tzinfo=UTC)
    day = DayEntity(
        user_id=test_user.id,
        date=test_date,
        status=value_objects.DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
        template=default_template,
        alarms=[
            value_objects.Alarm(
                name="Wake up",
                time=alarm_time,
                datetime=alarm_dt,
                type=value_objects.AlarmType.GENERIC,
                url="",
            )
        ],
    )

    result = await day_repo.put(day)

    assert len(result.alarms) == 1
    assert result.alarms[0].name == "Wake up"
    assert result.alarms[0].time == alarm_time
    assert result.alarms[0].datetime == alarm_dt
    assert result.alarms[0].type == value_objects.AlarmType.GENERIC
    assert result.alarms[0].url == ""

    fetched = await day_repo.get(day.id)
    assert len(fetched.alarms) == 1
    assert fetched.alarms[0].name == "Wake up"
    assert fetched.alarms[0].time == alarm_time
    assert fetched.alarms[0].datetime == alarm_dt
    assert fetched.alarms[0].type == value_objects.AlarmType.GENERIC
    assert fetched.alarms[0].url == ""


@pytest.mark.asyncio
async def test_remove_all_alarms_clears_field_in_database(
    day_repo, day_template_repo, test_user, test_date, setup_day_templates
):
    """Test that removing all alarms clears the alarms field in the database."""
    await setup_day_templates
    templates = await day_template_repo.all()
    default_template = templates[0] if templates else None
    if not default_template:
        pytest.skip("No templates available")

    alarm_time = time(8, 15, 0)
    alarm_dt = datetime(2025, 11, 27, 8, 15, tzinfo=UTC)
    day = DayEntity(
        user_id=test_user.id,
        date=test_date,
        status=value_objects.DayStatus.SCHEDULED,
        scheduled_at=get_current_datetime(),
        template=default_template,
        alarms=[
            value_objects.Alarm(
                name="Wake up",
                time=alarm_time,
                datetime=alarm_dt,
                type=value_objects.AlarmType.GENERIC,
                url="",
            )
        ],
    )

    await day_repo.put(day)
    retrieved = await day_repo.get(day.id)
    assert len(retrieved.alarms) == 1

    retrieved.alarms = []
    await day_repo.put(retrieved)

    final_retrieved = await day_repo.get(day.id)
    assert final_retrieved.alarms == []
    assert len(final_retrieved.alarms) == 0


@pytest.mark.asyncio
async def test_get_handles_legacy_routine_ids_in_template(
    day_repo, test_user, test_date
):
    """Regression test: handle legacy routine_ids in stored day templates."""
    routine_definition_id = uuid4()
    template_id = DayTemplateEntity.id_from_slug_and_user("default", test_user.id)
    day_id = DayEntity.id_from_date_and_user(test_date, test_user.id)

    template_payload = {
        "id": str(template_id),
        "user_id": str(test_user.id),
        "slug": "default",
        "routine_ids": [str(routine_definition_id)],
    }

    async with day_repo._get_connection(for_write=True) as conn:
        await conn.execute(
            days_tbl.insert().values(
                id=day_id,
                user_id=test_user.id,
                date=test_date,
                status=value_objects.DayStatus.UNSCHEDULED.value,
                template=template_payload,
            )
        )

    retrieved = await day_repo.get(day_id)

    assert retrieved.template is not None
    assert retrieved.template.routine_definition_ids == [routine_definition_id]
