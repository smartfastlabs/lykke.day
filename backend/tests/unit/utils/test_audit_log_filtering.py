"""Unit tests for audit log filtering utilities.

These tests ensure that audit log filtering correctly handles all entity types
that are part of the DayContext, using the exact entity type names as generated
by the UnitOfWork.
"""

from datetime import UTC, date as dt_date, datetime
from uuid import uuid4

import pytest

from lykke.core.utils.audit_log_filtering import is_audit_log_for_today
from lykke.domain.entities import AuditLogEntity

USER_TIMEZONE = "America/Chicago"


def _make_audit_log(
    entity_type: str,
    entity_data: dict,
    entity_id: str | None = None,
) -> AuditLogEntity:
    """Create an AuditLogEntity for testing."""
    return AuditLogEntity(
        id=uuid4(),
        user_id=uuid4(),
        activity_type="TestEvent",
        occurred_at=datetime.now(UTC),
        entity_id=uuid4() if entity_id is None else entity_id,
        entity_type=entity_type,
        meta={"entity_data": entity_data},
    )


def _get_entity_type_name(entity_class_name: str) -> str:
    """Get entity type name using the same logic as UnitOfWork."""
    from lykke.core.utils.strings import entity_type_from_class_name

    return entity_type_from_class_name(entity_class_name)


class TestEntityTypeNamingConsistency:
    """Tests that verify entity type names match between generation and filtering.

    These tests would have caught the 'calendar_entry' vs 'calendarentry' bug.
    """

    def test_task_entity_type_matches_filter(self):
        """Test TaskEntity generates 'task' which matches the filter."""
        entity_type = _get_entity_type_name("TaskEntity")
        assert entity_type == "task", (
            f"TaskEntity should generate 'task', got '{entity_type}'"
        )

    def test_calendarentry_entity_type_matches_filter(self):
        """Test CalendarEntryEntity generates 'calendarentry' which matches the filter.

        REGRESSION TEST: Previously the filter checked for 'calendar_entry' but
        the entity type was generated as 'calendarentry' (no underscore).
        """
        entity_type = _get_entity_type_name("CalendarEntryEntity")
        # The generated type has no underscore
        assert entity_type == "calendarentry", (
            f"CalendarEntryEntity should generate 'calendarentry', got '{entity_type}'"
        )
        # Verify this is NOT 'calendar_entry'
        assert entity_type != "calendar_entry", (
            "CalendarEntryEntity should NOT generate 'calendar_entry'"
        )

    def test_day_entity_type_matches_filter(self):
        """Test DayEntity generates 'day' which should be handled by filter.

        REGRESSION TEST: Previously 'day' entity type was not handled,
        causing reminder updates to not be pushed via websocket.
        """
        entity_type = _get_entity_type_name("DayEntity")
        assert entity_type == "day", (
            f"DayEntity should generate 'day', got '{entity_type}'"
        )

    def test_routine_definition_entity_type_matches_filter(self):
        """Test RoutineDefinitionEntity generates 'routine_definition' which matches the filter."""
        entity_type = _get_entity_type_name("RoutineDefinitionEntity")
        assert entity_type == "routine_definition", (
            "RoutineDefinitionEntity should generate "
            f"'routine_definition', got '{entity_type}'"
        )


