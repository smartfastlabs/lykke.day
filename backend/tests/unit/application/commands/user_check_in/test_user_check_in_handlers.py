"""Unit tests for user check-in command handlers."""

from __future__ import annotations

from datetime import UTC, date as dt_date, datetime
from typing import Any, cast
from uuid import uuid4

import pytest

from lykke.application.commands.user_check_in.create_user_check_in import (
    CreateUserCheckInCommand,
    CreateUserCheckInHandler,
)
from lykke.application.commands.user_check_in.run_user_status_use_case import (
    UserStatusUseCaseCommand,
    UserStatusUseCaseHandler,
)
from lykke.application.llm.mixin import LLMAssessmentResult
from lykke.domain import value_objects
from lykke.domain.entities import UserCheckInEntity, UserEntity
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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("handler_cls", "command", "expected_usecase", "expected_window_days", "expected_limit"),
    [
        (
            UserStatusUseCaseHandler,
            UserStatusUseCaseCommand(),
            "user_status_use_case",
            3,
            20,
        ),
    ],
)
async def test_status_handlers_persist_normalized_llm_checkins(
    handler_cls: type[Any],
    command: object,
    expected_usecase: str,
    expected_window_days: int,
    expected_limit: int,
) -> None:
    """User status use case persists normalized LLM check-ins."""
    user = UserEntity(id=uuid4(), email="test@example.com", hashed_password="hash")
    uow = create_uow_double()
    handler = handler_cls(
        user=user,
        uow_factory=create_uow_factory_double(uow),
        repository_factory=_RepositoryFactory(create_read_only_repos_double()),
    )
    now = datetime(2026, 3, 7, 8, 30, tzinfo=UTC)

    async def run_assessment_llm_stub(_: object) -> LLMAssessmentResult:
        assessment = handler.assessment_model(
            text="  Feeling steady today.  ",
            scores={"focus": 4, "energy": "3.5"},
        )
        return LLMAssessmentResult(
            assessment=assessment,
            prompt_context=cast(value_objects.LLMPromptContext, None),
            current_time=now,
            llm_provider=value_objects.LLMProvider.OPENAI,
            system_prompt="system",
            context_prompt="context",
            ask_prompt="ask",
        )

    handler.run_assessment_llm = run_assessment_llm_stub  # type: ignore[method-assign]

    await handler.handle(command)  # type: ignore[arg-type]

    assert handler.template_usecase == expected_usecase
    assert handler.recent_checkin_window_days == expected_window_days
    assert handler.recent_checkin_limit == expected_limit
    assert len(uow.created) == 1

    created = uow.created[0]
    assert isinstance(created, UserCheckInEntity)
    assert created.source == value_objects.UserCheckInSource.LLM_USE_CASE
    assert created.source_name == expected_usecase
    assert created.source_metadata["usecase"] == expected_usecase
    assert created.source_metadata["llm_provider"] == value_objects.LLMProvider.OPENAI.value
    assert created.checkin_at == now
    assert created.text == "Feeling steady today."
    assert created.scores == {"focus": 4.0, "energy": 3.5}


@pytest.mark.asyncio
async def test_user_status_use_case_build_prompt_input_uses_recent_checkins() -> None:
    """Prompt input includes recent check-ins using configured query window."""
    user = UserEntity(id=uuid4(), email="test@example.com", hashed_password="hash")
    handler = UserStatusUseCaseHandler(
        user=user,
        uow_factory=create_uow_factory_double(create_uow_double()),
        repository_factory=_RepositoryFactory(create_read_only_repos_double()),
    )

    captured_query: value_objects.UserCheckInQuery | None = None
    captured_date: dt_date | None = None
    recent_checkins = ["check-in-1", "check-in-2"]
    prompt_context = cast(value_objects.LLMPromptContext, {"stub": True})

    class _PromptContextHandler:
        async def handle(self, query: object) -> value_objects.LLMPromptContext:
            nonlocal captured_date
            captured_date = getattr(query, "date")
            return prompt_context

    class _UserCheckInRepo:
        async def search(self, query: value_objects.UserCheckInQuery) -> list[str]:
            nonlocal captured_query
            captured_query = query
            return recent_checkins

    class _UseCaseConfigRepo:
        async def search(self, query: object) -> list[object]:
            _ = query
            return []

    handler.get_llm_prompt_context_handler = _PromptContextHandler()  # type: ignore[assignment]
    handler.user_check_in_ro_repo = _UserCheckInRepo()  # type: ignore[assignment]
    handler.usecase_config_ro_repo = _UseCaseConfigRepo()  # type: ignore[assignment]

    target_date = dt_date(2026, 3, 7)
    prompt_input = await handler.build_prompt_input(target_date)

    assert captured_date == target_date
    assert captured_query is not None
    assert captured_query.limit == 20
    assert captured_query.order_by == "checkin_at"
    assert captured_query.order_by_desc is True
    assert prompt_input.prompt_context is prompt_context
    expected_metrics = [
        {"name": name, "description": description}
        for name, description in UserStatusUseCaseHandler.default_metrics
    ]
    assert prompt_input.extra_template_vars == {
        "recent_check_ins": recent_checkins,
        "status_metrics": expected_metrics,
    }


@pytest.mark.asyncio
async def test_user_status_use_case_preview_normalizes_generated_checkin() -> None:
    """Preview returns normalized text/scores without persistence."""
    user = UserEntity(id=uuid4(), email="test@example.com", hashed_password="hash")
    uow = create_uow_double()
    handler = UserStatusUseCaseHandler(
        user=user,
        uow_factory=create_uow_factory_double(uow),
        repository_factory=_RepositoryFactory(create_read_only_repos_double()),
    )

    async def run_assessment_llm_stub(_: object) -> LLMAssessmentResult:
        class _Assessment:
            text = "  Doing okay overall  "
            scores = {"anxiety": "42", "noise": None}

        return LLMAssessmentResult(
            assessment=cast(Any, _Assessment()),
            prompt_context=cast(value_objects.LLMPromptContext, None),
            current_time=datetime(2026, 3, 7, 8, 30, tzinfo=UTC),
            llm_provider=value_objects.LLMProvider.OPENAI,
            system_prompt="system",
            context_prompt="context",
            ask_prompt="ask",
        )

    handler.run_assessment_llm = run_assessment_llm_stub  # type: ignore[method-assign]

    preview = await handler.preview_generated_checkin()

    assert preview is not None
    assert preview.text == "Doing okay overall"
    assert preview.scores == {"anxiety": 42.0}
    assert not uow.created


@pytest.mark.asyncio
async def test_create_user_check_in_persists_user_source_and_default_scores() -> None:
    """CreateUserCheckInHandler defaults scores and persists as user-authored."""
    user = UserEntity(id=uuid4(), email="test@example.com", hashed_password="hash")
    uow = create_uow_double()
    handler = CreateUserCheckInHandler(
        user=user,
        uow_factory=create_uow_factory_double(uow),
        repository_factory=_RepositoryFactory(create_read_only_repos_double()),
    )

    created = await handler.handle(CreateUserCheckInCommand(text="Checking in"))

    assert isinstance(created, UserCheckInEntity)
    assert len(uow.created) == 1
    assert created.source == value_objects.UserCheckInSource.USER
    assert created.source_name is None
    assert created.scores == {}
    assert created.text == "Checking in"
