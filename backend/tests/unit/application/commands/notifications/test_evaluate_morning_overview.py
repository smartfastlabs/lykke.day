"""Unit tests for MorningOverviewHandler."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date as dt_date, datetime
from typing import Any
from uuid import uuid4

import pytest

from lykke.application.commands.notifications import (
    MorningOverviewCommand,
    MorningOverviewHandler,
)
from lykke.application.gateways.llm_protocol import LLMTool, LLMToolRunResult
from lykke.application.llm.mixin import LLMRunSnapshotContext
from lykke.application.queries.compute_task_risk import TaskRiskResult, TaskRiskScore
from lykke.core.config import settings
from lykke.domain import value_objects
from lykke.domain.entities import (
    DayEntity,
    DayTemplateEntity,
    PushSubscriptionEntity,
    TaskEntity,
    UserEntity,
)
from tests.support.dobles import (
    create_push_subscription_repo_double,
    create_read_only_repos_double,
    create_uow_double,
    create_uow_factory_double,
    create_user_repo_double,
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
class _TaskRiskHandler:
    result: TaskRiskResult

    async def handle(self, _: Any) -> TaskRiskResult:
        return self.result


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
        endpoint="https://example.com/push/overview",
        p256dh="p256dh",
        auth="auth",
    )


@pytest.mark.asyncio
async def test_morning_overview_skips_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid4()
    handler = MorningOverviewHandler(
        create_read_only_repos_double(),
        create_uow_factory_double(create_uow_double()),
        user_id,
        _LLMGatewayFactory(),
        _PromptContextHandler(prompt_context=_build_prompt_context(user_id)),
        _TaskRiskHandler(TaskRiskResult(high_risk_tasks=[])),
        _Recorder(commands=[]),
    )

    called = False

    async def run_llm_side_effect() -> None:
        nonlocal called
        called = True

    handler.run_llm = run_llm_side_effect  # type: ignore[method-assign]
    monkeypatch.setattr(settings, "SMART_NOTIFICATIONS_ENABLED", False)

    await handler.handle(MorningOverviewCommand(user_id=user_id))

    assert called is False


@pytest.mark.asyncio
async def test_morning_overview_handles_user_lookup_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid4()
    user_repo = create_user_repo_double()

    async def raise_get(_: Any) -> None:
        raise RuntimeError("missing user")

    user_repo.get = raise_get
    handler = MorningOverviewHandler(
        create_read_only_repos_double(user_repo=user_repo),
        create_uow_factory_double(create_uow_double()),
        user_id,
        _LLMGatewayFactory(),
        _PromptContextHandler(prompt_context=_build_prompt_context(user_id)),
        _TaskRiskHandler(TaskRiskResult(high_risk_tasks=[])),
        _Recorder(commands=[]),
    )
    monkeypatch.setattr(settings, "SMART_NOTIFICATIONS_ENABLED", True)

    await handler.handle(MorningOverviewCommand(user_id=user_id))


@pytest.mark.asyncio
async def test_morning_overview_skips_without_llm_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid4()
    user_repo = create_user_repo_double()
    user = UserEntity(email="test@example.com", hashed_password="hash")

    async def return_user(_: Any) -> UserEntity:
        return user

    user_repo.get = return_user
    handler = MorningOverviewHandler(
        create_read_only_repos_double(user_repo=user_repo),
        create_uow_factory_double(create_uow_double()),
        user_id,
        _LLMGatewayFactory(),
        _PromptContextHandler(prompt_context=_build_prompt_context(user_id)),
        _TaskRiskHandler(TaskRiskResult(high_risk_tasks=[])),
        _Recorder(commands=[]),
    )
    monkeypatch.setattr(settings, "SMART_NOTIFICATIONS_ENABLED", True)

    await handler.handle(MorningOverviewCommand(user_id=user_id))


@pytest.mark.asyncio
async def test_morning_overview_skips_without_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid4()
    user_repo = create_user_repo_double()
    user = UserEntity(
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(
            llm_provider=value_objects.LLMProvider.OPENAI,
            timezone="UTC",
        ),
    )

    async def return_user(_: Any) -> UserEntity:
        return user

    user_repo.get = return_user
    handler = MorningOverviewHandler(
        create_read_only_repos_double(user_repo=user_repo),
        create_uow_factory_double(create_uow_double()),
        user_id,
        _LLMGatewayFactory(),
        _PromptContextHandler(prompt_context=_build_prompt_context(user_id)),
        _TaskRiskHandler(TaskRiskResult(high_risk_tasks=[])),
        _Recorder(commands=[]),
    )

    called = False

    async def run_llm_side_effect() -> None:
        nonlocal called
        called = True

    handler.run_llm = run_llm_side_effect  # type: ignore[method-assign]
    monkeypatch.setattr(settings, "SMART_NOTIFICATIONS_ENABLED", True)

    await handler.handle(MorningOverviewCommand(user_id=user_id))

    assert called is False


@pytest.mark.asyncio
async def test_morning_overview_runs_llm_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid4()
    user_repo = create_user_repo_double()
    user = UserEntity(
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(
            llm_provider=value_objects.LLMProvider.OPENAI,
            morning_overview_time="08:00",
            timezone="UTC",
        ),
    )

    async def return_user(_: Any) -> UserEntity:
        return user

    user_repo.get = return_user
    handler = MorningOverviewHandler(
        create_read_only_repos_double(user_repo=user_repo),
        create_uow_factory_double(create_uow_double()),
        user_id,
        _LLMGatewayFactory(),
        _PromptContextHandler(prompt_context=_build_prompt_context(user_id)),
        _TaskRiskHandler(TaskRiskResult(high_risk_tasks=[])),
        _Recorder(commands=[]),
    )

    called = False

    async def run_llm_side_effect() -> None:
        nonlocal called
        called = True

    handler.run_llm = run_llm_side_effect  # type: ignore[method-assign]
    monkeypatch.setattr(settings, "SMART_NOTIFICATIONS_ENABLED", True)

    await handler.handle(MorningOverviewCommand(user_id=user_id))

    assert called is True


@pytest.mark.asyncio
async def test_morning_overview_build_prompt_input_includes_risk_data() -> None:
    user_id = uuid4()
    template = DayTemplateEntity(user_id=user_id, slug="default")
    day = DayEntity.create_for_date(dt_date(2025, 11, 27), user_id, template)
    task = TaskEntity(
        user_id=user_id,
        scheduled_date=day.date,
        name="Draft report",
        status=value_objects.TaskStatus.READY,
        type=value_objects.TaskType.WORK,
        category=value_objects.TaskCategory.WORK,
        frequency=value_objects.TaskFrequency.ONCE,
    )
    prompt_context = value_objects.LLMPromptContext(
        day=day,
        tasks=[task],
        calendar_entries=[],
        brain_dump_items=[],
        messages=[],
        push_notifications=[],
    )

    risk_result = TaskRiskResult(
        high_risk_tasks=[
            TaskRiskScore(
                task_id=task.id,
                completion_rate=42.1,
                risk_reason="low completion rate",
            )
        ]
    )
    handler = MorningOverviewHandler(
        create_read_only_repos_double(),
        create_uow_factory_double(create_uow_double()),
        user_id,
        _LLMGatewayFactory(),
        _PromptContextHandler(prompt_context=prompt_context),
        _TaskRiskHandler(result=risk_result),
        _Recorder(commands=[]),
    )

    result = await handler.build_prompt_input(day.date)

    assert result.prompt_context == prompt_context
    high_risk_tasks = result.extra_template_vars["high_risk_tasks"]
    assert high_risk_tasks[0]["name"] == "Draft report"
    assert high_risk_tasks[0]["completion_rate"] == 42.1


@pytest.mark.asyncio
async def test_morning_overview_build_prompt_input_skips_unrated_tasks() -> None:
    user_id = uuid4()
    template = DayTemplateEntity(user_id=user_id, slug="default")
    day = DayEntity.create_for_date(dt_date(2025, 11, 27), user_id, template)
    task = TaskEntity(
        user_id=user_id,
        scheduled_date=day.date,
        name="Low risk",
        status=value_objects.TaskStatus.READY,
        type=value_objects.TaskType.WORK,
        category=value_objects.TaskCategory.WORK,
        frequency=value_objects.TaskFrequency.ONCE,
    )
    prompt_context = value_objects.LLMPromptContext(
        day=day,
        tasks=[task],
        calendar_entries=[],
        brain_dump_items=[],
        messages=[],
        push_notifications=[],
    )

    handler = MorningOverviewHandler(
        create_read_only_repos_double(),
        create_uow_factory_double(create_uow_double()),
        user_id,
        _LLMGatewayFactory(),
        _PromptContextHandler(prompt_context=prompt_context),
        _TaskRiskHandler(TaskRiskResult(high_risk_tasks=[])),
        _Recorder(commands=[]),
    )

    result = await handler.build_prompt_input(day.date)

    assert result.extra_template_vars["high_risk_tasks"] == []


@pytest.mark.asyncio
async def test_morning_overview_tool_creates_skipped_notification() -> None:
    user_id = uuid4()
    prompt_context = _build_prompt_context(user_id)
    uow = create_uow_double()
    push_subscription_repo = create_push_subscription_repo_double()
    send_recorder = _Recorder(commands=[])
    handler = MorningOverviewHandler(
        create_read_only_repos_double(push_subscription_repo=push_subscription_repo),
        create_uow_factory_double(uow),
        user_id,
        _LLMGatewayFactory(),
        _PromptContextHandler(prompt_context=prompt_context),
        _TaskRiskHandler(TaskRiskResult(high_risk_tasks=[])),
        send_recorder,
    )
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

    await tool.callback(should_notify=True, message="Morning plan", priority="high")

    assert len(uow.created) == 1
    notification = uow.created[0]
    assert notification.status == "skipped"
    assert notification.error_message == "no_subscriptions"
    assert notification.triggered_by == "morning_overview"
    assert notification.llm_snapshot is not None
    assert send_recorder.commands == []


@pytest.mark.asyncio
async def test_morning_overview_tool_skips_when_llm_declines() -> None:
    user_id = uuid4()
    prompt_context = _build_prompt_context(user_id)
    uow = create_uow_double()
    push_subscription_repo = create_push_subscription_repo_double()
    send_recorder = _Recorder(commands=[])
    handler = MorningOverviewHandler(
        create_read_only_repos_double(push_subscription_repo=push_subscription_repo),
        create_uow_factory_double(uow),
        user_id,
        _LLMGatewayFactory(),
        _PromptContextHandler(prompt_context=prompt_context),
        _TaskRiskHandler(TaskRiskResult(high_risk_tasks=[])),
        send_recorder,
    )

    tools = handler.build_tools(
        current_time=datetime.now(UTC),
        prompt_context=prompt_context,
        llm_provider=value_objects.LLMProvider.OPENAI,
    )
    tool = tools[0]

    await tool.callback(should_notify=False, message="No thanks", priority="low")

    assert uow.created == []
    assert send_recorder.commands == []


@pytest.mark.asyncio
async def test_morning_overview_tool_sends_notification() -> None:
    user_id = uuid4()
    prompt_context = _build_prompt_context(user_id)
    push_subscription_repo = create_push_subscription_repo_double()
    subscription = _build_subscription(user_id)
    send_recorder = _Recorder(commands=[])

    async def return_subscriptions() -> list[PushSubscriptionEntity]:
        return [subscription]

    push_subscription_repo.all = return_subscriptions
    handler = MorningOverviewHandler(
        create_read_only_repos_double(push_subscription_repo=push_subscription_repo),
        create_uow_factory_double(create_uow_double()),
        user_id,
        _LLMGatewayFactory(),
        _PromptContextHandler(prompt_context=prompt_context),
        _TaskRiskHandler(TaskRiskResult(high_risk_tasks=[])),
        send_recorder,
    )

    tools = handler.build_tools(
        current_time=datetime.now(UTC),
        prompt_context=prompt_context,
        llm_provider=value_objects.LLMProvider.OPENAI,
    )
    tool = tools[0]

    await tool.callback(should_notify=True, message="Morning plan", priority="high")

    assert len(send_recorder.commands) == 1
    command = send_recorder.commands[0]
    assert command.subscriptions == [subscription]
    assert command.message == "Morning plan"


@pytest.mark.asyncio
async def test_morning_overview_tool_handles_send_errors() -> None:
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

    handler = MorningOverviewHandler(
        create_read_only_repos_double(push_subscription_repo=push_subscription_repo),
        create_uow_factory_double(create_uow_double()),
        user_id,
        _LLMGatewayFactory(),
        _PromptContextHandler(prompt_context=prompt_context),
        _TaskRiskHandler(TaskRiskResult(high_risk_tasks=[])),
        send_recorder,
    )

    tools = handler.build_tools(
        current_time=datetime.now(UTC),
        prompt_context=prompt_context,
        llm_provider=value_objects.LLMProvider.OPENAI,
    )
    tool = tools[0]

    await tool.callback(should_notify=True, message="Morning plan", priority="high")
    await tool.callback(should_notify=True, message="Morning plan", priority="high")
    await tool.callback(should_notify=True, message="Morning plan", priority="high")