class TestIsAuditLogForTodayTaskFiltering:
    """Tests for task entity filtering."""

    @pytest.mark.asyncio
    async def test_task_for_today_returns_true(self):
        """Test task scheduled for today returns True."""
        today = dt_date(2025, 1, 15)
        audit_log = _make_audit_log(
            entity_type="task",
            entity_data={"scheduled_date": "2025-01-15"},
        )

        result = await is_audit_log_for_today(
            audit_log, today, user_timezone=USER_TIMEZONE
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_task_for_different_day_returns_false(self):
        """Test task scheduled for different day returns False."""
        today = dt_date(2025, 1, 15)
        audit_log = _make_audit_log(
            entity_type="task",
            entity_data={"scheduled_date": "2025-01-20"},
        )

        result = await is_audit_log_for_today(
            audit_log, today, user_timezone=USER_TIMEZONE
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_task_without_scheduled_date_returns_false(self):
        """Test task without scheduled_date returns False."""
        today = dt_date(2025, 1, 15)
        audit_log = _make_audit_log(
            entity_type="task",
            entity_data={},  # No scheduled_date
        )

        result = await is_audit_log_for_today(
            audit_log, today, user_timezone=USER_TIMEZONE
        )
        assert result is False


class TestIsAuditLogForTodayCalendarEntryFiltering:
    """Tests for calendar entry filtering.

    REGRESSION TESTS: These would have caught the entity type mismatch bug
    where 'calendar_entry' was used instead of 'calendarentry'.
    """

    @pytest.mark.asyncio
    async def test_calendarentry_with_date_for_today_returns_true(self):
        """Test calendar entry with date matching today returns True."""
        today = dt_date(2025, 1, 15)
        audit_log = _make_audit_log(
            entity_type="calendarentry",  # Correct: no underscore
            entity_data={"date": "2025-01-15"},
        )

        result = await is_audit_log_for_today(
            audit_log, today, user_timezone=USER_TIMEZONE
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_calendarentry_with_starts_at_for_today_returns_true(self):
        """Test calendar entry with starts_at on today returns True."""
        today = dt_date(2025, 1, 15)
        audit_log = _make_audit_log(
            entity_type="calendarentry",  # Correct: no underscore
            entity_data={"starts_at": "2025-01-15T10:00:00+00:00"},
        )

        result = await is_audit_log_for_today(
            audit_log, today, user_timezone=USER_TIMEZONE
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_calendarentry_for_different_day_returns_false(self):
        """Test calendar entry for different day returns False."""
        today = dt_date(2025, 1, 15)
        audit_log = _make_audit_log(
            entity_type="calendarentry",
            entity_data={"date": "2025-01-20"},
        )

        result = await is_audit_log_for_today(
            audit_log, today, user_timezone=USER_TIMEZONE
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_wrong_entity_type_calendar_entry_returns_false(self):
        """Test that 'calendar_entry' (with underscore) is NOT recognized.

        REGRESSION TEST: This verifies the fix - 'calendar_entry' should NOT work
        because the actual entity type is 'calendarentry'.
        """
        today = dt_date(2025, 1, 15)
        audit_log = _make_audit_log(
            entity_type="calendar_entry",  # WRONG: has underscore
            entity_data={"date": "2025-01-15"},
        )

        result = await is_audit_log_for_today(
            audit_log, today, user_timezone=USER_TIMEZONE
        )
        # Should return False because 'calendar_entry' is not a recognized type
        assert result is False


class TestIsAuditLogForTodayDayFiltering:
    """Tests for day entity filtering.

    REGRESSION TESTS: These would have caught the missing 'day' handler bug.
    """

    @pytest.mark.asyncio
    async def test_day_for_today_returns_true(self):
        """Test day entity for today returns True.

        REGRESSION TEST: Previously 'day' was not handled, returning False
        for all day updates, which caused reminder changes to not be pushed.
        """
        today = dt_date(2025, 1, 15)
        audit_log = _make_audit_log(
            entity_type="day",
            entity_data={"date": "2025-01-15"},
        )

        result = await is_audit_log_for_today(
            audit_log, today, user_timezone=USER_TIMEZONE
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_day_for_different_day_returns_false(self):
        """Test day entity for different day returns False."""
        today = dt_date(2025, 1, 15)
        audit_log = _make_audit_log(
            entity_type="day",
            entity_data={"date": "2025-01-20"},
        )

        result = await is_audit_log_for_today(
            audit_log, today, user_timezone=USER_TIMEZONE
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_day_with_reminders_for_today_returns_true(self):
        """Test day entity with reminders for today returns True.

        This simulates a reminder being added/updated/removed.
        """
        today = dt_date(2025, 1, 15)
        audit_log = _make_audit_log(
            entity_type="day",
            entity_data={
                "date": "2025-01-15",
                "reminders": [
                    {
                        "id": str(uuid4()),
                        "name": "Test Reminder",
                        "status": "INCOMPLETE",
                    }
                ],
            },
        )

        result = await is_audit_log_for_today(
            audit_log, today, user_timezone=USER_TIMEZONE
        )
        assert result is True


class TestIsAuditLogForTodayRoutineFiltering:
    """Tests for routine definition entity filtering."""

    @pytest.mark.asyncio
    async def test_routine_always_returns_true(self):
        """Test routine definition entities are always considered relevant."""
        today = dt_date(2025, 1, 15)
        audit_log = _make_audit_log(
            entity_type="routine_definition",
            entity_data={"name": "Morning Routine"},
        )

        result = await is_audit_log_for_today(
            audit_log, today, user_timezone=USER_TIMEZONE
        )
        assert result is True


class TestIsAuditLogForTodayEdgeCases:
    """Tests for edge cases in audit log filtering."""

    @pytest.mark.asyncio
    async def test_missing_entity_data_returns_false(self):
        """Test audit log without entity_data in meta returns False."""
        today = dt_date(2025, 1, 15)
        audit_log = AuditLogEntity(
            id=uuid4(),
            user_id=uuid4(),
            activity_type="TestEvent",
            occurred_at=datetime.now(UTC),
            entity_id=uuid4(),
            entity_type="task",
            meta={},  # No entity_data
        )

        result = await is_audit_log_for_today(
            audit_log, today, user_timezone=USER_TIMEZONE
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_missing_entity_type_returns_false(self):
        """Test audit log without entity_type returns False."""
        today = dt_date(2025, 1, 15)
        audit_log = AuditLogEntity(
            id=uuid4(),
            user_id=uuid4(),
            activity_type="TestEvent",
            occurred_at=datetime.now(UTC),
            entity_id=uuid4(),
            entity_type=None,  # No entity_type
            meta={"entity_data": {"scheduled_date": "2025-01-15"}},
        )

        result = await is_audit_log_for_today(
            audit_log, today, user_timezone=USER_TIMEZONE
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_unknown_entity_type_returns_false(self):
        """Test unknown entity type returns False."""
        today = dt_date(2025, 1, 15)
        audit_log = _make_audit_log(
            entity_type="unknown_type",
            entity_data={"date": "2025-01-15"},
        )

        result = await is_audit_log_for_today(
            audit_log, today, user_timezone=USER_TIMEZONE
        )
        assert result is False
