"""Integration tests for ResetCalendarSyncHandler."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from lykke.application.commands.calendar.reset_calendar_sync import (
    ResetCalendarSyncCommand,
    ResetCalendarSyncHandler,
)
from lykke.application.commands.calendar.sync_calendar import SyncCalendarHandler
from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.domain import value_objects
from lykke.domain.entities import AuthTokenEntity, CalendarEntity, CalendarEntryEntity
from lykke.domain.value_objects.sync import SyncSubscription
from lykke.infrastructure.gateways import StubPubSubGateway
from lykke.infrastructure.unit_of_work import (
    SqlAlchemyReadOnlyRepositoryFactory,
    SqlAlchemyUnitOfWorkFactory,
)
from lykke.presentation.handler_factory import CommandHandlerFactory


class FakeGoogleGateway(GoogleCalendarGatewayProtocol):
    """Fake Google gateway for testing."""

    def __init__(self, *, expiration: datetime) -> None:
        self._expiration = expiration
        self.subscribe_calls: list[dict[str, object]] = []
        self.unsubscribe_calls: list[dict[str, object]] = []
        self.load_events_calls: list[dict[str, object]] = []

    async def subscribe_to_calendar(
        self,
        calendar: CalendarEntity,
        token: AuthTokenEntity,
        webhook_url: str,
        channel_id: str,
        client_state: str,
    ) -> value_objects.CalendarSubscription:
        self.subscribe_calls.append(
            {
                "calendar_id": calendar.id,
                "token_id": token.id,
                "webhook_url": webhook_url,
                "channel_id": channel_id,
                "client_state": client_state,
            }
        )
        return value_objects.CalendarSubscription(
            channel_id=channel_id,
            resource_id=f"resource-{channel_id}",
            expiration=self._expiration,
        )

    async def unsubscribe_from_calendar(
        self,
        calendar: CalendarEntity,
        token: AuthTokenEntity,
        channel_id: str,
        resource_id: str | None,
    ) -> None:
        self.unsubscribe_calls.append(
            {
                "calendar_id": calendar.id,
                "token_id": token.id,
                "channel_id": channel_id,
                "resource_id": resource_id,
            }
        )

    async def load_calendar_events(
        self,
        calendar: CalendarEntity,
        lookback: datetime,
        token: AuthTokenEntity,
        *,
        user_timezone: str | None = None,
        sync_token: str | None = None,
    ) -> tuple[
        list[CalendarEntryEntity],
        list[CalendarEntryEntity],
        list[Any],
        list[Any],
        str | None,
    ]:
        self.load_events_calls.append(
            {
                "calendar_id": calendar.id,
                "lookback": lookback,
                "sync_token": sync_token,
                "user_timezone": user_timezone,
            }
        )
        # Return empty events for sync
        return [], [], [], [], "next-sync-token"

    def get_flow(self, flow_name: str) -> Any:  # pragma: no cover - unused
        raise NotImplementedError


@pytest.mark.asyncio
async def test_reset_calendar_sync_unsubscribes_deletes_future_events_and_resubscribes(
    test_user,
    auth_token_repo,
    calendar_repo,
    calendar_entry_repo,
) -> None:
    """Test that reset_sync unsubscribes, deletes future events, and resubscribes."""
    auth_token = await auth_token_repo.put(
        AuthTokenEntity(
            id=uuid4(),
            user_id=test_user.id,
            platform="google",
            token="test-token",
            refresh_token="test-refresh",
        )
    )

    # Create a calendar with a subscription
    calendar = CalendarEntity(
        user_id=test_user.id,
        name="My Calendar",
        auth_token_id=auth_token.id,
        platform="google",
        platform_id="platform-id",
        sync_subscription=SyncSubscription(
            subscription_id="old-channel-id",
            resource_id="old-resource-id",
            expiration=datetime.now(UTC) + timedelta(days=1),
            provider="google",
            client_state="old-state",
            webhook_url="https://example.com/webhook",
        ),
        sync_subscription_id="old-channel-id",
    )
    await calendar_repo.put(calendar)

    # Create calendar entries - some in the past, some in the future
    now = datetime.now(UTC)
    past_entry = CalendarEntryEntity(
        user_id=test_user.id,
        calendar_id=calendar.id,
        name="Past Event",
        platform_id="past-event-id",
        platform="google",
        status="confirmed",
        starts_at=now - timedelta(days=1),
        ends_at=now - timedelta(days=1) + timedelta(hours=1),
        frequency=value_objects.TaskFrequency.ONCE,
    )
    await calendar_entry_repo.put(past_entry)

    future_entry = CalendarEntryEntity(
        user_id=test_user.id,
        calendar_id=calendar.id,
        name="Future Event",
        platform_id="future-event-id",
        platform="google",
        status="confirmed",
        starts_at=now + timedelta(days=1),
        ends_at=now + timedelta(days=1) + timedelta(hours=1),
        frequency=value_objects.TaskFrequency.ONCE,
    )
    future_entry.create()
    await calendar_entry_repo.put(future_entry)

    expiration = datetime.now(UTC) + timedelta(days=1)
    google_gateway = FakeGoogleGateway(expiration=expiration)
    uow_factory = SqlAlchemyUnitOfWorkFactory(pubsub_gateway=StubPubSubGateway())
    ro_repo_factory = SqlAlchemyReadOnlyRepositoryFactory()
    handler = CommandHandlerFactory(
        user=test_user,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
        google_gateway_provider=lambda: google_gateway,
    ).create(ResetCalendarSyncHandler)

    # Execute reset_sync
    updated_calendars = await handler.handle(ResetCalendarSyncCommand())

    # Verify results
    assert len(updated_calendars) == 1
    updated_calendars[0]

    # Verify unsubscribe was called
    assert len(google_gateway.unsubscribe_calls) == 1
    assert google_gateway.unsubscribe_calls[0]["calendar_id"] == calendar.id
    assert google_gateway.unsubscribe_calls[0]["channel_id"] == "old-channel-id"
    assert google_gateway.unsubscribe_calls[0]["resource_id"] == "old-resource-id"

    # Verify subscribe was called (resubscribe)
    assert len(google_gateway.subscribe_calls) == 1
    assert google_gateway.subscribe_calls[0]["calendar_id"] == calendar.id

    # Verify sync was called
    assert len(google_gateway.load_events_calls) == 1
    assert google_gateway.load_events_calls[0]["calendar_id"] == calendar.id

    # Verify future entry was deleted
    future_entries = await calendar_entry_repo.search(
        value_objects.CalendarEntryQuery(calendar_id=calendar.id)
    )
    future_entry_ids = [e.id for e in future_entries]
    assert future_entry.id not in future_entry_ids, "Future entry should be deleted"

    # Verify past entry still exists
    assert past_entry.id in future_entry_ids, "Past entry should still exist"

    # Verify calendar was resubscribed
    persisted = await calendar_repo.get(calendar.id)
    assert persisted.sync_subscription is not None
    assert persisted.sync_subscription.subscription_id != "old-channel-id"
    assert persisted.sync_subscription_id != "old-channel-id"


@pytest.mark.asyncio
async def test_reset_calendar_sync_handles_multiple_calendars(
    test_user,
    auth_token_repo,
    calendar_repo,
    calendar_entry_repo,
) -> None:
    """Test that reset_sync handles multiple calendars correctly."""
    auth_token = await auth_token_repo.put(
        AuthTokenEntity(
            id=uuid4(),
            user_id=test_user.id,
            platform="google",
            token="test-token",
            refresh_token="test-refresh",
        )
    )

    # Create two calendars with subscriptions
    calendar1 = CalendarEntity(
        user_id=test_user.id,
        name="Calendar 1",
        auth_token_id=auth_token.id,
        platform="google",
        platform_id="platform-id-1",
        sync_subscription=SyncSubscription(
            subscription_id="channel-1",
            resource_id="resource-1",
            expiration=datetime.now(UTC) + timedelta(days=1),
            provider="google",
            client_state="state-1",
            webhook_url="https://example.com/webhook",
        ),
        sync_subscription_id="channel-1",
    )
    await calendar_repo.put(calendar1)

    calendar2 = CalendarEntity(
        user_id=test_user.id,
        name="Calendar 2",
        auth_token_id=auth_token.id,
        platform="google",
        platform_id="platform-id-2",
        sync_subscription=SyncSubscription(
            subscription_id="channel-2",
            resource_id="resource-2",
            expiration=datetime.now(UTC) + timedelta(days=1),
            provider="google",
            client_state="state-2",
            webhook_url="https://example.com/webhook",
        ),
        sync_subscription_id="channel-2",
    )
    await calendar_repo.put(calendar2)

    # Create a calendar without subscription (should be ignored)
    calendar3 = CalendarEntity(
        user_id=test_user.id,
        name="Calendar 3",
        auth_token_id=auth_token.id,
        platform="google",
        platform_id="platform-id-3",
        sync_subscription=None,
        sync_subscription_id=None,
    )
    await calendar_repo.put(calendar3)

    # Create future entries for subscribed calendars
    now = datetime.now(UTC)
    entry1 = CalendarEntryEntity(
        user_id=test_user.id,
        calendar_id=calendar1.id,
        name="Future Event 1",
        platform_id="future-1",
        platform="google",
        status="confirmed",
        starts_at=now + timedelta(days=1),
        ends_at=now + timedelta(days=1) + timedelta(hours=1),
        frequency=value_objects.TaskFrequency.ONCE,
    )
    entry1.create()
    await calendar_entry_repo.put(entry1)

    entry2 = CalendarEntryEntity(
        user_id=test_user.id,
        calendar_id=calendar2.id,
        name="Future Event 2",
        platform_id="future-2",
        platform="google",
        status="confirmed",
        starts_at=now + timedelta(days=1),
        ends_at=now + timedelta(days=1) + timedelta(hours=1),
        frequency=value_objects.TaskFrequency.ONCE,
    )
    entry2.create()
    await calendar_entry_repo.put(entry2)

    expiration = datetime.now(UTC) + timedelta(days=1)
    google_gateway = FakeGoogleGateway(expiration=expiration)
    uow_factory = SqlAlchemyUnitOfWorkFactory(pubsub_gateway=StubPubSubGateway())
    ro_repo_factory = SqlAlchemyReadOnlyRepositoryFactory()
    handler = CommandHandlerFactory(
        user=test_user,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
        google_gateway_provider=lambda: google_gateway,
    ).create(ResetCalendarSyncHandler)

    # Execute reset_sync
    updated_calendars = await handler.handle(ResetCalendarSyncCommand())

    # Verify both subscribed calendars were processed
    assert len(updated_calendars) == 2
    updated_ids = {cal.id for cal in updated_calendars}
    assert calendar1.id in updated_ids
    assert calendar2.id in updated_ids
    assert calendar3.id not in updated_ids  # Unsubscribed calendar should be ignored

    # Verify both were unsubscribed
    assert len(google_gateway.unsubscribe_calls) == 2
    unsubscribe_ids = {call["calendar_id"] for call in google_gateway.unsubscribe_calls}
    assert calendar1.id in unsubscribe_ids
    assert calendar2.id in unsubscribe_ids

    # Verify both were resubscribed
    assert len(google_gateway.subscribe_calls) == 2
    subscribe_ids = {call["calendar_id"] for call in google_gateway.subscribe_calls}
    assert calendar1.id in subscribe_ids
    assert calendar2.id in subscribe_ids

    # Verify both were synced
    assert len(google_gateway.load_events_calls) == 2
    sync_ids = {call["calendar_id"] for call in google_gateway.load_events_calls}
    assert calendar1.id in sync_ids
    assert calendar2.id in sync_ids

    # Verify future entries were deleted
    entries1 = await calendar_entry_repo.search(
        value_objects.CalendarEntryQuery(calendar_id=calendar1.id)
    )
    assert entry1.id not in [e.id for e in entries1]

    entries2 = await calendar_entry_repo.search(
        value_objects.CalendarEntryQuery(calendar_id=calendar2.id)
    )
    assert entry2.id not in [e.id for e in entries2]


@pytest.mark.asyncio
async def test_reset_calendar_sync_handles_no_subscribed_calendars(
    test_user,
    auth_token_repo,
    calendar_repo,
) -> None:
    """Test that reset_sync handles the case when no calendars have subscriptions."""
    auth_token = await auth_token_repo.put(
        AuthTokenEntity(
            id=uuid4(),
            user_id=test_user.id,
            platform="google",
            token="test-token",
            refresh_token="test-refresh",
        )
    )

    # Create a calendar without subscription (use unique platform_id to avoid conflicts)
    unique_platform_id = f"platform-id-{uuid4()}"
    calendar = CalendarEntity(
        user_id=test_user.id,
        name="My Calendar",
        auth_token_id=auth_token.id,
        platform="google",
        platform_id=unique_platform_id,
        sync_subscription=None,
        sync_subscription_id=None,
    )
    await calendar_repo.put(calendar)

    # Verify calendar was persisted without subscription
    persisted = await calendar_repo.get(calendar.id)
    assert persisted.sync_subscription is None, (
        "Calendar should not have a subscription"
    )
    assert persisted.sync_subscription_id is None, (
        "Calendar should not have a subscription_id"
    )

    expiration = datetime.now(UTC) + timedelta(days=1)
    google_gateway = FakeGoogleGateway(expiration=expiration)
    uow_factory = SqlAlchemyUnitOfWorkFactory(pubsub_gateway=StubPubSubGateway())
    ro_repo_factory = SqlAlchemyReadOnlyRepositoryFactory()
    handler = CommandHandlerFactory(
        user=test_user,
        ro_repo_factory=ro_repo_factory,
        uow_factory=uow_factory,
        google_gateway_provider=lambda: google_gateway,
    ).create(ResetCalendarSyncHandler)

    # Execute reset_sync
    updated_calendars = await handler.handle(ResetCalendarSyncCommand())

    # Verify no calendars were processed
    assert len(updated_calendars) == 0
    assert len(google_gateway.unsubscribe_calls) == 0
    assert len(google_gateway.subscribe_calls) == 0
    assert len(google_gateway.load_events_calls) == 0
