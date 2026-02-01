"""Unit tests for prompt rendering helpers."""

from __future__ import annotations

from datetime import UTC, date as dt_date, datetime
from uuid import uuid4

import pytest
from dobles import allow

from lykke.application.llm import render_system_prompt
from lykke.application.llm.prompt_rendering import render_context_prompt
from lykke.application.repositories import UseCaseConfigRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities import (
    DayEntity,
    DayTemplateEntity,
    MessageEntity,
    UserEntity,
)
from tests.support.dobles import create_repo_double


def test_render_context_prompt_serializes_llm_prompt_context() -> None:
    user_id = uuid4()
    current_time = datetime(2026, 1, 31, 8, 30, tzinfo=UTC)
    day_date = dt_date(2026, 1, 31)
    template = DayTemplateEntity(user_id=user_id, slug="default")
    day = DayEntity.create_for_date(day_date, user_id=user_id, template=template)

    prompt_context = value_objects.LLMPromptContext(
        day=day,
        tasks=[],
        routines=[],
        calendar_entries=[],
        brain_dump_items=[],
        factoids=[],
        messages=[],
        push_notifications=[],
    )

    inbound_message = MessageEntity(
        user_id=user_id,
        role=value_objects.MessageRole.USER,
        type=value_objects.MessageType.SMS_INBOUND,
        content="Hello from SMS",
        meta={"provider": "twilio", "from_number": "+15551234567"},
        created_at=current_time,
    )

    rendered = render_context_prompt(
        usecase="process_inbound_sms",
        prompt_context=prompt_context,
        current_time=current_time,
        extra_template_vars={"inbound_message": inbound_message},
    )

    assert "Day context (today):" in rendered
    assert '"day"' in rendered


@pytest.mark.asyncio
async def test_render_system_prompt_uses_base_personality_slug() -> None:
    """Ensure system prompt includes base personality template."""
    user_id = uuid4()
    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(
            template_defaults=["default"] * 7,
            base_personality_slug="direct",
        ),
    )

    usecase_config_repo = create_repo_double(UseCaseConfigRepositoryReadOnlyProtocol)
    allow(usecase_config_repo).search.and_return([])

    result = await render_system_prompt(
        usecase="notification",
        user=user,
        usecase_config_ro_repo=usecase_config_repo,
    )

    assert "direct, no-nonsense tone" in result
