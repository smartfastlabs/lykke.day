"""Unit tests for ResetCalendarDataHandler."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest

from lykke.application.commands.calendar import (
    ResetCalendarDataCommand,
    ResetCalendarDataHandler,
)
from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.domain import value_objects
from lykke.domain.entities import (
    AuthTokenEntity,
    CalendarEntity,
    CalendarEntryEntity,
    CalendarEntrySeriesEntity,
    UserEntity,
)
from lykke.domain.value_objects.sync import SyncSubscription
from tests.support.dobles import (
    create_auth_token_repo_double,
    create_calendar_entry_repo_double,
    create_calendar_entry_series_repo_double,
    create_calendar_repo_double,
    create_google_gateway_double,
    create_read_only_repos_double,
    create_uow_double,
    create_uow_factory_double,
)


class _RepositoryFactory:
    def __init__(self, ro_repos: object) -> None:
        self._ro_repos = ro_repos

    def create(self, user: object) -> object:
        _ = user
        return self._ro_repos


class _GatewayFactory:
    def __init__(self, google_gateway: GoogleCalendarGatewayProtocol) -> None:
        self._google_gateway = google_gateway

    def can_create(self, dependency_type: type[object]) -> bool:
        return dependency_type is GoogleCalendarGatewayProtocol

    def create(self, dependency_type: type[object]) -> object:
        _ = dependency_type
        return self._google_gateway


def _build_calendar(user_id: Any, *, subscribed: bool) -> CalendarEntity:
    subscription = None
    subscription_id = None
    if subscribed:
        subscription = SyncSubscription(
            subscription_id="channel-1",
            resource_id="resource-1",
            expiration=datetime(2025, 12, 1, tzinfo=UTC),
            provider="google",
            client_state="state",
            sync_token="token",
            webhook_url="https://example.com",
        )
        subscription_id = subscription.subscription_id
    return CalendarEntity(
        user_id=user_id,
        name="Work",
        auth_token_id=uuid4(),
        platform_id="cal-1",
        platform="google",
        sync_subscription=subscription,
        sync_subscription_id=subscription_id,
    )


@pytest.mark.asyncio
async def test_reset_calendar_data_skips_unsubscribed_calendars() -> None:
    user_id = uuid4()
    calendar = _build_calendar(user_id, subscribed=False)
    calendar_entry_repo = create_calendar_entry_repo_double()
    calendar_entry_series_repo = create_calendar_entry_series_repo_double()
    calendar_repo = create_calendar_repo_double()

    async def all_calendars() -> list[CalendarEntity]:
        return [calendar]

    async def no_entries(_: object) -> list[CalendarEntryEntity]:
        return []

    async def no_series(_: object) -> list[CalendarEntrySeriesEntity]:
        return []

    calendar_repo.all = all_calendars
    calendar_entry_repo.search = no_entries
    calendar_entry_series_repo.search = no_series

    uow = create_uow_double(
        calendar_repo=calendar_repo,
        calendar_entry_repo=calendar_entry_repo,
        calendar_entry_series_repo=calendar_entry_series_repo,
        auth_token_repo=create_auth_token_repo_double(),
    )

    ro_repos = create_read_only_repos_double(
        calendar_repo=calendar_repo,
        calendar_entry_repo=calendar_entry_repo,
        calendar_entry_series_repo=calendar_entry_series_repo,
    )
    google_gateway = create_google_gateway_double()

    handler = ResetCalendarDataHandler(
        user=UserEntity(id=user_id, email="test@example.com", hashed_password="!"),
        uow_factory=create_uow_factory_double(uow),
        repository_factory=_RepositoryFactory(ro_repos),
        gateway_factory=_GatewayFactory(google_gateway),
    )

    result = await handler.handle(ResetCalendarDataCommand())

    assert result == []
    assert uow.deleted == []


@pytest.mark.asyncio
async def test_reset_calendar_data_refreshes_subscriptions() -> None:
    user_id = uuid4()
    calendar = _build_calendar(user_id, subscribed=True)
    token = AuthTokenEntity(user_id=user_id, platform="google", token="token")
    entry = CalendarEntryEntity(
        user_id=user_id,
        name="Event",
        calendar_id=calendar.id,
        platform_id="event-1",
        platform="google",
        status="confirmed",
        starts_at=datetime(2025, 11, 27, 9, 0, tzinfo=UTC),
        ends_at=datetime(2025, 11, 27, 10, 0, tzinfo=UTC),
        frequency=value_objects.TaskFrequency.ONCE,
    )
    series = CalendarEntrySeriesEntity(
        user_id=user_id,
        calendar_id=calendar.id,
        name="Series",
        platform_id="series-1",
        platform="google",
        frequency=value_objects.TaskFrequency.WEEKLY,
    )
    calendar_entry_repo = create_calendar_entry_repo_double()
    calendar_entry_series_repo = create_calendar_entry_series_repo_double()
    calendar_repo = create_calendar_repo_double()
    auth_token_repo = create_auth_token_repo_double()

    async def all_calendars() -> list[CalendarEntity]:
        return [calendar]

    async def entries(_: object) -> list[CalendarEntryEntity]:
        return [entry]

    async def series_items(_: object) -> list[CalendarEntrySeriesEntity]:
        return [series]

    async def get_token(_: object) -> AuthTokenEntity:
        return token

    calendar_repo.all = all_calendars
    calendar_entry_repo.search = entries
    calendar_entry_series_repo.search = series_items
    auth_token_repo.get = get_token

    uow = create_uow_double(
        calendar_repo=calendar_repo,
        calendar_entry_repo=calendar_entry_repo,
        calendar_entry_series_repo=calendar_entry_series_repo,
        auth_token_repo=auth_token_repo,
    )

    ro_repos = create_read_only_repos_double(
        calendar_repo=calendar_repo,
        calendar_entry_repo=calendar_entry_repo,
        calendar_entry_series_repo=calendar_entry_series_repo,
        auth_token_repo=auth_token_repo,
    )

    google_gateway = create_google_gateway_double()
    unsubscribed: list[str] = []

    async def unsubscribe_from_calendar(**kwargs: Any) -> None:
        unsubscribed.append(kwargs["channel_id"])

    google_gateway.unsubscribe_from_calendar = unsubscribe_from_calendar

    async def subscribe_to_calendar(**_: Any) -> value_objects.CalendarSubscription:
        return value_objects.CalendarSubscription(
            channel_id="new-channel",
            resource_id="new-resource",
            expiration=datetime(2025, 12, 1, tzinfo=UTC),
        )

    google_gateway.subscribe_to_calendar = subscribe_to_calendar

    handler = ResetCalendarDataHandler(
        user=UserEntity(id=user_id, email="test@example.com", hashed_password="!"),
        uow_factory=create_uow_factory_double(uow),
        repository_factory=_RepositoryFactory(ro_repos),
        gateway_factory=_GatewayFactory(google_gateway),
    )

    result = await handler.handle(ResetCalendarDataCommand())

    assert unsubscribed == ["channel-1"]
    assert len(result) == 1
    assert uow.deleted == [entry, series]
    assert uow.added


@pytest.mark.asyncio
async def test_reset_calendar_data_rejects_unknown_platform() -> None:
    user_id = uuid4()
    calendar = CalendarEntity(
        user_id=user_id,
        name="Work",
        auth_token_id=uuid4(),
        platform_id="cal-1",
        platform="microsoft",
    )
    token = AuthTokenEntity(user_id=user_id, platform="microsoft", token="token")
    uow = create_uow_double(
        calendar_repo=create_calendar_repo_double(),
        calendar_entry_repo=create_calendar_entry_repo_double(),
        calendar_entry_series_repo=create_calendar_entry_series_repo_double(),
        auth_token_repo=create_auth_token_repo_double(),
    )
    ro_repos = create_read_only_repos_double()

    handler = ResetCalendarDataHandler(
        user=UserEntity(id=user_id, email="test@example.com", hashed_password="!"),
        uow_factory=create_uow_factory_double(uow),
        repository_factory=_RepositoryFactory(ro_repos),
        gateway_factory=_GatewayFactory(create_google_gateway_double()),
    )

    with pytest.raises(NotImplementedError):
        await handler._refresh_subscription(calendar, token, uow)
