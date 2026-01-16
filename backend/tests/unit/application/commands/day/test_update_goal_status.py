"""Unit tests for UpdateGoalStatusHandler."""

import datetime
from datetime import UTC, date as dt_date
from uuid import uuid4

import pytest

from lykke.application.commands.day import UpdateGoalStatusHandler
from lykke.core.exceptions import DomainError, NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity
from lykke.domain.events.day_events import GoalStatusChangedEvent


class _FakeDayReadOnlyRepo:
    """Fake day repository for testing."""

    def __init__(self, day: DayEntity) -> None:
        self._day = day

    async def get(self, day_id):
        if day_id == self._day.id:
            return self._day
        raise NotFoundError(f"Day {day_id} not found")


class _FakeReadOnlyRepos:
    """Lightweight container matching ReadOnlyRepositories protocol."""

    def __init__(self, day_repo: _FakeDayReadOnlyRepo) -> None:
        fake = object()
        self.audit_log_ro_repo = fake
        self.auth_token_ro_repo = fake
        self.bot_personality_ro_repo = fake
        self.calendar_entry_ro_repo = fake
        self.calendar_entry_series_ro_repo = fake
        self.calendar_ro_repo = fake
        self.conversation_ro_repo = fake
        self.day_ro_repo = day_repo
        self.day_template_ro_repo = fake
        self.factoid_ro_repo = fake
        self.message_ro_repo = fake
        self.push_subscription_ro_repo = fake
        self.routine_ro_repo = fake
        self.task_definition_ro_repo = fake
        self.task_ro_repo = fake
        self.time_block_definition_ro_repo = fake
        self.user_ro_repo = fake


class _FakeUoW:
    """Minimal UnitOfWork that just collects added entities."""

    def __init__(self, day_repo) -> None:
        self.added = []
        self.day_ro_repo = day_repo

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    def add(self, entity):
        self.added.append(entity)


class _FakeUoWFactory:
    def __init__(self, day_repo) -> None:
        self.uow = _FakeUoW(day_repo)

    def create(self, _user_id):
        return self.uow


@pytest.mark.asyncio
async def test_update_goal_status_updates_status():
    """Test update_goal_status updates the goal's status."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)
    goal = day.add_goal("Test Goal")
    # Clear events from add_goal
    day.collect_events()

    day_repo = _FakeDayReadOnlyRepo(day)
    ro_repos = _FakeReadOnlyRepos(day_repo)
    uow_factory = _FakeUoWFactory(day_repo)
    handler = UpdateGoalStatusHandler(ro_repos, uow_factory, user_id)

    # Act
    result = await handler.update_goal_status(
        date=task_date, goal_id=goal.id, status=value_objects.GoalStatus.COMPLETE
    )

    # Assert
    updated_goal = next(g for g in result.goals if g.id == goal.id)
    assert updated_goal.status == value_objects.GoalStatus.COMPLETE
    assert len(uow_factory.uow.added) == 1
    assert uow_factory.uow.added[0] == result


@pytest.mark.asyncio
async def test_update_goal_status_emits_domain_event():
    """Test update_goal_status emits GoalStatusChangedEvent."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)
    goal = day.add_goal("Test Goal")
    # Clear events from add_goal
    day.collect_events()

    day_repo = _FakeDayReadOnlyRepo(day)
    ro_repos = _FakeReadOnlyRepos(day_repo)
    uow_factory = _FakeUoWFactory(day_repo)
    handler = UpdateGoalStatusHandler(ro_repos, uow_factory, user_id)

    # Act
    result = await handler.update_goal_status(
        date=task_date, goal_id=goal.id, status=value_objects.GoalStatus.COMPLETE
    )

    # Assert
    events = result.collect_events()
    assert len(events) == 1
    assert isinstance(events[0], GoalStatusChangedEvent)
    assert events[0].goal_id == goal.id
    assert events[0].goal_name == "Test Goal"
    assert events[0].old_status == value_objects.GoalStatus.INCOMPLETE
    assert events[0].new_status == value_objects.GoalStatus.COMPLETE
    assert events[0].day_id == day.id


@pytest.mark.asyncio
async def test_update_goal_status_raises_error_if_goal_not_found():
    """Test update_goal_status raises error if goal doesn't exist."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)
    fake_goal_id = uuid4()

    day_repo = _FakeDayReadOnlyRepo(day)
    ro_repos = _FakeReadOnlyRepos(day_repo)
    uow_factory = _FakeUoWFactory(day_repo)
    handler = UpdateGoalStatusHandler(ro_repos, uow_factory, user_id)

    # Act & Assert
    with pytest.raises(DomainError, match="not found"):
        await handler.update_goal_status(
            date=task_date, goal_id=fake_goal_id, status=value_objects.GoalStatus.COMPLETE
        )


@pytest.mark.asyncio
async def test_update_goal_status_no_change_does_not_add_to_uow():
    """Test update_goal_status doesn't add entity to UoW if status unchanged."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)
    goal = day.add_goal("Test Goal")
    # Clear events from add_goal
    day.collect_events()
    
    # Set goal status to COMPLETE
    day.update_goal_status(goal.id, value_objects.GoalStatus.COMPLETE)
    # Clear events from update
    day.collect_events()

    day_repo = _FakeDayReadOnlyRepo(day)
    ro_repos = _FakeReadOnlyRepos(day_repo)
    uow_factory = _FakeUoWFactory(day_repo)
    handler = UpdateGoalStatusHandler(ro_repos, uow_factory, user_id)

    # Act - try to update to same status
    result = await handler.update_goal_status(
        date=task_date, goal_id=goal.id, status=value_objects.GoalStatus.COMPLETE
    )

    # Assert - entity should not be added to UoW because status didn't change
    assert len(uow_factory.uow.added) == 0
    assert result.goals[0].status == value_objects.GoalStatus.COMPLETE
    # No events should be emitted
    events = result.collect_events()
    assert len(events) == 0


@pytest.mark.asyncio
async def test_update_goal_status_all_status_transitions():
    """Test update_goal_status works for all status transitions."""
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)
    goal = day.add_goal("Test Goal")

    day_repo = _FakeDayReadOnlyRepo(day)
    ro_repos = _FakeReadOnlyRepos(day_repo)
    uow_factory = _FakeUoWFactory(day_repo)
    handler = UpdateGoalStatusHandler(ro_repos, uow_factory, user_id)

    # INCOMPLETE -> COMPLETE
    result = await handler.update_goal_status(
        date=task_date, goal_id=goal.id, status=value_objects.GoalStatus.COMPLETE
    )
    assert result.goals[0].status == value_objects.GoalStatus.COMPLETE

    # Update the day in repo for next test
    day_repo._day = result

    # COMPLETE -> PUNT
    result = await handler.update_goal_status(
        date=task_date, goal_id=goal.id, status=value_objects.GoalStatus.PUNT
    )
    assert result.goals[0].status == value_objects.GoalStatus.PUNT

    # Update the day in repo for next test
    day_repo._day = result

    # PUNT -> INCOMPLETE
    result = await handler.update_goal_status(
        date=task_date, goal_id=goal.id, status=value_objects.GoalStatus.INCOMPLETE
    )
    assert result.goals[0].status == value_objects.GoalStatus.INCOMPLETE
