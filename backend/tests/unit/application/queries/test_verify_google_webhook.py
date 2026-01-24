"""Unit tests for VerifyGoogleWebhookHandler."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from lykke.application.queries.google import (
    VerifyGoogleWebhookHandler,
    VerifyGoogleWebhookQuery,
)
from lykke.core.exceptions import NotFoundError
from lykke.domain.entities import CalendarEntity
from lykke.domain.value_objects.sync import SyncSubscription
from tests.unit.fakes import _FakeReadOnlyRepos


class _FakeCalendarRepo:
    def __init__(self, calendar: CalendarEntity | None = None) -> None:
        self._calendar = calendar

    async def get(self, calendar_id):
        if self._calendar and self._calendar.id == calendar_id:
            return self._calendar
        raise NotFoundError("Calendar not found")


@pytest.mark.asyncio
async def test_verify_google_webhook_returns_true_for_valid_token():
    user_id = uuid4()
    subscription = SyncSubscription(
        subscription_id="sub-id",
        resource_id="resource-id",
        expiration=datetime.now(UTC),
        provider="google",
        client_state="secret",
    )
    calendar = CalendarEntity(
        user_id=user_id,
        name="Calendar",
        auth_token_id=uuid4(),
        platform="google",
        platform_id="calendar-1",
        sync_subscription=subscription,
    )
    calendar_repo = _FakeCalendarRepo(calendar)
    ro_repos = _FakeReadOnlyRepos(calendar_repo=calendar_repo)
    handler = VerifyGoogleWebhookHandler(ro_repos=ro_repos, user_id=user_id)

    result = await handler.handle(
        VerifyGoogleWebhookQuery(
            calendar_id=calendar.id,
            channel_token="secret",
            resource_state="sync",
        )
    )

    assert result.should_sync is True


@pytest.mark.asyncio
async def test_verify_google_webhook_returns_false_for_missing_token():
    user_id = uuid4()
    subscription = SyncSubscription(
        subscription_id="sub-id",
        resource_id="resource-id",
        expiration=datetime.now(UTC),
        provider="google",
        client_state="secret",
    )
    calendar = CalendarEntity(
        user_id=user_id,
        name="Calendar",
        auth_token_id=uuid4(),
        platform="google",
        platform_id="calendar-1",
        sync_subscription=subscription,
    )
    calendar_repo = _FakeCalendarRepo(calendar)
    ro_repos = _FakeReadOnlyRepos(calendar_repo=calendar_repo)
    handler = VerifyGoogleWebhookHandler(ro_repos=ro_repos, user_id=user_id)

    result = await handler.handle(
        VerifyGoogleWebhookQuery(
            calendar_id=calendar.id,
            channel_token=None,
            resource_state=None,
        )
    )

    assert result.should_sync is False
