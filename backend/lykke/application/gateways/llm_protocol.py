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

    name: str | None = None
    callback: Callable[..., Awaitable[Any] | Any]
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
    result: Any


class LLMGatewayProtocol(Protocol):
    """Protocol defining the interface for LLM gateway implementations.

    This protocol allows the system to work with any LLM provider
    (Anthropic, OpenAI, etc.) as long as they implement this interface.
    """

    async def run_usecase(
        self,
        system_prompt: str,
        context_prompt: str,
        ask_prompt: str,
        tools: Sequence[LLMTool],
    ) -> LLMToolCallResult | None:
        """Run an LLM use case and return the tool call result.

        Args:
            system_prompt: The system prompt defining the LLM's role and instructions
            context_prompt: The user context prompt to evaluate
            ask_prompt: The specific ask prompt for the LLM
            tools: Tools available for the LLM to call

        Returns:
            The tool call result or None if no completion was returned
        """
        raise NotImplementedError
