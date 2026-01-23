"""Unit tests for GetRoutineHandler."""

from uuid import uuid4

import pytest

from lykke.application.queries.routine import GetRoutineHandler, GetRoutineQuery
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import RoutineEntity
from tests.unit.fakes import _FakeReadOnlyRepos, _FakeRoutineReadOnlyRepo


@pytest.mark.asyncio
async def test_get_routine_returns_routine_by_id():
    """Verify get_routine returns the correct routine."""
    user_id = uuid4()
    routine_id = uuid4()

    routine = RoutineEntity(
        id=routine_id,
        user_id=user_id,
        name="Morning Routine",
        category=value_objects.TaskCategory.HEALTH,
        routine_schedule=value_objects.RecurrenceSchedule(
            frequency=value_objects.TaskFrequency.DAILY,
        ),
        tasks=[],
    )

    # Setup repository
    routine_repo = _FakeRoutineReadOnlyRepo(routine)
    ro_repos = _FakeReadOnlyRepos(routine_repo=routine_repo)
    handler = GetRoutineHandler(ro_repos, user_id)

    # Act
    result = await handler.handle(GetRoutineQuery(routine_id=routine_id))

    # Assert
    assert result == routine
    assert result.id == routine_id
    assert result.name == "Morning Routine"


@pytest.mark.asyncio
async def test_get_routine_raises_not_found_for_invalid_id():
    """Verify get_routine raises NotFoundError for invalid ID."""
    user_id = uuid4()
    invalid_id = uuid4()

    routine = RoutineEntity(
        id=uuid4(),  # Different ID
        user_id=user_id,
        name="Morning Routine",
        category=value_objects.TaskCategory.HEALTH,
        routine_schedule=value_objects.RecurrenceSchedule(
            frequency=value_objects.TaskFrequency.DAILY,
        ),
        tasks=[],
    )

    # Setup repository
    routine_repo = _FakeRoutineReadOnlyRepo(routine)
    ro_repos = _FakeReadOnlyRepos(routine_repo=routine_repo)
    handler = GetRoutineHandler(ro_repos, user_id)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await handler.handle(GetRoutineQuery(routine_id=invalid_id))
