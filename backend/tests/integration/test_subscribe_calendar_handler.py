from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from lykke.application.commands.calendar.subscribe_calendar import (
    SubscribeCalendarCommand,
    SubscribeCalendarHandler,
)
from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.domain import value_objects
from lykke.domain.entities import AuthTokenEntity, CalendarEntity, CalendarEntryEntity
from lykke.infrastructure.gateways import StubPubSubGateway
from lykke.infrastructure.unit_of_work import (
    SqlAlchemyReadOnlyRepositories,
    SqlAlchemyUnitOfWorkFactory,
)


class FakeGoogleGateway(GoogleCalendarGatewayProtocol):
    def __init__(self, *, expiration: datetime) -> None:
        self._expiration = expiration
        self.calls: list[dict[str, object]] = []

    async def subscribe_to_calendar(
        self,
        calendar: CalendarEntity,
        token: AuthTokenEntity,
        webhook_url: str,
        channel_id: str,
        client_state: str,
    ) -> value_objects.CalendarSubscription:
        self.calls.append(
            {
                "calendar_id": calendar.id,
                "token_id": token.id,
                "webhook_url": webhook_url,
                "channel_id": channel_id,
                "client_state": client_state,
            }
        )
        return value_objects.CalendarSubscription(
            channel_id="channel-id",
            resource_id="resource-id",
            expiration=self._expiration,
        )

    async def load_calendar_events(  # pragma: no cover - unused in this test
        self,
        calendar: CalendarEntity,
        lookback: datetime,
        token: AuthTokenEntity,
        *,
        user_timezone: str | None = None,
        sync_token: str | None = None,
    ) -> tuple[list[CalendarEntryEntity], list[CalendarEntryEntity], str | None]:
        return [], [], "next-token"

    async def unsubscribe_from_calendar(  # pragma: no cover - unused in this test
        self,
        calendar: CalendarEntity,
        token: AuthTokenEntity,
        channel_id: str,
        resource_id: str | None,
    ) -> None:
        raise NotImplementedError

    def get_flow(self, flow_name: str) -> Any:  # pragma: no cover - unused
        raise NotImplementedError


@pytest.mark.asyncio
async def test_subscribe_calendar_persists_subscription(
    test_user,
    auth_token_repo,
    calendar_repo,
) -> None:
    auth_token = await auth_token_repo.put(
        AuthTokenEntity(
            id=uuid4(),
            user_id=test_user.id,
            platform="google",
            token="test-token",
            refresh_token="test-refresh",
        )
    )

    calendar = CalendarEntity(
        user_id=test_user.id,
        name="My Calendar",
        auth_token_id=auth_token.id,
        platform="google",
        platform_id="platform-id",
    )
    await calendar_repo.put(calendar)

    expiration = datetime.now(UTC) + timedelta(days=1)
    google_gateway = FakeGoogleGateway(expiration=expiration)

    handler = SubscribeCalendarHandler(
        ro_repos=SqlAlchemyReadOnlyRepositories(user_id=test_user.id),
        uow_factory=SqlAlchemyUnitOfWorkFactory(pubsub_gateway=StubPubSubGateway()),
        user_id=test_user.id,
        google_gateway=google_gateway,
    )

    updated_calendar = await handler.handle(SubscribeCalendarCommand(calendar=calendar))

    persisted = await calendar_repo.get(calendar.id)

    assert persisted.sync_subscription is not None
    assert persisted.sync_subscription.subscription_id == "channel-id"
    assert persisted.sync_subscription.resource_id == "resource-id"
    assert persisted.sync_subscription.expiration == expiration
    assert persisted.sync_subscription.provider == "google"
    assert persisted.sync_subscription_id == "channel-id"
    assert updated_calendar.sync_subscription_id == "channel-id"
    assert google_gateway.calls and google_gateway.calls[0]["client_state"]
