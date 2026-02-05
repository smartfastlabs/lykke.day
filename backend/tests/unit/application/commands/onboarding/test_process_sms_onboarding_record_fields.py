"""Unit tests for SMS onboarding tool callbacks."""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from dobles import allow

from lykke.application.commands.onboarding import ProcessSmsOnboardingHandler
from lykke.application.gateways.llm_protocol import LLMTool
from lykke.application.llm.data_collection import DataCollectionState
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, MessageEntity, UserEntity
from tests.support.dobles import (
    create_read_only_repos_double,
    create_uow_factory_double,
    create_uow_double,
)


class _RepoFactory:
    def __init__(self, ro_repos: object) -> None:
        self._ro_repos = ro_repos

    def create(self, user: object) -> object:
        _ = user
        return self._ro_repos


class _Capture:
    def __init__(self) -> None:
        self.calls: list[object] = []

    async def handle(self, command: object) -> object:
        self.calls.append(command)
        return command


def _tool_by_name(tools: list[LLMTool], name: str) -> LLMTool:
    for tool in tools:
        if tool.name == name:
            return tool
    raise AssertionError(f"Tool {name} not found")


@pytest.mark.asyncio
async def test_record_fields_persists_settings_profile_and_state() -> None:
    user_id = uuid4()
    inbound = MessageEntity(
        id=uuid4(),
        user_id=user_id,
        role=value_objects.MessageRole.USER,
        type=value_objects.MessageType.SMS_INBOUND,
        content="I'm in Chicago. Call me Todd.",
        meta={"provider": "twilio", "from_number": "+15551234567"},
    )

    # Read-only repos: usecase config is empty initially.
    usecase_config_repo = create_read_only_repos_double().usecase_config_ro_repo
    allow(usecase_config_repo).search.and_return([])

    ro_repos = create_read_only_repos_double(usecase_config_repo=usecase_config_repo)

    uow = create_uow_double()
    uow_factory = create_uow_factory_double(uow)

    handler = ProcessSmsOnboardingHandler(
        user=UserEntity(id=user_id, email="test@example.com", hashed_password="!"),
        uow_factory=uow_factory,
        repository_factory=_RepoFactory(ro_repos),
    )

    # Inject captured downstream handlers.
    handler.create_usecase_config_handler = _Capture()  # type: ignore[assignment]
    handler.update_user_handler = _Capture()  # type: ignore[assignment]
    handler.upsert_user_profile_handler = _Capture()  # type: ignore[assignment]
    handler.sms_gateway = object()  # not used

    handler._inbound_message = inbound
    handler._state = DataCollectionState()

    today = date(2026, 2, 5)
    prompt_context = value_objects.LLMPromptContext(
        day=DayEntity(user_id=user_id, date=today),
        tasks=[],
        routines=[],
        calendar_entries=[],
        brain_dumps=[],
        factoids=[],
        messages=[inbound],
        push_notifications=[],
    )

    tools = handler.build_tools(
        current_time=datetime(2026, 2, 5, 9, 0, 0, tzinfo=UTC),
        prompt_context=prompt_context,
        llm_provider=value_objects.LLMProvider.ANTHROPIC,
    )
    record = _tool_by_name(tools, "record_fields")

    await record.callback(
        fields={"timezone": "America/Chicago", "preferred_name": " Todd "},
        message=None,
    )

    # Saved workflow state via usecase config handler.
    assert handler.create_usecase_config_handler.calls  # type: ignore[attr-defined]

    # Updated user settings via UpdateUserHandler.
    assert handler.update_user_handler.calls  # type: ignore[attr-defined]

    # Upserted structured profile.
    assert handler.upsert_user_profile_handler.calls  # type: ignore[attr-defined]

