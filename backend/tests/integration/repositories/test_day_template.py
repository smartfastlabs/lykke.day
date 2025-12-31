"""Integration tests for DayTemplateRepository."""

from datetime import time

import pytest

from planned.core.exceptions import exceptions
from planned.domain.entities import Alarm, DayTemplate
from planned.domain.value_objects.alarm import AlarmType
from planned.infrastructure.repositories import DayTemplateRepository


@pytest.mark.asyncio
async def test_get_by_slug(day_template_repo, test_user, setup_day_templates):
    await setup_day_templates
    """Test getting a day template by slug."""
    result = await day_template_repo.get_by_slug("default")

    assert result.slug == "default"
    assert result.user_id == test_user.id


@pytest.mark.asyncio
async def test_get_by_slug_not_found(day_template_repo):
    """Test getting a non-existent day template raises NotFoundError."""
    with pytest.raises(exceptions.NotFoundError):
        await day_template_repo.get_by_slug("nonexistent")


@pytest.mark.asyncio
async def test_put(day_template_repo, test_user):
    """Test creating a new day template."""
    template = DayTemplate(
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
    with pytest.raises(exceptions.NotFoundError):
        await day_template_repo2.get_by_slug("default")

    # User1 should still see their templates
    result = await day_template_repo.get_by_slug("default")
    assert result.user_id == test_user.id
