"""Unit tests for HandleGoogleLoginCallbackHandler."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from dobles import allow

import lykke.application.commands.google.handle_google_login_callback as handler_module
from lykke.application.commands.google import (
    HandleGoogleLoginCallbackCommand,
    HandleGoogleLoginCallbackHandler,
)
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import AuthTokenEntity, CalendarEntity
from lykke.domain.value_objects import CalendarQuery
from lykke.domain.value_objects.sync import SyncSubscription
from tests.support.dobles import (
    create_auth_token_repo_double,
    create_calendar_repo_double,
    create_google_gateway_double,
    create_read_only_repos_double,
    create_uow_double,
    create_uow_factory_double,
)


@pytest.mark.asyncio
async def test_handle_google_login_callback_updates_auth_token_and_calendars(
    monkeypatch,
):
    user_id = uuid4()
    existing_auth_token = AuthTokenEntity(
        user_id=user_id,
        platform="google",
        token="old-token",
    )
    subscription = SyncSubscription(
        subscription_id="sub-id",
        resource_id="resource-id",
        expiration=datetime.now(UTC),
        provider="google",
        client_state="secret",
    )
    existing_calendar = CalendarEntity(
        user_id=user_id,
        name="Old Calendar",
        auth_token_id=existing_auth_token.id,
        platform="google",
        platform_id="calendar-1",
        sync_subscription=subscription,
        sync_subscription_id="sync-id",
    )
    other_calendar = CalendarEntity(
        user_id=user_id,
        name="Other Calendar",
        auth_token_id=uuid4(),
        platform="google",
        platform_id="calendar-2",
    )

    auth_token_repo = create_auth_token_repo_double()
    allow(auth_token_repo).get.with_args(existing_auth_token.id).and_return(
        existing_auth_token
    )

    calendar_repo = create_calendar_repo_double()
    allow(calendar_repo).get.with_args(existing_calendar.id).and_return(
        existing_calendar
    )
    # When searching all calendars (no platform_id filter)
    allow(calendar_repo).search.and_return([existing_calendar, other_calendar])
    # When searching for specific platform_id: return existing for "calendar-1", None for "calendar-3"
    # We need to stub with_args for each case
    allow(calendar_repo).search_one_or_none.with_args(
        CalendarQuery(platform_id="calendar-1")
    ).and_return(existing_calendar)
    allow(calendar_repo).search_one_or_none.with_args(
        CalendarQuery(platform_id="calendar-3")
    ).and_return(None)

    uow = create_uow_double(
        auth_token_repo=auth_token_repo, calendar_repo=calendar_repo
    )
    uow_factory = create_uow_factory_double(uow)
    ro_repos = create_read_only_repos_double(
        auth_token_repo=auth_token_repo, calendar_repo=calendar_repo
    )

    # Create fake credentials and flow objects
    class Credentials:
        def __init__(self) -> None:
            self.client_id = "client-id"
            self.client_secret = "client-secret"
            self.expiry = datetime.now(UTC)
            self.refresh_token = "refresh-token"
            self.scopes = ["scope"]
            self.token = "access-token"
            self.token_uri = "token-uri"

    class Flow:
        def __init__(self) -> None:
            self.credentials = Credentials()
            self.fetched_code: str | None = None

        def fetch_token(self, *, code: str) -> None:
            self.fetched_code = code

    flow = Flow()
    gateway = create_google_gateway_double()
    allow(gateway).get_flow.and_return(flow)

    google_items = [
        {"id": "calendar-1", "summary": "Updated Calendar"},
        {"id": "calendar-3", "summary": "New Calendar"},
    ]

    # Create fake calendar service inline
    class CalendarList:
        def __init__(self, items: list[dict[str, str]]) -> None:
            self._items = items

        def list(self) -> CalendarList:
            return self

        def execute(self) -> dict[str, list[dict[str, str]]]:
            return {"items": self._items}

    class CalendarService:
        def __init__(self, items: list[dict[str, str]]) -> None:
            self._items = items

        def calendarList(self) -> CalendarList:
            return CalendarList(self._items)

    monkeypatch.setattr(
        handler_module,
        "build",
        lambda *args, **kwargs: CalendarService(google_items),
    )

    handler = HandleGoogleLoginCallbackHandler(
        ro_repos=ro_repos,
        uow_factory=uow_factory,
        user_id=user_id,
        google_gateway=gateway,
    )

    result = await handler.handle(
        HandleGoogleLoginCallbackCommand(
            code="auth-code",
            auth_token_id=existing_auth_token.id,
        )
    )

    assert flow.fetched_code == "auth-code"
    assert result.calendars_to_resubscribe == [existing_calendar.id]
    assert any(
        isinstance(entity, AuthTokenEntity) and entity.id == existing_auth_token.id
        for entity in uow.added
    )
    assert any(
        isinstance(entity, CalendarEntity) and entity.platform_id == "calendar-1"
        for entity in uow.added
    )
    assert any(
        isinstance(entity, CalendarEntity) and entity.platform_id == "calendar-3"
        for entity in uow.created
    )
