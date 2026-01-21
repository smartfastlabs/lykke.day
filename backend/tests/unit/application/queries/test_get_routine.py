"""Unit tests for GetRoutineHandler."""

from uuid import uuid4

import pytest

from lykke.application.queries.routine import GetRoutineHandler, GetRoutineQuery
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import RoutineEntity


class _FakeRoutineReadOnlyRepo:
    """Fake routine repository for testing."""

    def __init__(self, routine: RoutineEntity | None = None) -> None:
        self._routine = routine

    async def get(self, routine_id):
        if self._routine and routine_id == self._routine.id:
            return self._routine
        raise NotFoundError(f"Routine {routine_id} not found")


class _FakeReadOnlyRepos:
    """Lightweight container matching ReadOnlyRepositories protocol."""

    def __init__(self, routine_repo: _FakeRoutineReadOnlyRepo) -> None:
        fake = object()
        self.audit_log_ro_repo = fake
        self.auth_token_ro_repo = fake
        self.bot_personality_ro_repo = fake
        self.calendar_entry_ro_repo = fake
        self.calendar_entry_series_ro_repo = fake
        self.calendar_ro_repo = fake
        self.conversation_ro_repo = fake
        self.day_ro_repo = fake
        self.day_template_ro_repo = fake
        self.factoid_ro_repo = fake
        self.message_ro_repo = fake
        self.notification_ro_repo = fake
        self.push_notification_ro_repo = fake
        self.push_subscription_ro_repo = fake
        self.routine_ro_repo = routine_repo
        self.task_definition_ro_repo = fake
        self.task_ro_repo = fake
        self.template_ro_repo = fake
        self.time_block_definition_ro_repo = fake
        self.user_ro_repo = fake


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
    ro_repos = _FakeReadOnlyRepos(routine_repo)
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
    ro_repos = _FakeReadOnlyRepos(routine_repo)
    handler = GetRoutineHandler(ro_repos, user_id)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await handler.handle(GetRoutineQuery(routine_id=invalid_id))
