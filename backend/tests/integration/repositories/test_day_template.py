"""Integration tests for DayTemplateRepository."""

from datetime import time
from uuid import UUID

import pytest
import pytest_asyncio

from planned.core.exceptions import exceptions
from planned.domain.entities import Alarm, DayTemplate
from planned.domain.value_objects.alarm import AlarmType
from planned.infrastructure.repositories import DayTemplateRepository


@pytest.mark.asyncio
async def test_get(day_template_repo, test_user, setup_day_templates):
    """Test getting a day template by ID."""
    result = await day_template_repo.get("default")
    
    assert result.id == "default"
    assert result.user_uuid == test_user.uuid


@pytest.mark.asyncio
async def test_get_not_found(day_template_repo):
    """Test getting a non-existent day template raises NotFoundError."""
    with pytest.raises(exceptions.NotFoundError):
        await day_template_repo.get("nonexistent")


@pytest.mark.asyncio
async def test_put(day_template_repo, test_user):
    """Test creating a new day template."""
    template = DayTemplate(
        user_uuid=test_user.uuid,
        id="custom",
        tasks=[],
        alarm=Alarm(
            name="Custom Alarm",
            time=time(8, 0),
            type=AlarmType.GENTLE,
        ),
    )
    
    result = await day_template_repo.put(template)
    
    assert result.id == "custom"
    assert result.alarm.name == "Custom Alarm"


@pytest.mark.asyncio
async def test_all(day_template_repo, test_user, setup_day_templates):
    """Test getting all day templates."""
    all_templates = await day_template_repo.all()
    
    template_ids = [t.id for t in all_templates]
    assert "default" in template_ids
    assert "weekend" in template_ids


@pytest.mark.asyncio
async def test_user_isolation(day_template_repo, test_user, create_test_user, setup_day_templates):
    """Test that different users' day templates are properly isolated."""
    # Create another user
    user2 = await create_test_user()
    day_template_repo2 = DayTemplateRepository(user_uuid=user2.uuid)
    
    # User2 should not see user1's templates
    with pytest.raises(exceptions.NotFoundError):
        await day_template_repo2.get("default")
    
    # User1 should still see their templates
    result = await day_template_repo.get("default")
    assert result.user_uuid == test_user.uuid

