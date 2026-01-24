"""Anthropic (Claude) LLM gateway implementation."""

import json
from collections.abc import Callable
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from pydantic import SecretStr

from lykke.core.config import settings
from lykke.infrastructure.gateways.llm_tools import build_tool_spec_from_callable


def _normalize_response_content(content: str | list[str | dict[str, Any]]) -> str:
    if isinstance(content, str):
        return content

    parts: list[str] = []
    for item in content:
        if isinstance(item, str):
            parts.append(item)
            continue
        if isinstance(item, dict):
            text = item.get("text")
            if isinstance(text, str):
                parts.append(text)
            else:
                parts.append(json.dumps(item))
    return "\n".join(parts)


def _extract_tool_call_args(response: Any, tool_name: str) -> dict[str, Any] | None:
    tool_calls: list[Any] = []
    if getattr(response, "tool_calls", None):
        tool_calls = list(response.tool_calls)
    if not tool_calls:
        additional_kwargs = getattr(response, "additional_kwargs", {}) or {}
        raw_calls = additional_kwargs.get("tool_calls") or additional_kwargs.get(
            "tool_call"
        )
        if raw_calls:
            tool_calls = raw_calls if isinstance(raw_calls, list) else [raw_calls]

    for call in tool_calls:
        name: str | None = None
        args: Any = None
        if isinstance(call, dict):
            name = call.get("name") or call.get("function", {}).get("name")
            args = call.get("args") or call.get("arguments")
            if args is None:
                args = call.get("function", {}).get("arguments")
        else:
            name = getattr(call, "name", None)
            args = getattr(call, "args", None)

        if name != tool_name:
            continue
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                return None
        if isinstance(args, dict):
            return args
    return None


class AnthropicLLMGateway:
    """Anthropic (Claude) implementation of LLM gateway."""

    def __init__(self) -> None:
        """Initialize Anthropic LLM gateway."""
        self._llm = ChatAnthropic(
            model_name=settings.ANTHROPIC_MODEL,
            api_key=SecretStr(settings.ANTHROPIC_API_KEY),
            temperature=0.7,
            timeout=None,
            stop=None,
        )

    async def run_usecase(
        self,
        system_prompt: str,
        context_prompt: str,
        ask_prompt: str,
        on_complete: Callable[..., Any],
    ) -> Any | None:
        """Run an LLM use case and return the on_complete result.

        Args:
            system_prompt: The system prompt defining the LLM's role and instructions
            context_prompt: The user context prompt to evaluate
            ask_prompt: The specific ask prompt for the LLM
            on_complete: Callback invoked with tool arguments

        Returns:
            The on_complete result or None if no completion was returned
        """
        try:
            tool_spec, model = build_tool_spec_from_callable(on_complete)
            tools = [tool_spec]
            default_tool_name = tool_spec["name"]
            # Call LLM with provided prompts
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=context_prompt),
                HumanMessage(content=ask_prompt),
            ]
            llm = self._llm.bind_tools(tools)
            response = await llm.ainvoke(messages)

            decision_data: dict[str, Any] | None = None
            decision_data = _extract_tool_call_args(response, default_tool_name)
            if decision_data is None:
                logger.debug(
                    f"LLM response missing tool call '{default_tool_name}', "
                    "falling back to content parsing"
                )

            if decision_data is None:
                # Parse response content as a fallback
                response_text = _normalize_response_content(response.content).strip()

                # Try to extract JSON from response (might be wrapped in markdown code blocks)
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()

                decision_data = json.loads(response_text)

            if not isinstance(decision_data, dict):
                return None

            validated = model(**decision_data)
            return on_complete(**validated.model_dump())

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(
                f"Response text: {response_text if 'response_text' in locals() else 'N/A'}"
            )
            return None
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Error running use case with Anthropic: {e}")
            logger.exception(e)
            return None
