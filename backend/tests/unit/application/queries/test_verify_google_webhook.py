"""Unit tests for VerifyGoogleWebhookHandler."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from dobles import allow

from lykke.application.queries.google import (
    VerifyGoogleWebhookHandler,
    VerifyGoogleWebhookQuery,
)
from lykke.core.exceptions import NotFoundError
from lykke.domain.entities import CalendarEntity, UserEntity
from lykke.domain.value_objects.sync import SyncSubscription
from tests.support.dobles import (
    create_calendar_repo_double,
    create_read_only_repos_double,
)


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
    calendar_repo = create_calendar_repo_double()
    allow(calendar_repo).get.with_args(calendar.id).and_return(calendar)

    ro_repos = create_read_only_repos_double(calendar_repo=calendar_repo)
    user = UserEntity(id=user_id, email="test@example.com", hashed_password="!")
    handler = VerifyGoogleWebhookHandler(ro_repos=ro_repos, user=user)

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
    calendar_repo = create_calendar_repo_double()
    allow(calendar_repo).get.with_args(calendar.id).and_return(calendar)

    ro_repos = create_read_only_repos_double(calendar_repo=calendar_repo)
    user = UserEntity(id=user_id, email="test@example.com", hashed_password="!")
    handler = VerifyGoogleWebhookHandler(ro_repos=ro_repos, user=user)

    result = await handler.handle(
        VerifyGoogleWebhookQuery(
            calendar_id=calendar.id,
            channel_token=None,
            resource_state=None,
        )
    )

    assert result.should_sync is False
