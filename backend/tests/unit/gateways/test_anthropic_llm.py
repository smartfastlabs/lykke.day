"""Unit tests for Anthropic LLM gateway model-not-found fallback and error handling."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from lykke.application.gateways.llm_protocol import LLMTool
from lykke.infrastructure.gateways.anthropic_llm import (
    AnthropicLLMGateway,
    _is_model_not_found_error,
)


def test_is_model_not_found_error_404() -> None:
    """Detects 404 in exception message."""
    assert _is_model_not_found_error(ValueError("Error code: 404 - ...")) is True


def test_is_model_not_found_error_not_found_type() -> None:
    """Detects not_found_error in exception message."""
    assert (
        _is_model_not_found_error(
            ValueError("{'error': {'type': 'not_found_error', 'message': 'model: x'}}")
        )
        is True
    )


def test_is_model_not_found_error_model_prefix() -> None:
    """Detects 'model:' in exception message."""
    assert (
        _is_model_not_found_error(ValueError("model: claude-3-5-haiku-20241022"))
        is True
    )


def test_is_model_not_found_error_other() -> None:
    """Returns False for unrelated errors."""
    assert _is_model_not_found_error(ValueError("rate limit")) is False
    assert _is_model_not_found_error(ValueError("")) is False


@pytest.mark.asyncio
async def test_run_usecase_fallback_succeeds_when_configured_model_not_found() -> None:
    """First ainvoke raises model-not-found; retry with fallback model succeeds."""
    configured = "claude-3-5-haiku-20241022"
    fallback = "claude-sonnet-4-6"

    def echo_message(message: str) -> dict[str, str]:
        return {"message": message}

    tool = LLMTool(callback=echo_message)
    success_response = MagicMock()
    success_response.content = ""
    success_response.tool_calls = [
        MagicMock(name="echo_message", args={"message": "hello"})
    ]
    success_response.additional_kwargs = {}

    ainvoke_calls: list[int] = []

    async def ainvoke_side_effect(*_args: object, **_kwargs: object) -> MagicMock:
        ainvoke_calls.append(1)
        if len(ainvoke_calls) == 1:
            raise ValueError(
                "Error code: 404 - {'type': 'error', 'error': {'type': 'not_found_error', 'message': 'model: claude-3-5-haiku-20241022'}}"
            )
        return success_response

    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value.ainvoke = AsyncMock(
        side_effect=ainvoke_side_effect
    )

    with (
        patch(
            "app.infrastructure.gateways.anthropic_llm.settings",
            MagicMock(
                ANTHROPIC_MODEL=configured,
                ANTHROPIC_FALLBACK_MODEL=fallback,
                ANTHROPIC_API_KEY="test-key",
            ),
        ),
        patch(
            "app.infrastructure.gateways.anthropic_llm.ChatAnthropic",
            return_value=mock_llm,
        ),
    ):
        gateway = AnthropicLLMGateway()
        result = await gateway.run_usecase(
            system_prompt="You are a test assistant.",
            ask_prompt="Call echo_message with message 'hello'.",
            tools=[tool],
        )

    assert result is not None
    assert len(result.tool_results) == 1
    assert result.tool_results[0].tool_name == "echo_message"
    assert result.tool_results[0].result == {"message": "hello"}
    assert len(ainvoke_calls) == 2


@pytest.mark.asyncio
async def test_run_usecase_returns_none_when_fallback_also_fails() -> None:
    """Both configured model and fallback raise model-not-found; returns None."""
    configured = "bad-model"
    fallback = "claude-sonnet-4-6"
    error_msg = "Error code: 404 - not_found_error model: bad-model"

    def noop(message: str) -> dict[str, str]:
        return {"message": message}

    tool = LLMTool(callback=noop)
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value.ainvoke = AsyncMock(
        side_effect=ValueError(error_msg)
    )

    with (
        patch(
            "app.infrastructure.gateways.anthropic_llm.settings",
            MagicMock(
                ANTHROPIC_MODEL=configured,
                ANTHROPIC_FALLBACK_MODEL=fallback,
                ANTHROPIC_API_KEY="test-key",
            ),
        ),
        patch(
            "app.infrastructure.gateways.anthropic_llm.ChatAnthropic",
            return_value=mock_llm,
        ),
    ):
        gateway = AnthropicLLMGateway()
        result = await gateway.run_usecase(
            system_prompt="Test.",
            ask_prompt="Call noop.",
            tools=[tool],
        )

    assert result is None
    assert mock_llm.bind_tools.return_value.ainvoke.await_count == 2


@pytest.mark.asyncio
async def test_run_usecase_no_retry_when_non_model_error() -> None:
    """Other errors are not retried; single ainvoke and raise."""

    def noop(message: str) -> dict[str, str]:
        return {"message": message}

    tool = LLMTool(callback=noop)
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value.ainvoke = AsyncMock(
        side_effect=ValueError("Rate limit exceeded")
    )

    with (
        patch(
            "app.infrastructure.gateways.anthropic_llm.settings",
            MagicMock(
                ANTHROPIC_MODEL="claude-sonnet-4-6",
                ANTHROPIC_FALLBACK_MODEL="claude-sonnet-4-6",
                ANTHROPIC_API_KEY="test-key",
            ),
        ),
        patch(
            "app.infrastructure.gateways.anthropic_llm.ChatAnthropic",
            return_value=mock_llm,
        ),
    ):
        gateway = AnthropicLLMGateway()
        result = await gateway.run_usecase(
            system_prompt="Test.",
            ask_prompt="Call noop.",
            tools=[tool],
        )

    assert result is None
    assert mock_llm.bind_tools.return_value.ainvoke.await_count == 1
