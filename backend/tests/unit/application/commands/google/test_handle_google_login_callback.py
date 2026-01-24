"""Unit tests for HandleGoogleLoginCallbackHandler."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

import lykke.application.commands.google.handle_google_login_callback as handler_module
from lykke.application.commands.google import (
    HandleGoogleLoginCallbackCommand,
    HandleGoogleLoginCallbackHandler,
)
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import AuthTokenEntity, CalendarEntity
from lykke.domain.value_objects.sync import SyncSubscription
from tests.unit.fakes import _FakeReadOnlyRepos


class _FakeCredentials:
    def __init__(self) -> None:
        self.client_id = "client-id"
        self.client_secret = "client-secret"
        self.expiry = datetime.now(UTC)
        self.refresh_token = "refresh-token"
        self.scopes = ["scope"]
        self.token = "access-token"
        self.token_uri = "token-uri"


class _FakeFlow:
    def __init__(self) -> None:
        self.credentials = _FakeCredentials()
        self.fetched_code: str | None = None

    def fetch_token(self, *, code: str) -> None:
        self.fetched_code = code


class _FakeGoogleGateway:
    def __init__(self, flow: _FakeFlow) -> None:
        self._flow = flow

    def get_flow(self, _flow_name: str) -> _FakeFlow:
        return self._flow


class _FakeCalendarList:
    def __init__(self, items: list[dict[str, str]]) -> None:
        self._items = items

    def list(self) -> "_FakeCalendarList":
        return self

    def execute(self) -> dict[str, list[dict[str, str]]]:
        return {"items": self._items}


class _FakeCalendarService:
    def __init__(self, items: list[dict[str, str]]) -> None:
        self._items = items

    def calendarList(self) -> _FakeCalendarList:
        return _FakeCalendarList(self._items)


class _FakeAuthTokenRepo:
    def __init__(self, token: AuthTokenEntity | None = None) -> None:
        self._token = token

    async def get(self, token_id: UUID) -> AuthTokenEntity:
        if self._token and self._token.id == token_id:
            return self._token
        raise NotFoundError("Auth token not found")


class _FakeCalendarRepo:
    def __init__(self, calendars: list[CalendarEntity]) -> None:
        self._calendars = calendars

    async def get(self, calendar_id: UUID) -> CalendarEntity:
        for calendar in self._calendars:
            if calendar.id == calendar_id:
                return calendar
        raise NotFoundError("Calendar not found")

    async def search(
        self, query: value_objects.CalendarQuery
    ) -> list[CalendarEntity]:
        if query.platform_id is None:
            return list(self._calendars)
        return [
            calendar
            for calendar in self._calendars
            if calendar.platform_id == query.platform_id
        ]

    async def search_one_or_none(
        self, query: value_objects.CalendarQuery
    ) -> CalendarEntity | None:
        results = await self.search(query)
        return results[0] if results else None


class _FakeUoW:
    def __init__(
        self,
        *,
        auth_token_repo: _FakeAuthTokenRepo,
        calendar_repo: _FakeCalendarRepo,
    ) -> None:
        self.auth_token_ro_repo = auth_token_repo
        self.calendar_ro_repo = calendar_repo
        self.added: list[object] = []
        self.created: list[object] = []

    async def __aenter__(self) -> "_FakeUoW":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    def add(self, entity: object) -> object:
        self.added.append(entity)
        return entity

    async def create(self, entity: object) -> object:
        self.created.append(entity)
        if hasattr(entity, "create"):
            entity.create()
        return entity


class _FakeUoWFactory:
    def __init__(self, uow: _FakeUoW) -> None:
        self._uow = uow

    def create(self, _user_id: UUID) -> _FakeUoW:
        return self._uow


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

    auth_token_repo = _FakeAuthTokenRepo(existing_auth_token)
    calendar_repo = _FakeCalendarRepo([existing_calendar, other_calendar])
    uow = _FakeUoW(auth_token_repo=auth_token_repo, calendar_repo=calendar_repo)
    uow_factory = _FakeUoWFactory(uow)
    ro_repos = _FakeReadOnlyRepos(
        auth_token_repo=auth_token_repo, calendar_repo=calendar_repo
    )

    flow = _FakeFlow()
    gateway = _FakeGoogleGateway(flow)

    google_items = [
        {"id": "calendar-1", "summary": "Updated Calendar"},
        {"id": "calendar-3", "summary": "New Calendar"},
    ]

    monkeypatch.setattr(
        handler_module,
        "build",
        lambda *args, **kwargs: _FakeCalendarService(google_items),
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
