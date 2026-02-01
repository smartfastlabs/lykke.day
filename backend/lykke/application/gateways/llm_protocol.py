"""Protocol for LLM gateway implementations."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, TypeVar, cast, get_type_hints

if TYPE_CHECKING:
    from pydantic import BaseModel
from pydantic import Field, create_model

T = TypeVar("T")


@dataclass(frozen=True)
class LLMTool:
    """Tool definition for LLM calls."""

    callback: Callable[..., Awaitable[Any] | Any]
    name: str = field(init=False)
    description: str | None = field(init=False)
    args_model: type[BaseModel] = field(init=False)

    def __post_init__(self) -> None:
        inferred_name = getattr(self.callback, "__name__", None) or "tool"
        object.__setattr__(self, "name", inferred_name)

        inferred_description = inspect.getdoc(self.callback)
        object.__setattr__(self, "description", inferred_description)

        args_model = self._build_args_model(self.callback, inferred_name)
        object.__setattr__(self, "args_model", args_model)

    @staticmethod
    def _build_args_model(
        callback: Callable[..., Awaitable[Any] | Any], tool_name: str
    ) -> type[BaseModel]:
        signature = inspect.signature(callback)
        hints = get_type_hints(callback)
        fields: dict[str, tuple[Any, Any]] = {}

        for name, param in signature.parameters.items():
            if name == "self":
                continue
            if param.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                raise ValueError("LLM tool callbacks must use named parameters")

            annotation = param.annotation
            if annotation is inspect.Parameter.empty:
                annotation = hints.get(name, Any)
            elif isinstance(annotation, str):
                annotation = hints.get(name, Any)
            default_value: Any = (
                ... if param.default is inspect.Parameter.empty else param.default
            )
            fields[name] = (annotation, Field(default=default_value))

        model_name = "".join(part.title() for part in tool_name.split("_")) + "Args"
        return create_model(model_name, **cast("dict[str, Any]", fields))


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
