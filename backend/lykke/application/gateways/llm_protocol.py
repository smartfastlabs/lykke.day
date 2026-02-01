"""Protocol for LLM gateway implementations."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

if TYPE_CHECKING:
    from pydantic import BaseModel

T = TypeVar("T")


@dataclass(frozen=True)
class LLMTool:
    """Tool definition for LLM calls."""

    callback: Callable[..., Awaitable[Any] | Any]
    name: str | None = None
    description: str | None = None
    prompt_notes: list[str] | None = None
    args_model: type[BaseModel] | None = None

    def __post_init__(self) -> None:
        if self.name is None:
            inferred_name = getattr(self.callback, "__name__", None) or "tool"
            object.__setattr__(self, "name", inferred_name)
        if self.description is None:
            inferred_description = inspect.getdoc(self.callback)
            if inferred_description:
                object.__setattr__(self, "description", inferred_description)


@dataclass(frozen=True)
class LLMToolCallResult:
    """Result for a tool call returned by the LLM."""

    tool_name: str
    arguments: dict[str, Any]
    result: Any


@dataclass(frozen=True)
class LLMToolRunResult:
    """Result for an LLM run that may include multiple tool calls."""

    tool_results: list[LLMToolCallResult]
    request_payload: dict[str, Any] | None = None


class LLMGatewayProtocol(Protocol):
    """Protocol defining the interface for LLM gateway implementations.

    This protocol allows the system to work with any LLM provider
    (Anthropic, OpenAI, etc.) as long as they implement this interface.
    """

    async def run_usecase(
        self,
        system_prompt: str,
        ask_prompt: str,
        tools: Sequence[LLMTool],
        metadata: dict[str, Any] | None = None,
    ) -> LLMToolRunResult | None:
        """Run an LLM use case and return the tool call result.

        Args:
            system_prompt: The system prompt defining the LLM's role and instructions
            ask_prompt: The specific ask prompt for the LLM
            tools: Tools available for the LLM to call
            metadata: Optional metadata for logging/diagnostics

        Returns:
            The tool call results or None if no completion was returned
        """
        raise NotImplementedError

    async def preview_usecase(
        self,
        system_prompt: str,
        ask_prompt: str,
        tools: Sequence[LLMTool],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Preview the exact request payload for an LLM use case.

        Args:
            system_prompt: The system prompt defining the LLM's role and instructions
            ask_prompt: The specific ask prompt for the LLM
            tools: Tools available for the LLM to call
            metadata: Optional metadata for logging/diagnostics

        Returns:
            Request payload that would be sent to the LLM provider
        """
        raise NotImplementedError
