"""Integration tests for DayTemplateRepository."""

from datetime import time

import pytest

from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities.day_template import DayTemplateEntity
from lykke.domain.value_objects.alarm import Alarm, AlarmType
from lykke.infrastructure.repositories import DayTemplateRepository


@pytest.mark.asyncio
async def test_search_one_by_slug(day_template_repo, test_user, setup_day_templates):
    await setup_day_templates
    """Test getting a day template by slug."""
    result = await day_template_repo.search_one(
        value_objects.DayTemplateQuery(slug="default")
    )

    assert result.slug == "default"
    assert result.user_id == test_user.id


@pytest.mark.asyncio
async def test_search_one_by_slug_not_found(day_template_repo):
    """Test getting a non-existent day template raises NotFoundError."""
    with pytest.raises(NotFoundError):
        await day_template_repo.search_one(
            value_objects.DayTemplateQuery(slug="nonexistent")
        )


@pytest.mark.asyncio
async def test_put(day_template_repo, test_user):
    """Test creating a new day template."""
    template = DayTemplateEntity(
        user_id=test_user.id,
        slug="custom",
        alarm=Alarm(
            name="Custom Alarm",
            time=time(8, 0),
            type=AlarmType.GENTLE,
        ),
    )

    result = await day_template_repo.put(template)

    assert result.slug == "custom"
    assert result.alarm.name == "Custom Alarm"


@pytest.mark.asyncio
async def test_all(day_template_repo, test_user, setup_day_templates):
    """Test getting all day templates."""
    await setup_day_templates
    all_templates = await day_template_repo.all()

    template_slugs = [t.slug for t in all_templates]
    assert "default" in template_slugs
    assert "weekend" in template_slugs


@pytest.mark.asyncio
async def test_user_isolation(
    day_template_repo, test_user, create_test_user, setup_day_templates
):
    """Test that different users' day templates are properly isolated."""
    await setup_day_templates
    # Create another user
    user2 = await create_test_user()
    day_template_repo2 = DayTemplateRepository(user_id=user2.id)

    # User2 should not see user1's templates
    with pytest.raises(NotFoundError):
        await day_template_repo2.search_one(
            value_objects.DayTemplateQuery(slug="default")
        )

    # User1 should still see their templates
    result = await day_template_repo.search_one(
        value_objects.DayTemplateQuery(slug="default")
    )
    assert result.user_id == test_user.id


@pytest.mark.asyncio
async def test_put_with_time_blocks_persists_to_database(day_template_repo, test_user):
    """Test that creating a day template with time blocks persists them to the database."""
    from uuid import uuid4

    # Create a template with time blocks
    time_block_def_id = uuid4()
    template = DayTemplateEntity(
        user_id=test_user.id,
        slug="time-block-test",
        time_blocks=[
            value_objects.DayTemplateTimeBlock(
                time_block_definition_id=time_block_def_id,
                start_time=time(9, 0, 0),
                end_time=time(12, 0, 0),
            ),
            value_objects.DayTemplateTimeBlock(
                time_block_definition_id=time_block_def_id,
                start_time=time(14, 0, 0),
                end_time=time(17, 0, 0),
            ),
        ],
    )

    # Save to database
    result = await day_template_repo.put(template)

    # Verify returned entity has time blocks
    assert len(result.time_blocks) == 2
    assert result.time_blocks[0].time_block_definition_id == time_block_def_id
    assert result.time_blocks[0].start_time == time(9, 0, 0)
    assert result.time_blocks[0].end_time == time(12, 0, 0)

    # Fetch from database to verify persistence
    fetched = await day_template_repo.get(result.id)
    assert len(fetched.time_blocks) == 2
    assert fetched.time_blocks[0].time_block_definition_id == time_block_def_id
    assert fetched.time_blocks[0].start_time == time(9, 0, 0)
    assert fetched.time_blocks[0].end_time == time(12, 0, 0)
    assert fetched.time_blocks[1].time_block_definition_id == time_block_def_id
    assert fetched.time_blocks[1].start_time == time(14, 0, 0)
    assert fetched.time_blocks[1].end_time == time(17, 0, 0)
