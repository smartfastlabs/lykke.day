"""Unit tests for ListBasePersonalitiesHandler."""

from uuid import uuid4

import pytest

from lykke.application.queries.list_base_personalities import (
    ListBasePersonalitiesHandler,
    ListBasePersonalitiesQuery,
)


class _FakeReadOnlyRepos:
    """Minimal read-only repos container for BaseQueryHandler."""

    def __init__(self) -> None:
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
        self.push_notification_ro_repo = fake
        self.push_subscription_ro_repo = fake
        self.routine_ro_repo = fake
        self.task_definition_ro_repo = fake
        self.task_ro_repo = fake
        self.time_block_definition_ro_repo = fake
        self.usecase_config_ro_repo = fake
        self.user_ro_repo = fake


@pytest.mark.asyncio
async def test_list_base_personalities_includes_defaults() -> None:
    """Ensure base personalities list includes expected slugs."""
    handler = ListBasePersonalitiesHandler(_FakeReadOnlyRepos(), uuid4())

    result = await handler.handle(ListBasePersonalitiesQuery())

    slugs = {personality.slug for personality in result}
    assert "default" in slugs
    assert "calm_coach" in slugs
    assert "direct" in slugs
    assert "cheerful" in slugs
    assert "analytical" in slugs
