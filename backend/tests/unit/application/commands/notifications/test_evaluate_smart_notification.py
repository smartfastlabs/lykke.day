"""Unit tests for SmartNotificationHandler."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date as dt_date, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from dobles import allow

from lykke.application.commands.notifications import (
    SmartNotificationCommand,
    SmartNotificationHandler,
)
from lykke.application.gateways.llm_protocol import LLMTool, LLMToolRunResult
from lykke.application.llm.mixin import LLMRunSnapshotContext
from lykke.application.repositories import PushNotificationRepositoryReadOnlyProtocol
from lykke.core.config import settings
from lykke.domain import value_objects
from lykke.domain.entities import (
    DayEntity,
    DayTemplateEntity,
    PushNotificationEntity,
    PushSubscriptionEntity,
    UserEntity,
)
from tests.support.dobles import (
    create_push_subscription_repo_double,
    create_read_only_repos_double,
    create_repo_double,
    create_uow_double,
    create_uow_factory_double,
)


class _RepositoryFactory:
    def __init__(self, ro_repos: object) -> None:
        self._ro_repos = ro_repos

    def create(self, user: object) -> object:
        _ = user
        return self._ro_repos


class _LLMGateway:
    async def run_usecase(
        self,
        system_prompt: str,
        ask_prompt: str,
        tools: list[LLMTool],
        metadata: dict[str, Any] | None = None,
    ) -> LLMToolRunResult | None:
        _ = system_prompt
        _ = ask_prompt
        _ = tools
        _ = metadata
        return None

    async def preview_usecase(
        self,
        system_prompt: str,
        ask_prompt: str,
        tools: list[LLMTool],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        _ = tools
        _ = metadata
        return {
            "request_messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": ask_prompt},
            ],
            "request_tools": [],
            "request_tool_choice": "auto",
            "request_model_params": {},
        }


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
        brain_dumps=[],
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


def _build_user(user_id: Any) -> UserEntity:
    return UserEntity(id=user_id, email="test@example.com", hashed_password="!")


def _build_user_with_llm(user_id: Any) -> UserEntity:
    return UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="!",
        settings=value_objects.UserSetting(
            llm_provider=value_objects.LLMProvider.OPENAI,
            timezone="UTC",
        ),
    )


@pytest.mark.asyncio
async def test_smart_handle_skips_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid4()
    handler = SmartNotificationHandler(
        user=_build_user(user_id),
        uow_factory=create_uow_factory_double(create_uow_double()),
        repository_factory=_RepositoryFactory(create_read_only_repos_double()),
    )
    handler.llm_gateway_factory = _LLMGatewayFactory()
    handler.get_llm_prompt_context_handler = _PromptContextHandler(
        prompt_context=_build_prompt_context(user_id)
    )
    handler.send_push_notification_handler = _Recorder(commands=[])

    called = False

    async def run_llm_side_effect() -> None:
        nonlocal called
        called = True

    handler.run_llm = run_llm_side_effect  # type: ignore[method-assign]
    monkeypatch.setattr(settings, "SMART_NOTIFICATIONS_ENABLED", False)

    await handler.handle(SmartNotificationCommand(user=_build_user(user_id)))

    assert called is False


@pytest.mark.asyncio
async def test_smart_handle_runs_llm_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid4()
    handler = SmartNotificationHandler(
        user=_build_user(user_id),
        uow_factory=create_uow_factory_double(create_uow_double()),
        repository_factory=_RepositoryFactory(create_read_only_repos_double()),
    )
    handler.llm_gateway_factory = _LLMGatewayFactory()
    handler.get_llm_prompt_context_handler = _PromptContextHandler(
        prompt_context=_build_prompt_context(user_id)
    )
    handler.send_push_notification_handler = _Recorder(commands=[])

    called = False

    async def run_llm_side_effect() -> None:
        nonlocal called
        called = True

    handler.run_llm = run_llm_side_effect  # type: ignore[method-assign]
    monkeypatch.setattr(settings, "SMART_NOTIFICATIONS_ENABLED", True)

    await handler.handle(
        SmartNotificationCommand(user=_build_user(user_id), triggered_by="scheduled")
    )

    assert called is True
    assert handler._triggered_by == "scheduled"


@pytest.mark.asyncio
async def test_smart_build_prompt_input() -> None:
    user_id = uuid4()
    prompt_context = _build_prompt_context(user_id)
    handler = SmartNotificationHandler(
        user=_build_user(user_id),
        uow_factory=create_uow_factory_double(create_uow_double()),
        repository_factory=_RepositoryFactory(create_read_only_repos_double()),
    )
    handler.llm_gateway_factory = _LLMGatewayFactory()
    handler.get_llm_prompt_context_handler = _PromptContextHandler(
        prompt_context=prompt_context
    )
    handler.send_push_notification_handler = _Recorder(commands=[])

    result = await handler.build_prompt_input(dt_date(2025, 11, 27))

    assert result.prompt_context == prompt_context


@pytest.mark.asyncio
async def test_smart_tool_skips_low_priority() -> None:
    user_id = uuid4()
    prompt_context = _build_prompt_context(user_id)
    send_recorder = _Recorder(commands=[])
    handler = SmartNotificationHandler(
        user=_build_user(user_id),
        uow_factory=create_uow_factory_double(create_uow_double()),
        repository_factory=_RepositoryFactory(create_read_only_repos_double()),
    )
    handler.llm_gateway_factory = _LLMGatewayFactory()
    handler.get_llm_prompt_context_handler = _PromptContextHandler(
        prompt_context=prompt_context
    )
    handler.send_push_notification_handler = send_recorder

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
        user=_build_user(user_id),
        uow_factory=create_uow_factory_double(create_uow_double()),
        repository_factory=_RepositoryFactory(create_read_only_repos_double()),
    )
    handler.llm_gateway_factory = _LLMGatewayFactory()
    handler.get_llm_prompt_context_handler = _PromptContextHandler(
        prompt_context=prompt_context
    )
    handler.send_push_notification_handler = send_recorder

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
    push_notification_repo = create_repo_double(
        PushNotificationRepositoryReadOnlyProtocol
    )
    handler = SmartNotificationHandler(
        user=_build_user(user_id),
        uow_factory=create_uow_factory_double(uow),
        repository_factory=_RepositoryFactory(
            create_read_only_repos_double(
                push_notification_repo=push_notification_repo,
                push_subscription_repo=push_subscription_repo,
            )
        ),
    )
    handler.llm_gateway_factory = _LLMGatewayFactory()
    handler.get_llm_prompt_context_handler = _PromptContextHandler(
        prompt_context=prompt_context
    )
    handler.send_push_notification_handler = _Recorder(commands=[])
    handler._triggered_by = "scheduled"
    handler._llm_snapshot_context = LLMRunSnapshotContext(
        prompt_context=prompt_context,
        current_time=datetime(2025, 11, 27, 9, 0, tzinfo=UTC),
        llm_provider=value_objects.LLMProvider.OPENAI,
        system_prompt="system",
    )

    async def no_subscriptions() -> list[PushSubscriptionEntity]:
        return []

    push_subscription_repo.all = no_subscriptions
    allow(push_notification_repo).search.and_return([])

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
    push_notification_repo = create_repo_double(
        PushNotificationRepositoryReadOnlyProtocol
    )
    subscription = _build_subscription(user_id)
    send_recorder = _Recorder(commands=[])

    async def return_subscriptions() -> list[PushSubscriptionEntity]:
        return [subscription]

    push_subscription_repo.all = return_subscriptions
    handler = SmartNotificationHandler(
        user=_build_user(user_id),
        uow_factory=create_uow_factory_double(create_uow_double()),
        repository_factory=_RepositoryFactory(
            create_read_only_repos_double(
                push_notification_repo=push_notification_repo,
                push_subscription_repo=push_subscription_repo,
            )
        ),
    )
    handler.llm_gateway_factory = _LLMGatewayFactory()
    handler.get_llm_prompt_context_handler = _PromptContextHandler(
        prompt_context=prompt_context
    )
    handler.send_push_notification_handler = send_recorder

    tools = handler.build_tools(
        current_time=datetime.now(UTC),
        prompt_context=prompt_context,
        llm_provider=value_objects.LLMProvider.OPENAI,
    )
    allow(push_notification_repo).search.and_return([])
    tool = tools[0]

    await tool.callback(should_notify=True, message="Urgent", priority="high")

    assert len(send_recorder.commands) == 1
    command = send_recorder.commands[0]
    assert command.subscriptions == [subscription]
    assert command.message == "Urgent"


@pytest.mark.asyncio
async def test_smart_tool_skips_when_recent_notification_sent() -> None:
    user_id = uuid4()
    prompt_context = _build_prompt_context(user_id)
    push_subscription_repo = create_push_subscription_repo_double()
    push_notification_repo = create_repo_double(
        PushNotificationRepositoryReadOnlyProtocol
    )
    subscription = _build_subscription(user_id)
    send_recorder = _Recorder(commands=[])
    current_time = datetime(2025, 11, 27, 9, 0, tzinfo=UTC)
    cooldown_start = current_time - timedelta(minutes=15)

    async def return_subscriptions() -> list[PushSubscriptionEntity]:
        return [subscription]

    push_subscription_repo.all = return_subscriptions
    allow(push_notification_repo).search.and_return(
        [
            PushNotificationEntity(
                user_id=user_id,
                push_subscription_ids=[subscription.id],
                content="{}",
                status="success",
                sent_at=current_time - timedelta(minutes=5),
            )
        ]
    )

    handler = SmartNotificationHandler(
        user=_build_user(user_id),
        uow_factory=create_uow_factory_double(create_uow_double()),
        repository_factory=_RepositoryFactory(
            create_read_only_repos_double(
                push_notification_repo=push_notification_repo,
                push_subscription_repo=push_subscription_repo,
            )
        ),
    )
    handler.llm_gateway_factory = _LLMGatewayFactory()
    handler.get_llm_prompt_context_handler = _PromptContextHandler(
        prompt_context=prompt_context
    )
    handler.send_push_notification_handler = send_recorder

    tools = handler.build_tools(
        current_time=current_time,
        prompt_context=prompt_context,
        llm_provider=value_objects.LLMProvider.OPENAI,
    )
    tool = tools[0]

    await tool.callback(should_notify=True, message="Time to check in", priority="high")

    assert send_recorder.commands == []


@pytest.mark.asyncio
async def test_smart_tool_handles_send_errors() -> None:
    user_id = uuid4()
    prompt_context = _build_prompt_context(user_id)
    push_subscription_repo = create_push_subscription_repo_double()
    push_notification_repo = create_repo_double(
        PushNotificationRepositoryReadOnlyProtocol
    )
    subscription = _build_subscription(user_id)

    async def return_subscriptions() -> list[PushSubscriptionEntity]:
        return [subscription]

    push_subscription_repo.all = return_subscriptions

    send_recorder = _Recorder(commands=[])

    async def raise_send(_: object) -> None:
        raise RuntimeError("send failed")

    send_recorder.handle = raise_send

    handler = SmartNotificationHandler(
        user=_build_user(user_id),
        uow_factory=create_uow_factory_double(create_uow_double()),
        repository_factory=_RepositoryFactory(
            create_read_only_repos_double(
                push_notification_repo=push_notification_repo,
                push_subscription_repo=push_subscription_repo,
            )
        ),
    )
    handler.llm_gateway_factory = _LLMGatewayFactory()
    handler.get_llm_prompt_context_handler = _PromptContextHandler(
        prompt_context=prompt_context
    )
    handler.send_push_notification_handler = send_recorder

    tools = handler.build_tools(
        current_time=datetime.now(UTC),
        prompt_context=prompt_context,
        llm_provider=value_objects.LLMProvider.OPENAI,
    )
    allow(push_notification_repo).search.and_return([])
    tool = tools[0]

    await tool.callback(should_notify=True, message="Urgent", priority="high")
    await tool.callback(should_notify=True, message="Urgent", priority="high")


@pytest.mark.asyncio
async def test_run_llm_injects_usecase_config_ro_repo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression test for prod AttributeError on self.usecase_config_ro_repo.

    BaseHandler wires annotated dependencies by resolving annotation strings
    against the defining module at runtime. If
    `UseCaseConfigRepositoryReadOnlyProtocol` is not available at runtime in
    `lykke.application.llm.mixin`, the `usecase_config_ro_repo` attribute is
    never injected and `LLMHandlerMixin.run_llm()` crashes.
    """

    user_id = uuid4()
    ro_repos = create_read_only_repos_double()
    handler = SmartNotificationHandler(
        user=_build_user_with_llm(user_id),
        uow_factory=create_uow_factory_double(create_uow_double()),
        repository_factory=_RepositoryFactory(ro_repos),
    )
    handler.llm_gateway_factory = _LLMGatewayFactory()
    handler.get_llm_prompt_context_handler = _PromptContextHandler(
        prompt_context=_build_prompt_context(user_id)
    )
    handler.send_push_notification_handler = _Recorder(commands=[])

    # Assert injection happened (this was missing in production).
    assert handler.usecase_config_ro_repo is ro_repos.usecase_config_ro_repo

    # Avoid filesystem/template rendering in this unit test; we only want to
    # verify that the LLM flow can access `self.usecase_config_ro_repo`.
    from lykke.application.llm import mixin as llm_mixin

    called = {"system": 0}

    async def fake_render_system_prompt(
        *,
        usecase: str,
        user: UserEntity,
        usecase_config_ro_repo: object,
    ) -> str:
        _ = (usecase, user)
        assert usecase_config_ro_repo is ro_repos.usecase_config_ro_repo
        called["system"] += 1
        return "system"

    def fake_render_context_prompt(*_: object, **__: object) -> str:
        return "context"

    def fake_render_ask_prompt(*_: object, **__: object) -> str:
        return "ask"

    monkeypatch.setattr(llm_mixin, "render_system_prompt", fake_render_system_prompt)
    monkeypatch.setattr(llm_mixin, "render_context_prompt", fake_render_context_prompt)
    monkeypatch.setattr(llm_mixin, "render_ask_prompt", fake_render_ask_prompt)

    result = await handler.run_llm()

    assert result is None
    assert called["system"] == 1
