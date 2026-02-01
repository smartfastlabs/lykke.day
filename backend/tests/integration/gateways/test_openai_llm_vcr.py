"""Integration test for Anthropic gateway with VCR."""

import os

import pytest

from lykke.application.gateways.llm_protocol import LLMTool
from lykke.infrastructure.gateways.anthropic_llm import AnthropicLLMGateway


@pytest.mark.asyncio
@pytest.mark.vcr(
    cassette_library_dir="tests/integration/cassettes",
    cassette_name="anthropic_llm_simple_tool",
)
async def test_anthropic_llm_gateway_with_vcr() -> None:
    """Record or replay a simple Anthropic tool call via VCR."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY is required to record the cassette.")

    def echo_message(message: str) -> dict[str, str]:
        """Echo a message."""
        return {"message": message}

    gateway = AnthropicLLMGateway()
    result = await gateway.run_usecase(
        system_prompt="You are a test assistant.",
        ask_prompt="Call the echo_message tool with message 'hello'.",
        tools=[
            LLMTool(callback=echo_message)
        ],
    )

    assert result is not None
    assert len(result.tool_results) == 1
    tool_result = result.tool_results[0]
    assert tool_result.tool_name == "echo_message"
    assert isinstance(tool_result.result, dict)
    assert tool_result.result.get("message") == "hello"
