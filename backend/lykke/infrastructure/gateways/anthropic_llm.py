"""Anthropic (Claude) LLM gateway implementation."""

import json
from collections.abc import Callable, Sequence
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from pydantic import SecretStr

from lykke.application.gateways.llm_protocol import LLMTool, LLMToolCallResult
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


def _extract_tool_call(
    response: Any, tool_names: Sequence[str]
) -> tuple[str, dict[str, Any]] | None:
    for tool_name in tool_names:
        tool_args = _extract_tool_call_args(response, tool_name)
        if tool_args is not None:
            return tool_name, tool_args
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
        tools: Sequence[LLMTool],
    ) -> LLMToolCallResult | None:
        """Run an LLM use case and return the on_complete result.

        Args:
            system_prompt: The system prompt defining the LLM's role and instructions
            context_prompt: The user context prompt to evaluate
            ask_prompt: The specific ask prompt for the LLM
            tools: Tools available for the LLM to call

        Returns:
            The tool call result or None if no completion was returned
        """
        try:
            if not tools:
                raise ValueError("At least one tool must be provided")

            tool_specs: list[dict[str, Any]] = []
            models_by_name: dict[str, Any] = {}
            callbacks_by_name: dict[str, Callable[..., Any]] = {}

            for tool in tools:
                tool_spec, model = build_tool_spec_from_callable(
                    tool.callback, tool_name=tool.name, description=tool.description
                )
                tool_specs.append(tool_spec)
                models_by_name[tool.name] = model
                callbacks_by_name[tool.name] = tool.callback
            # Call LLM with provided prompts
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=context_prompt),
                HumanMessage(content=ask_prompt),
            ]
            llm = self._llm.bind_tools(tool_specs)
            response = await llm.ainvoke(messages)

            tool_call = _extract_tool_call(response, list(models_by_name.keys()))
            if tool_call is None:
                logger.debug(
                    "LLM response missing tool call, falling back to content parsing"
                )

            if tool_call is None:
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

                parsed_data: Any = json.loads(response_text)
                tool_name: str | None = None
                tool_args: dict[str, Any] | None = None
                if isinstance(parsed_data, dict):
                    tool_name = parsed_data.get("tool_name") or parsed_data.get("name")
                    tool_args = parsed_data.get("args")
                    if tool_name and isinstance(tool_args, dict):
                        tool_call = (tool_name, tool_args)
                    elif len(models_by_name) == 1:
                        only_tool = next(iter(models_by_name.keys()))
                        tool_call = (only_tool, parsed_data)

            if tool_call is None:
                return None
            tool_name, tool_args = tool_call
            if tool_name not in models_by_name:
                logger.error(f"LLM selected unknown tool '{tool_name}'")
                return None

            validated = models_by_name[tool_name](**tool_args)
            result = callbacks_by_name[tool_name](**validated.model_dump())
            return LLMToolCallResult(tool_name=tool_name, result=result)

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
