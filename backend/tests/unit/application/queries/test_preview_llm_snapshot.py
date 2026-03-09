"""Unit tests for PreviewLLMSnapshotHandler."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as dt_date
from typing import Any
from uuid import uuid4

import pytest
from dobles import allow

from lykke.application.queries.preview_llm_snapshot import (
    PreviewLLMSnapshotHandler,
    PreviewLLMSnapshotQuery,
)
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity, UserEntity
from tests.support.dobles import (
    create_read_only_repos_double,
    create_repo_double,
)


class _RepositoryFactory:
    def __init__(self, ro_repos: object) -> None:
        self._ro_repos = ro_repos

    def create(self, user: object) -> object:
        _ = user
        return self._ro_repos


@dataclass
class _PromptContextHandler:
    prompt_context: value_objects.LLMPromptContext

    async def handle(self, _: object) -> value_objects.LLMPromptContext:
        return self.prompt_context


class _LLMGateway:
    def __init__(self) -> None:
        self.assessment_calls = 0
        self.usecase_calls = 0

    async def preview_assessment_usecase(
        self,
        _: str,
        __: str,
        ___: object,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.assessment_calls += 1
        _ = metadata
        return {
            "request_messages": [{"role": "user", "content": "ask"}],
            "assessment_schema": {"name": "assessment-schema"},
            "request_model_params": {"temperature": 0},
        }

    async def preview_usecase(
        self,
        _: str,
        __: str,
        ___: list[object],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.usecase_calls += 1
        _ = metadata
        return {}


class _LLMGatewayFactory:
    def __init__(self, gateway: _LLMGateway) -> None:
        self.gateway = gateway

    def create_gateway(self, provider: value_objects.LLMProvider) -> _LLMGateway:
        _ = provider
        return self.gateway


def _build_prompt_context(user_id: object) -> value_objects.LLMPromptContext:
    template = DayTemplateEntity(user_id=user_id, slug="default")
    day = DayEntity.create_for_date(dt_date(2026, 3, 8), user_id, template)
    return value_objects.LLMPromptContext(day=day)


@pytest.mark.asyncio
async def test_preview_user_status_snapshot_uses_assessment_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """User status snapshot preview should use assessment payload generation."""
    user_id = uuid4()
    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(
            llm_provider=value_objects.LLMProvider.OPENAI,
            timezone="UTC",
            status_signals=[
                value_objects.StatusSignal(
                    name="Anxiety",
                    slug="anxiety",
                    description="Stress level",
                    goal=value_objects.StatusSignalGoal(
                        text="Keep this low",
                        value=30,
                    ),
                ),
                value_objects.StatusSignal(
                    name="Energy",
                    slug="energy",
                    description="Current energy",
                ),
            ],
        ),
    )
    prompt_context = _build_prompt_context(user_id)

    usecase_config_repo = create_repo_double(
        "lykke.application.repositories.UseCaseConfigRepositoryReadOnlyProtocol"
    )
    allow(usecase_config_repo).search.and_return([])
    user_check_in_repo = create_repo_double(
        "lykke.application.repositories.UserCheckInRepositoryReadOnlyProtocol"
    )
    recent_check_ins = [{"id": "c1"}, {"id": "c2"}]
    allow(user_check_in_repo).search.and_return(recent_check_ins)

    ro_repos = create_read_only_repos_double(
        usecase_config_repo=usecase_config_repo,
        user_check_in_repo=user_check_in_repo,
    )
    handler = PreviewLLMSnapshotHandler(
        user=user,
        repository_factory=_RepositoryFactory(ro_repos),
    )
    handler.get_llm_prompt_context_handler = _PromptContextHandler(prompt_context)
    gateway = _LLMGateway()
    handler.llm_gateway_factory = _LLMGatewayFactory(gateway)

    captured_context_vars: dict[str, object] = {}
    captured_ask_vars: dict[str, object] = {}

    def _fake_render_context_prompt(
        *,
        usecase: str,
        prompt_context: value_objects.LLMPromptContext,
        current_time: object,
        extra_template_vars: dict[str, Any],
    ) -> str:
        _ = (usecase, prompt_context, current_time)
        captured_context_vars.update(extra_template_vars)
        return "context"

    def _fake_render_ask_prompt(
        *, usecase: str, extra_template_vars: dict[str, Any]
    ) -> str:
        _ = usecase
        captured_ask_vars.update(extra_template_vars)
        return "ask"

    async def _fake_render_system_prompt(
        *,
        usecase: str,
        user: UserEntity,
        usecase_config_ro_repo: object,
    ) -> str:
        _ = (usecase, user, usecase_config_ro_repo)
        return "system"

    monkeypatch.setattr(
        "lykke.application.queries.preview_llm_snapshot.render_context_prompt",
        _fake_render_context_prompt,
    )
    monkeypatch.setattr(
        "lykke.application.queries.preview_llm_snapshot.render_ask_prompt",
        _fake_render_ask_prompt,
    )
    monkeypatch.setattr(
        "lykke.application.queries.preview_llm_snapshot.render_system_prompt",
        _fake_render_system_prompt,
    )

    snapshot = await handler.handle(PreviewLLMSnapshotQuery(usecase="user_status_use_case"))

    assert snapshot is not None
    assert gateway.assessment_calls == 1
    assert gateway.usecase_calls == 0
    assert snapshot.tools is None
    assert snapshot.tool_choice == {"name": "assessment-schema"}
    assert captured_context_vars["recent_check_ins"] == recent_check_ins
    assert captured_ask_vars["recent_check_ins"] == recent_check_ins
    assert captured_context_vars["status_signals"] == [
        {
            "name": "Anxiety",
            "slug": "anxiety",
            "description": "Stress level",
            "goal": {"text": "Keep this low", "value": 30},
        },
        {
            "name": "Energy",
            "slug": "energy",
            "description": "Current energy",
            "goal": {"text": "", "value": None},
        },
    ]
