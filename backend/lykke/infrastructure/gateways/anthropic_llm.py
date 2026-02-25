"""Anthropic (Claude) LLM gateway implementation."""

import inspect
import json
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from lykke.application.gateways.llm_protocol import (
    LLMTool,
    LLMToolCallResult,
    LLMToolRunResult,
)
from lykke.core.config import settings
from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.infrastructure.gateways.llm_tools import build_tool_spec_from_callable
from pydantic import SecretStr


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


def _extract_tool_calls_from_response(
    response: Any, tool_names: Sequence[str]
) -> list[tuple[str, dict[str, Any]]]:
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

    extracted: list[tuple[str, dict[str, Any]]] = []
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

        if not isinstance(name, str) or name not in tool_names:
            continue
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                continue
        if isinstance(args, dict):
            extracted.append((name, args))
    return extracted


def _extract_tool_calls_from_content(
    response_text: str, tool_names: Sequence[str]
) -> list[tuple[str, dict[str, Any]]]:
    parsed_data: Any = json.loads(response_text)
    extracted: list[tuple[str, dict[str, Any]]] = []
    if isinstance(parsed_data, dict):
        tool_name = parsed_data.get("tool_name") or parsed_data.get("name")
        tool_args = parsed_data.get("args")
        if tool_name and isinstance(tool_args, dict):
            extracted.append((tool_name, tool_args))
        elif len(tool_names) == 1:
            only_tool = next(iter(tool_names))
            extracted.append((only_tool, parsed_data))
    elif isinstance(parsed_data, list):
        for item in parsed_data:
            if not isinstance(item, dict):
                continue
            tool_name = item.get("tool_name") or item.get("name")
            tool_args = item.get("args")
            if tool_name and isinstance(tool_args, dict):
                extracted.append((tool_name, tool_args))
    return extracted


def _coerce_json_safe(value: Any) -> Any:
    try:
        serialized = dataclass_to_json_dict(value)
    except Exception:
        serialized = value
    try:
        json.dumps(serialized)
        return serialized
    except TypeError:
        return str(value)


