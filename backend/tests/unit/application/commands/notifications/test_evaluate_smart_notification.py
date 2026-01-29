"""Unit tests for SmartNotificationHandler."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date as dt_date, datetime
from typing import Any
from uuid import uuid4

import pytest

from lykke.application.commands.notifications import (
    SmartNotificationCommand,
    SmartNotificationHandler,
)
from lykke.application.gateways.llm_protocol import LLMTool, LLMToolRunResult
from lykke.application.llm.mixin import LLMRunSnapshotContext
from lykke.core.config import settings
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity, PushSubscriptionEntity
from tests.support.dobles import (
    create_push_subscription_repo_double,
    create_read_only_repos_double,
    create_uow_double,
    create_uow_factory_double,
)


class _LLMGateway:
    async def run_usecase(
        self,
        system_prompt: str,
        context_prompt: str,
        ask_prompt: str,
        tools: list[LLMTool],
        metadata: dict[str, Any] | None = None,
    ) -> LLMToolRunResult | None:
        _ = system_prompt
        _ = context_prompt
        _ = ask_prompt
        _ = tools
        _ = metadata
        return None


class _LLMGatewayFactory:
    def create_gateway(self, provider: value_objects.LLMProvider) -> _LLMGateway:
        _ = provider
        return _LLMGateway()


@dataclass
class _PromptContextHandler:
    prompt_context: value_objects.LLMPromptContext

    async def handle(self, _: Any) -> value_objects.LLMPromptContext:
        return self.prompt_context


@dataclass
class _Recorder:
    commands: list[object]

    async def handle(self, command: object) -> None:
        self.commands.append(command)


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


def _build_subscription(user_id: Any) -> PushSubscriptionEntity:
    return PushSubscriptionEntity(
        user_id=user_id,
        endpoint="https://example.com/push/1",
        p256dh="p256dh",
        auth="auth",
    )


@pytest.mark.asyncio
async def test_smart_handle_skips_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid4()
    handler = SmartNotificationHandler(
        create_read_only_repos_double(),
        create_uow_factory_double(create_uow_double()),
        user_id,
        _LLMGatewayFactory(),
        _PromptContextHandler(prompt_context=_build_prompt_context(user_id)),
        _Recorder(commands=[]),
    )

    called = False

    async def run_llm_side_effect() -> None:
        nonlocal called
        called = True

    handler.run_llm = run_llm_side_effect  # type: ignore[method-assign]
    monkeypatch.setattr(settings, "SMART_NOTIFICATIONS_ENABLED", False)

    await handler.handle(SmartNotificationCommand(user_id=user_id))

    assert called is False


@pytest.mark.asyncio
async def test_smart_handle_runs_llm_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid4()
    handler = SmartNotificationHandler(
        create_read_only_repos_double(),
        create_uow_factory_double(create_uow_double()),
        user_id,
        _LLMGatewayFactory(),
        _PromptContextHandler(prompt_context=_build_prompt_context(user_id)),
        _Recorder(commands=[]),
    )

    called = False

    async def run_llm_side_effect() -> None:
        nonlocal called
        called = True

    handler.run_llm = run_llm_side_effect  # type: ignore[method-assign]
    monkeypatch.setattr(settings, "SMART_NOTIFICATIONS_ENABLED", True)

    await handler.handle(
        SmartNotificationCommand(user_id=user_id, triggered_by="scheduled")
    )

    assert called is True
    assert handler._triggered_by == "scheduled"


@pytest.mark.asyncio
async def test_smart_build_prompt_input() -> None:
    user_id = uuid4()
    prompt_context = _build_prompt_context(user_id)
    handler = SmartNotificationHandler(
        create_read_only_repos_double(),
        create_uow_factory_double(create_uow_double()),
        user_id,
        _LLMGatewayFactory(),
        _PromptContextHandler(prompt_context=prompt_context),
        _Recorder(commands=[]),
    )

    result = await handler.build_prompt_input(dt_date(2025, 11, 27))

    assert result.prompt_context == prompt_context


@pytest.mark.asyncio
async def test_smart_tool_skips_low_priority() -> None:
    user_id = uuid4()
    prompt_context = _build_prompt_context(user_id)
    send_recorder = _Recorder(commands=[])
    handler = SmartNotificationHandler(
        create_read_only_repos_double(),
        create_uow_factory_double(create_uow_double()),
        user_id,
        _LLMGatewayFactory(),
        _PromptContextHandler(prompt_context=prompt_context),
        send_recorder,
    )

    tools = handler.build_tools(
        current_time=datetime.now(UTC),
        prompt_context=prompt_context,
        llm_provider=value_objects.LLMProvider.OPENAI,
    )
    tool = tools[0]

    await tool.callback(should_notify=True, message="Heads up", priority="low")

    assert send_recorder.commands == []


@pytest.mark.asyncio
async def test_smart_tool_skips_when_llm_declines() -> None:
    user_id = uuid4()
    prompt_context = _build_prompt_context(user_id)
    send_recorder = _Recorder(commands=[])
    handler = SmartNotificationHandler(
        create_read_only_repos_double(),
        create_uow_factory_double(create_uow_double()),
        user_id,
        _LLMGatewayFactory(),
        _PromptContextHandler(prompt_context=prompt_context),
        send_recorder,
    )

    tools = handler.build_tools(
        current_time=datetime.now(UTC),
        prompt_context=prompt_context,
        llm_provider=value_objects.LLMProvider.OPENAI,
    )
    tool = tools[0]

    await tool.callback(should_notify=False, message="Nope", priority="high")

    assert send_recorder.commands == []


@pytest.mark.asyncio
async def test_smart_tool_creates_skipped_notification_when_no_subscriptions() -> None:
    user_id = uuid4()
    prompt_context = _build_prompt_context(user_id)
    uow = create_uow_double()
    push_subscription_repo = create_push_subscription_repo_double()
    handler = SmartNotificationHandler(
        create_read_only_repos_double(push_subscription_repo=push_subscription_repo),
        create_uow_factory_double(uow),
        user_id,
        _LLMGatewayFactory(),
        _PromptContextHandler(prompt_context=prompt_context),
        _Recorder(commands=[]),
    )
    handler._triggered_by = "scheduled"
    handler._llm_snapshot_context = LLMRunSnapshotContext(
        prompt_context=prompt_context,
        current_time=datetime(2025, 11, 27, 9, 0, tzinfo=UTC),
        llm_provider=value_objects.LLMProvider.OPENAI,
        system_prompt="system",
        context_prompt="context",
        ask_prompt="ask",
        tools_prompt="tools",
    )

    async def no_subscriptions() -> list[PushSubscriptionEntity]:
        return []

    push_subscription_repo.all = no_subscriptions

    tools = handler.build_tools(
        current_time=datetime.now(UTC),
        prompt_context=prompt_context,
        llm_provider=value_objects.LLMProvider.OPENAI,
    )
    tool = tools[0]

    await tool.callback(should_notify=True, message="Check in", priority="high")

    assert len(uow.created) == 1
    notification = uow.created[0]
    assert notification.status == "skipped"
    assert notification.error_message == "no_subscriptions"
    assert notification.triggered_by == "scheduled"
    assert notification.llm_snapshot is not None


@pytest.mark.asyncio
async def test_smart_tool_sends_notification_with_subscriptions() -> None:
    user_id = uuid4()
    prompt_context = _build_prompt_context(user_id)
    push_subscription_repo = create_push_subscription_repo_double()
    subscription = _build_subscription(user_id)
    send_recorder = _Recorder(commands=[])

    async def return_subscriptions() -> list[PushSubscriptionEntity]:
        return [subscription]

    push_subscription_repo.all = return_subscriptions
    handler = SmartNotificationHandler(
        create_read_only_repos_double(push_subscription_repo=push_subscription_repo),
        create_uow_factory_double(create_uow_double()),
        user_id,
        _LLMGatewayFactory(),
        _PromptContextHandler(prompt_context=prompt_context),
        send_recorder,
    )

    tools = handler.build_tools(
        current_time=datetime.now(UTC),
        prompt_context=prompt_context,
        llm_provider=value_objects.LLMProvider.OPENAI,
    )
    tool = tools[0]

    await tool.callback(should_notify=True, message="Urgent", priority="high")

    assert len(send_recorder.commands) == 1
    command = send_recorder.commands[0]
    assert command.subscriptions == [subscription]
    assert command.message == "Urgent"


@pytest.mark.asyncio
async def test_smart_tool_handles_send_errors() -> None:
    user_id = uuid4()
    prompt_context = _build_prompt_context(user_id)
    push_subscription_repo = create_push_subscription_repo_double()
    subscription = _build_subscription(user_id)

    async def return_subscriptions() -> list[PushSubscriptionEntity]:
        return [subscription]

    push_subscription_repo.all = return_subscriptions

    send_recorder = _Recorder(commands=[])

    async def raise_send(_: object) -> None:
        raise RuntimeError("send failed")

    send_recorder.handle = raise_send

    handler = SmartNotificationHandler(
        create_read_only_repos_double(push_subscription_repo=push_subscription_repo),
        create_uow_factory_double(create_uow_double()),
        user_id,
        _LLMGatewayFactory(),
        _PromptContextHandler(prompt_context=prompt_context),
        send_recorder,
    )

    tools = handler.build_tools(
        current_time=datetime.now(UTC),
        prompt_context=prompt_context,
        llm_provider=value_objects.LLMProvider.OPENAI,
    )
    tool = tools[0]

    await tool.callback(should_notify=True, message="Urgent", priority="high")
    await tool.callback(should_notify=True, message="Urgent", priority="high")
