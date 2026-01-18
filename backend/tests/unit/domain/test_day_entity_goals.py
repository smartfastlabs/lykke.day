"""Unit tests for DayEntity goal methods."""

import datetime
from datetime import UTC
from uuid import uuid4

import pytest

from lykke.core.exceptions import DomainError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity
from lykke.domain.events.day_events import (
    GoalAddedEvent,
    GoalRemovedEvent,
    GoalStatusChangedEvent,
)


@pytest.fixture
def test_day(test_user_id: str) -> DayEntity:
    """Create a test day."""
    template = DayTemplateEntity(
        user_id=test_user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )
    return DayEntity.create_for_date(
        datetime.date(2025, 11, 27),
        user_id=test_user_id,
        template=template,
    )


def test_add_goal_adds_goal_to_day(test_day: DayEntity) -> None:
    """Test add_goal adds a goal to the day."""
    goal = test_day.add_goal("Test Goal")

    assert len(test_day.goals) == 1
    assert test_day.goals[0].name == "Test Goal"
    assert test_day.goals[0].status == value_objects.GoalStatus.INCOMPLETE
    assert test_day.goals[0].id == goal.id
    assert goal.name == "Test Goal"


def test_add_goal_emits_domain_event(test_day: DayEntity) -> None:
    """Test add_goal emits GoalAddedEvent."""
    goal = test_day.add_goal("Test Goal")

    events = test_day.collect_events()
    assert len(events) == 1
    assert isinstance(events[0], GoalAddedEvent)
    assert events[0].goal_id == goal.id
    assert events[0].goal_name == "Test Goal"
    assert events[0].day_id == test_day.id
    assert events[0].date == test_day.date


def test_add_goal_enforces_max_five_goals(test_day: DayEntity) -> None:
    """Test add_goal enforces maximum of 5 goals."""
    test_day.add_goal("Goal 1")
    test_day.add_goal("Goal 2")
    test_day.add_goal("Goal 3")
    test_day.add_goal("Goal 4")
    test_day.add_goal("Goal 5")

    assert len(test_day.goals) == 5

    with pytest.raises(DomainError, match="at most 5 active goals"):
        test_day.add_goal("Goal 6")


def test_add_goal_sets_created_at(test_day: DayEntity) -> None:
    """Test add_goal sets created_at timestamp."""
    goal = test_day.add_goal("Test Goal")

    assert goal.created_at is not None
    assert goal.created_at.tzinfo == UTC


def test_update_goal_status_updates_status(test_day: DayEntity) -> None:
    """Test update_goal_status updates the goal's status."""
    goal = test_day.add_goal("Test Goal")
    goal_id = goal.id

    test_day.update_goal_status(goal_id, value_objects.GoalStatus.COMPLETE)

    updated_goal = next(g for g in test_day.goals if g.id == goal_id)
    assert updated_goal.status == value_objects.GoalStatus.COMPLETE
    assert updated_goal.name == "Test Goal"  # Name unchanged


def test_update_goal_status_emits_domain_event(test_day: DayEntity) -> None:
    """Test update_goal_status emits GoalStatusChangedEvent."""
    goal = test_day.add_goal("Test Goal")
    # Clear events from add_goal
    test_day.collect_events()

    test_day.update_goal_status(goal.id, value_objects.GoalStatus.COMPLETE)

    events = test_day.collect_events()
    assert len(events) == 1
    assert isinstance(events[0], GoalStatusChangedEvent)
    assert events[0].goal_id == goal.id
    assert events[0].goal_name == "Test Goal"
    assert events[0].old_status == value_objects.GoalStatus.INCOMPLETE
    assert events[0].new_status == value_objects.GoalStatus.COMPLETE
    assert events[0].day_id == test_day.id
    assert events[0].date == test_day.date


def test_update_goal_status_raises_error_if_goal_not_found(test_day: DayEntity) -> None:
    """Test update_goal_status raises error if goal doesn't exist."""
    fake_goal_id = uuid4()

    with pytest.raises(DomainError, match="not found"):
        test_day.update_goal_status(fake_goal_id, value_objects.GoalStatus.COMPLETE)


def test_update_goal_status_no_change_if_same_status(test_day: DayEntity) -> None:
    """Test update_goal_status doesn't emit event if status unchanged."""
    goal = test_day.add_goal("Test Goal")
    # Clear events from add_goal
    test_day.collect_events()

    test_day.update_goal_status(goal.id, value_objects.GoalStatus.INCOMPLETE)

    # No event should be emitted for no-op status change
    events = test_day.collect_events()
    assert len(events) == 0


def test_update_goal_status_all_transitions(test_day: DayEntity) -> None:
    """Test update_goal_status works for all status transitions."""
    goal = test_day.add_goal("Test Goal")

    # INCOMPLETE -> COMPLETE
    test_day.update_goal_status(goal.id, value_objects.GoalStatus.COMPLETE)
    assert test_day.goals[0].status == value_objects.GoalStatus.COMPLETE

    # COMPLETE -> PUNT
    test_day.update_goal_status(goal.id, value_objects.GoalStatus.PUNT)
    assert test_day.goals[0].status == value_objects.GoalStatus.PUNT

    # PUNT -> INCOMPLETE
    test_day.update_goal_status(goal.id, value_objects.GoalStatus.INCOMPLETE)
    assert test_day.goals[0].status == value_objects.GoalStatus.INCOMPLETE


def test_remove_goal_removes_goal_from_day(test_day: DayEntity) -> None:
    """Test remove_goal removes the goal from the day."""
    goal1 = test_day.add_goal("Goal 1")
    goal2 = test_day.add_goal("Goal 2")

    test_day.remove_goal(goal1.id)

    assert len(test_day.goals) == 1
    assert test_day.goals[0].id == goal2.id
    assert test_day.goals[0].name == "Goal 2"


def test_remove_goal_emits_domain_event(test_day: DayEntity) -> None:
    """Test remove_goal emits GoalRemovedEvent."""
    goal = test_day.add_goal("Test Goal")
    # Clear events from add_goal
    test_day.collect_events()

    test_day.remove_goal(goal.id)

    events = test_day.collect_events()
    assert len(events) == 1
    assert isinstance(events[0], GoalRemovedEvent)
    assert events[0].goal_id == goal.id
    assert events[0].goal_name == "Test Goal"
    assert events[0].day_id == test_day.id
    assert events[0].date == test_day.date


def test_remove_goal_raises_error_if_goal_not_found(test_day: DayEntity) -> None:
    """Test remove_goal raises error if goal doesn't exist."""
    fake_goal_id = uuid4()

    with pytest.raises(DomainError, match="not found"):
        test_day.remove_goal(fake_goal_id)


def test_remove_goal_with_multiple_goals(test_day: DayEntity) -> None:
    """Test remove_goal works correctly with multiple goals."""
    goal1 = test_day.add_goal("Goal 1")
    goal2 = test_day.add_goal("Goal 2")
    goal3 = test_day.add_goal("Goal 3")

    # Remove middle goal
    test_day.remove_goal(goal2.id)

    assert len(test_day.goals) == 2
    assert test_day.goals[0].id == goal1.id
    assert test_day.goals[1].id == goal3.id