def _is_model_not_found_error(exc: BaseException) -> bool:
    """True if the exception indicates Anthropic returned model not found (404)."""
    msg = str(exc).lower()
    return "404" in msg or "not_found_error" in msg or "model:" in msg


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
        ask_prompt: str,
        tools: Sequence[LLMTool],
        metadata: dict[str, Any] | None = None,
    ) -> LLMToolRunResult | None:
        """Run an LLM use case and return the on_complete result.

        Args:
            system_prompt: The system prompt defining the LLM's role and instructions
            ask_prompt: The specific ask prompt for the LLM
            tools: Tools available for the LLM to call

        Returns:
            The tool call result or None if no completion was returned
        """
        started_at = datetime.now(UTC)
        status = "success"
        tool_results_payload: list[dict[str, Any]] = []
        tool_calls_payload: list[dict[str, Any]] = []
        response_excerpt = ""
        response_length = 0
        error_info: dict[str, Any] | None = None
        effective_model = settings.ANTHROPIC_MODEL
        used_fallback = False

        try:
            if not tools:
                raise ValueError("At least one tool must be provided")

            tool_specs, models_by_name, callbacks_by_name = self._build_tool_data(tools)
            request_payload = await self.preview_usecase(
                system_prompt,
                ask_prompt,
                tools,
                metadata=metadata,
            )
            request_messages = request_payload.get("request_messages", [])
            messages = [
                SystemMessage(
                    content=request_messages[0]["content"]
                    if len(request_messages) > 0
                    else system_prompt
                ),
                HumanMessage(
                    content=request_messages[1]["content"]
                    if len(request_messages) > 1
                    else ask_prompt
                ),
            ]
            llm = self._llm.bind_tools(tool_specs)
            try:
                response = await llm.ainvoke(messages)
            except Exception as invoke_err:
                if _is_model_not_found_error(invoke_err) and (
                    settings.ANTHROPIC_FALLBACK_MODEL != settings.ANTHROPIC_MODEL
                ):
                    used_fallback = True
                    effective_model = settings.ANTHROPIC_FALLBACK_MODEL
                    logger.warning(
                        "Anthropic model not found, retrying with fallback",
                        configured_model=settings.ANTHROPIC_MODEL,
                        fallback_model=settings.ANTHROPIC_FALLBACK_MODEL,
                    )
                    fallback_llm = ChatAnthropic(
                        model_name=settings.ANTHROPIC_FALLBACK_MODEL,
                        api_key=SecretStr(settings.ANTHROPIC_API_KEY),
                        temperature=0.7,
                        timeout=None,
                        stop=None,
                    )
                    response = await fallback_llm.bind_tools(tool_specs).ainvoke(
                        messages
                    )
                else:
                    raise

            tool_calls = _extract_tool_calls_from_response(
                response, list(models_by_name.keys())
            )
            if not tool_calls:
                logger.debug(
                    "LLM response missing tool call, falling back to content parsing"
                )

            if not tool_calls:
                # Parse response content as a fallback
                response_text = _normalize_response_content(response.content).strip()
                response_length = len(response_text)
                response_excerpt = response_text[:2000]

                # Try to extract JSON from response (might be wrapped in markdown code blocks)
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()

                tool_calls = _extract_tool_calls_from_content(
                    response_text, list(models_by_name.keys())
                )

            if not tool_calls:
                status = "no_tool_calls"
                return None
            tool_results: list[LLMToolCallResult] = []
            for tool_name, tool_args in tool_calls:
                tool_calls_payload.append(
                    {"tool_name": tool_name, "arguments": _coerce_json_safe(tool_args)}
                )
                if tool_name not in models_by_name:
                    logger.error(f"LLM selected unknown tool '{tool_name}'")
                    continue
                validated = models_by_name[tool_name](**tool_args)
                result = callbacks_by_name[tool_name](**validated.model_dump())
                if inspect.isawaitable(result):
                    result = await result
                tool_results_payload.append(
                    {
                        "tool_name": tool_name,
                        "arguments": _coerce_json_safe(validated.model_dump()),
                        "result": _coerce_json_safe(result),
                    }
                )
                tool_results.append(
                    LLMToolCallResult(
                        tool_name=tool_name,
                        arguments=validated.model_dump(),
                        result=result,
                    )
                )
            if not tool_results:
                status = "no_tool_results"
                return None
            return LLMToolRunResult(
                tool_results=tool_results,
                request_payload=request_payload,
            )

        except json.JSONDecodeError as e:
            status = "error"
            error_info = {"type": "JSONDecodeError", "message": str(e)}
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(
                f"Response text: {response_text if 'response_text' in locals() else 'N/A'}"
            )
            return None
        except Exception as e:  # pylint: disable=broad-except
            status = "error"
            error_info = {"type": e.__class__.__name__, "message": str(e)}
            logger.error(f"Error running use case with Anthropic: {e}")
            if _is_model_not_found_error(e):
                logger.error(
                    "Anthropic model not found. Set ANTHROPIC_MODEL to a valid model id "
                    "(e.g. claude-sonnet-4-6). See https://docs.anthropic.com/en/api/models-list",
                    configured_model=settings.ANTHROPIC_MODEL,
                    fallback_attempted=used_fallback,
                    fallback_model=settings.ANTHROPIC_FALLBACK_MODEL,
                )
            logger.exception(e)
            return None
        finally:
            finished_at = datetime.now(UTC)
            event_data = {
                "source": "llm",
                "provider": "anthropic",
                "model": effective_model,
                "used_fallback": used_fallback,
                "status": status,
                "started_at": started_at.isoformat(),
                "finished_at": finished_at.isoformat(),
                "duration_ms": int((finished_at - started_at).total_seconds() * 1000),
                "metadata": _coerce_json_safe(metadata or {}),
                "prompts": {
                    "system": system_prompt,
                    "ask": ask_prompt,
                },
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                    }
                    for tool in tools
                ],
                "tool_calls": tool_calls_payload,
                "tool_results": tool_results_payload,
                "response_excerpt": response_excerpt,
                "response_length": response_length,
                "error": error_info,
            }

    async def preview_usecase(
        self,
        system_prompt: str,
        ask_prompt: str,
        tools: Sequence[LLMTool],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Preview the request payload for this LLM use case."""
        _ = metadata
        tool_specs, _, _ = self._build_tool_data(tools)
        request_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": ask_prompt},
        ]
        request_tool_choice = "auto"
        request_model_params = {
            "model": getattr(self._llm, "model_name", settings.ANTHROPIC_MODEL),
            "temperature": getattr(self._llm, "temperature", 0.7),
        }
        return {
            "request_messages": request_messages,
            "request_tools": [_coerce_json_safe(s) for s in tool_specs],
            "request_tool_choice": request_tool_choice,
            "request_model_params": request_model_params,
        }

    @staticmethod
    def _build_tool_data(
        tools: Sequence[LLMTool],
    ) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Callable[..., Any]]]:
        tool_specs: list[dict[str, Any]] = []
        models_by_name: dict[str, Any] = {}
        callbacks_by_name: dict[str, Callable[..., Any]] = {}

        for tool in tools:
            if tool.name is None:
                raise ValueError("LLM tool name cannot be None")
            tool_name = tool.name
            tool_spec, model = build_tool_spec_from_callable(
                tool.callback,
                tool_name=tool_name,
                description=tool.description,
            )
            tool_specs.append(tool_spec)
            models_by_name[tool_name] = model
            callbacks_by_name[tool_name] = tool.callback
        return tool_specs, models_by_name, callbacks_by_name
