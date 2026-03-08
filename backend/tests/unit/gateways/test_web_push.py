"""Unit tests for web push gateway transport behavior."""

from __future__ import annotations

from uuid import uuid4

import pytest

from lykke.core.exceptions import PushNotificationError
from lykke.domain.entities import PushSubscriptionEntity
from lykke.infrastructure.gateways import web_push


class _DummyMessage:
    encrypted = b"payload"
    headers: dict[str, str] = {"Authorization": "WebPush test"}


class _DummyWpClient:
    def get(self, content: str, subscription: object) -> _DummyMessage:
        _ = content, subscription
        return _DummyMessage()


def _build_subscription() -> PushSubscriptionEntity:
    return PushSubscriptionEntity(
        user_id=uuid4(),
        device_name="Test Device",
        endpoint="https://example.com/push",
        p256dh="p256dh",
        auth="auth",
    )


@pytest.mark.asyncio
async def test_send_notification_raises_for_410(monkeypatch: pytest.MonkeyPatch) -> None:
    """410 must be treated as a failed send (invalid subscription)."""

    class _DummyResponse:
        status = 410
        reason = "Gone"
        ok = False

    class _DummySession:
        async def __aenter__(self) -> "_DummySession":
            return self

        async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
            _ = exc_type, exc, tb

        async def post(self, **kwargs: object) -> _DummyResponse:
            _ = kwargs
            return _DummyResponse()

    def _client_session_factory() -> _DummySession:
        return _DummySession()

    monkeypatch.setattr(web_push, "wp", _DummyWpClient())
    monkeypatch.setattr(web_push.aiohttp, "ClientSession", _client_session_factory)

    with pytest.raises(PushNotificationError, match="410 Gone"):
        await web_push.send_notification(
            subscription=_build_subscription(),
            content={"title": "Hi", "body": "There"},
        )
