"""Integration tests for UserProfileRepository."""

from datetime import UTC, datetime, time
from uuid import uuid4

import pytest

from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import UserProfileEntity


@pytest.mark.asyncio
async def test_put_and_get(user_profile_repo, test_user):
    profile = UserProfileEntity(
        user_id=test_user.id,
        preferred_name="Todd",
        goals=["sleep", "focus"],
        work_hours=value_objects.WorkHours(
            start_time=time(9, 0),
            end_time=time(17, 0),
            weekdays=[value_objects.DayOfWeek.MONDAY, value_objects.DayOfWeek.FRIDAY],
        ),
        created_at=datetime(2026, 2, 5, 10, 0, 0, tzinfo=UTC),
    )
    await user_profile_repo.put(profile)

    loaded = await user_profile_repo.get(profile.id)
    assert loaded.user_id == test_user.id
    assert loaded.preferred_name == "Todd"
    assert loaded.goals == ["sleep", "focus"]
    assert loaded.work_hours is not None
    assert loaded.work_hours.start_time == time(9, 0)
    assert loaded.work_hours.weekdays == [
        value_objects.DayOfWeek.MONDAY,
        value_objects.DayOfWeek.FRIDAY,
    ]


@pytest.mark.asyncio
async def test_get_not_found(user_profile_repo):
    with pytest.raises(NotFoundError):
        await user_profile_repo.get(UserProfileEntity.id_from_user_id(uuid4()))

