"""Unit tests for OpenAI LLM gateway assessment usage."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel, Field

from lykke.infrastructure.gateways.openai_llm import OpenAILLMGateway


@pytest.mark.asyncio
async def test_run_assessment_usecase_returns_validated_payload() -> None:
    """Assessment use case returns a validated pydantic payload."""

    class AssessmentModel(BaseModel):
        text: str | None = None
        scores: dict[str, float] = Field(default_factory=dict)

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value.ainvoke = AsyncMock(
        return_value={"text": "Daily summary", "scores": {"mood": 81}}
    )

    with (
        patch(
            "lykke.infrastructure.gateways.openai_llm.settings",
            MagicMock(
                OPENAI_MODEL="gpt-4.1-mini",
                OPENAI_API_KEY="test-key",
            ),
        ),
        patch(
            "lykke.infrastructure.gateways.openai_llm.ChatOpenAI",
            return_value=mock_llm,
        ),
    ):
        gateway = OpenAILLMGateway()
        result = await gateway.run_assessment_usecase(
            system_prompt="You are a test assistant.",
            ask_prompt="Return a daily assessment.",
            assessment_model=AssessmentModel,
        )

    assert result is not None
    assert result.assessment.text == "Daily summary"
    assert result.assessment.scores["mood"] == 81
