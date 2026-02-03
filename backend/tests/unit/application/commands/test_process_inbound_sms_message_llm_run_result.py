"""Unit tests for ProcessInboundSmsHandler (persistence of llm_run_result)."""

from __future__ import annotations

from datetime import UTC, date as dt_date, datetime
from uuid import uuid4

import pytest
from dobles import allow

from lykke.application.commands.message import (
    ProcessInboundSmsCommand,
    ProcessInboundSmsHandler,
)
from lykke.application.llm import LLMRunResult
from lykke.domain import value_objects
from lykke.domain.entities import (
    DayEntity,
    DayTemplateEntity,
    MessageEntity,
    UserEntity,
)
from tests.support.dobles import (
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


class _LLMGatewayFactory:
    def create_gateway(self, provider: value_objects.LLMProvider) -> object:
        _ = provider
        return object()


@pytest.mark.asyncio
async def test_process_inbound_sms_records_llm_run_result_on_message() -> None:
    user_id = uuid4()
    message_id = uuid4()

    # Minimal prompt context required for snapshot serialization.
    today = dt_date(2025, 11, 27)
    template = DayTemplateEntity(user_id=user_id, slug="default")
    day = DayEntity.create_for_date(today, user_id=user_id, template=template)
    prompt_context = value_objects.LLMPromptContext(
        day=day,
        tasks=[],
        routines=[],
        calendar_entries=[],
        brain_dumps=[],
        factoids=[],
        messages=[],
        push_notifications=[],
    )

    inbound = MessageEntity(
        id=message_id,
        user_id=user_id,
        role=value_objects.MessageRole.USER,
        type=value_objects.MessageType.SMS_INBOUND,
        content="Please remind me to call mom",
        meta={"provider": "twilio", "from_number": "+15551234567"},
    )

    message_repo = create_read_only_repos_double().message_ro_repo
    allow(message_repo).get.with_args(message_id).and_return(inbound)

    ro_repos = create_read_only_repos_double(message_repo=message_repo)

    uow_message_repo = create_read_only_repos_double().message_ro_repo
    allow(uow_message_repo).get.with_args(message_id).and_return(inbound)

    uow = create_uow_double(message_repo=uow_message_repo)
    uow_factory = create_uow_factory_double(uow)

    handler = ProcessInboundSmsHandler(
        user=UserEntity(id=user_id, email="test@example.com", hashed_password="!"),
        uow_factory=uow_factory,
        repository_factory=_RepositoryFactory(ro_repos),
    )
    handler.llm_gateway_factory = _LLMGatewayFactory()
    handler.get_llm_prompt_context_handler = object()
    handler.create_adhoc_task_handler = object()
    handler.record_task_action_handler = object()
    handler.add_alarm_to_day_handler = object()
    handler.sms_gateway = object()

    # Bypass real LLM run, but still return a fully-formed result so we record snapshot.
    async def run_llm_override() -> LLMRunResult:
        return LLMRunResult(
            tool_results=[],
            prompt_context=prompt_context,
            current_time=datetime(2025, 11, 27, 9, 0, 0, tzinfo=UTC),
            llm_provider=value_objects.LLMProvider.OPENAI,
            system_prompt="system",
            context_prompt="context",
            ask_prompt="ask",
            tools_prompt="tools",
        )

    handler.run_llm = run_llm_override  # type: ignore[method-assign]

    await handler.handle(ProcessInboundSmsCommand(message_id=message_id))

    assert uow.added
    updated = uow.added[0]
    assert isinstance(updated, MessageEntity)
    assert updated.llm_run_result is not None
    assert updated.llm_run_result.llm_provider == value_objects.LLMProvider.OPENAI
    assert updated.llm_run_result.system_prompt == "system"
    assert updated.llm_run_result.system_prompt == "system"
