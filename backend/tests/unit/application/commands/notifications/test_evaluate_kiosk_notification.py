"""Unit tests for KioskNotificationHandler."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date as dt_date, datetime
from typing import Any
from uuid import uuid4

import pytest

from lykke.application.commands.notifications import (
    KioskNotificationCommand,
    KioskNotificationHandler,
)
from lykke.core.config import settings
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity
from tests.support.dobles import (
    create_pubsub_gateway_double,
    create_read_only_repos_double,
    create_uow_double,
    create_uow_factory_double,
)


@dataclass
class _PromptContextHandler:
    prompt_context: value_objects.LLMPromptContext

    async def handle(self, _: Any) -> value_objects.LLMPromptContext:
        return self.prompt_context


def _build_prompt_context(user_id: Any) -> value_objects.LLMPromptContext:
    template = DayTemplateEntity(user_id=user_id, slug="default")
    day = DayEntity.create_for_date(dt_date(2025, 11, 27), user_id, template)
    return value_objects.LLMPromptContext(
        day=day,
        tasks=[],
        calendar_entries=[],
        brain_dump_items=[],
        messages=[],
        push_notifications=[],
    )


@pytest.mark.asyncio
async def test_kiosk_handle_skips_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    user_id = uuid4()
    ro_repos = create_read_only_repos_double()
    uow = create_uow_double()
    handler = KioskNotificationHandler(
        ro_repos,
        create_uow_factory_double(uow),
        user_id,
        _PromptContextHandler(prompt_context=_build_prompt_context(user_id)),
        create_pubsub_gateway_double(),
    )

    called = False

    async def run_llm_side_effect() -> None:
        nonlocal called
        called = True

    handler.run_llm = run_llm_side_effect  # type: ignore[method-assign]
    monkeypatch.setattr(settings, "SMART_NOTIFICATIONS_ENABLED", False)

    await handler.handle(
        KioskNotificationCommand(user_id=user_id, triggered_by="scheduled")
    )

    assert called is False


@pytest.mark.asyncio
async def test_kiosk_handle_runs_llm_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid4()
    ro_repos = create_read_only_repos_double()
    uow = create_uow_double()
    handler = KioskNotificationHandler(
        ro_repos,
        create_uow_factory_double(uow),
        user_id,
        _PromptContextHandler(prompt_context=_build_prompt_context(user_id)),
        create_pubsub_gateway_double(),
    )

    called = False

    async def run_llm_side_effect() -> None:
        nonlocal called
        called = True

    handler.run_llm = run_llm_side_effect  # type: ignore[method-assign]
    monkeypatch.setattr(settings, "SMART_NOTIFICATIONS_ENABLED", True)

    await handler.handle(
        KioskNotificationCommand(user_id=user_id, triggered_by="scheduled")
    )

    assert called is True
    assert handler._triggered_by == "scheduled"


@pytest.mark.asyncio
async def test_kiosk_build_prompt_input() -> None:
    user_id = uuid4()
    prompt_context = _build_prompt_context(user_id)
    handler = KioskNotificationHandler(
        create_read_only_repos_double(),
        create_uow_factory_double(create_uow_double()),
        user_id,
        _PromptContextHandler(prompt_context=prompt_context),
        create_pubsub_gateway_double(),
    )

    result = await handler.build_prompt_input(dt_date(2025, 11, 27))

    assert result.prompt_context == prompt_context


@pytest.mark.asyncio
async def test_kiosk_tool_does_not_publish_without_message() -> None:
    user_id = uuid4()
    prompt_context = _build_prompt_context(user_id)
    pubsub_gateway = create_pubsub_gateway_double()
    published: list[dict[str, Any]] = []

    async def record_publish(
        *, user_id: Any, channel_type: str, message: dict[str, Any]
    ) -> None:
        published.append(
            {"user_id": user_id, "channel_type": channel_type, "message": message}
        )

    pubsub_gateway.publish_to_user_channel = record_publish
    handler = KioskNotificationHandler(
        create_read_only_repos_double(),
        create_uow_factory_double(create_uow_double()),
        user_id,
        _PromptContextHandler(prompt_context=prompt_context),
        pubsub_gateway,
    )

    tools = handler.build_tools(
        current_time=datetime.now(UTC),
        prompt_context=prompt_context,
        llm_provider=value_objects.LLMProvider.OPENAI,
    )
    tool = tools[0]

    await tool.callback(should_notify=True, message=None)

    assert published == []


@pytest.mark.asyncio
async def test_kiosk_tool_skips_when_llm_says_no() -> None:
    user_id = uuid4()
    prompt_context = _build_prompt_context(user_id)
    pubsub_gateway = create_pubsub_gateway_double()
    published: list[dict[str, Any]] = []

    async def record_publish(
        *, user_id: Any, channel_type: str, message: dict[str, Any]
    ) -> None:
        published.append(
            {"user_id": user_id, "channel_type": channel_type, "message": message}
        )

    pubsub_gateway.publish_to_user_channel = record_publish
    handler = KioskNotificationHandler(
        create_read_only_repos_double(),
        create_uow_factory_double(create_uow_double()),
        user_id,
        _PromptContextHandler(prompt_context=prompt_context),
        pubsub_gateway,
    )

    tools = handler.build_tools(
        current_time=datetime.now(UTC),
        prompt_context=prompt_context,
        llm_provider=value_objects.LLMProvider.OPENAI,
    )
    tool = tools[0]

    await tool.callback(should_notify=False, message="ignore")

    assert published == []


@pytest.mark.asyncio
async def test_kiosk_tool_publishes_notification() -> None:
    user_id = uuid4()
    prompt_context = _build_prompt_context(user_id)
    pubsub_gateway = create_pubsub_gateway_double()
    published: list[dict[str, Any]] = []

    async def record_publish(
        *, user_id: Any, channel_type: str, message: dict[str, Any]
    ) -> None:
        published.append(
            {"user_id": user_id, "channel_type": channel_type, "message": message}
        )

    pubsub_gateway.publish_to_user_channel = record_publish
    handler = KioskNotificationHandler(
        create_read_only_repos_double(),
        create_uow_factory_double(create_uow_double()),
        user_id,
        _PromptContextHandler(prompt_context=prompt_context),
        pubsub_gateway,
    )
    handler._triggered_by = "scheduled"

    tools = handler.build_tools(
        current_time=datetime.now(UTC),
        prompt_context=prompt_context,
        llm_provider=value_objects.LLMProvider.OPENAI,
    )
    tool = tools[0]

    await tool.callback(
        should_notify=True,
        message="Check your next task",
        category="task_reminder",
        reason="on schedule",
    )

    assert len(published) == 1
    assert published[0]["channel_type"] == "domain-events"
    payload = published[0]["message"]
    assert payload["event_type"].endswith(".KioskNotificationEvent")
    event_data = payload["event_data"]
    assert event_data["message"] == "Check your next task"
    assert event_data["category"] == "task_reminder"
    assert event_data["triggered_by"] == "scheduled"


@pytest.mark.asyncio
async def test_kiosk_tool_handles_publish_errors() -> None:
    user_id = uuid4()
    prompt_context = _build_prompt_context(user_id)
    pubsub_gateway = create_pubsub_gateway_double()

    async def raise_publish(*_: Any, **__: Any) -> None:
        raise RuntimeError("boom")

    pubsub_gateway.publish_to_user_channel = raise_publish
    handler = KioskNotificationHandler(
        create_read_only_repos_double(),
        create_uow_factory_double(create_uow_double()),
        user_id,
        _PromptContextHandler(prompt_context=prompt_context),
        pubsub_gateway,
    )

    tools = handler.build_tools(
        current_time=datetime.now(UTC),
        prompt_context=prompt_context,
        llm_provider=value_objects.LLMProvider.OPENAI,
    )
    tool = tools[0]

    await tool.callback(should_notify=True, message="Heads up", category="other")
