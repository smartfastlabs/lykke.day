"""Unit tests for structured logging in LLM gateways."""

from __future__ import annotations

from typing import Any

import pytest

from lykke.application.gateways.llm_protocol import LLMTool
from lykke.infrastructure.gateways import anthropic_llm, openai_llm


class _FakeResponse:
    def __init__(self) -> None:
        self.tool_calls = [{"name": "echo_message", "args": {"message": "hello"}}]
        self.content = "OK"


class _FakeLLM:
    def __init__(self, **_kwargs: Any) -> None:
        pass

    def bind_tools(self, _tool_specs: list[dict[str, Any]]) -> _FakeLLM:
        return self

    async def ainvoke(self, _messages: list[object]) -> _FakeResponse:
        return _FakeResponse()


class _FakeStructuredGateway:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
        self.closed = False

    async def log_event(
        self,
        *,
        event_type: str,
        event_data: dict[str, Any],
        occurred_at,
    ) -> None:
        self.events.append(
            {
                "event_type": event_type,
                "event_data": event_data,
                "occurred_at": occurred_at,
            }
        )

    async def close(self) -> None:
        self.closed = True


def _echo_message(message: str) -> dict[str, str]:
    return {"message": message}


@pytest.mark.asyncio
async def test_openai_gateway_emits_structured_log(monkeypatch) -> None:
    fake_gateway = _FakeStructuredGateway()

    monkeypatch.setattr(openai_llm, "ChatOpenAI", _FakeLLM)
    monkeypatch.setattr(openai_llm, "StructuredLogGateway", lambda: fake_gateway)

    gateway = openai_llm.OpenAILLMGateway()
    result = await gateway.run_usecase(
        system_prompt="system",
        ask_prompt="ask",
        tools=[LLMTool(name="echo_message", callback=_echo_message)],
        metadata={"user_id": "user-1"},
    )

    assert result is not None
    assert fake_gateway.events
    event = fake_gateway.events[0]["event_data"]
    assert event["provider"] == "openai"
    assert event["metadata"]["user_id"] == "user-1"
    assert event["tool_calls"]
    assert event["tool_results"]


@pytest.mark.asyncio
async def test_anthropic_gateway_emits_structured_log(monkeypatch) -> None:
    fake_gateway = _FakeStructuredGateway()

    monkeypatch.setattr(anthropic_llm, "ChatAnthropic", _FakeLLM)
    monkeypatch.setattr(anthropic_llm, "StructuredLogGateway", lambda: fake_gateway)

    gateway = anthropic_llm.AnthropicLLMGateway()
    result = await gateway.run_usecase(
        system_prompt="system",
        ask_prompt="ask",
        tools=[LLMTool(name="echo_message", callback=_echo_message)],
        metadata={"user_id": "user-1"},
    )

    assert result is not None
    assert fake_gateway.events
    event = fake_gateway.events[0]["event_data"]
    assert event["provider"] == "anthropic"
    assert event["metadata"]["user_id"] == "user-1"
    assert event["tool_calls"]
    assert event["tool_results"]
