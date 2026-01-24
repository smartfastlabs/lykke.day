"""Base classes for LLM use cases."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from lykke.application.gateways.llm_protocol import LLMTool

if TYPE_CHECKING:
    from datetime import date as datetime_date

    from lykke.domain import value_objects


@dataclass(frozen=True)
class UseCasePromptInput:
    """Prompt input for an LLM use case."""

    prompt_context: "value_objects.LLMPromptContext"
    extra_template_vars: dict[str, Any] | None = None


class BaseUseCase(ABC):
    """Base class for LLM use cases."""

    name: str
    template_usecase: str

    @abstractmethod
    async def build_prompt_input(self, date: datetime_date) -> UseCasePromptInput:
        """Build the prompt inputs for this use case."""

    @abstractmethod
    def build_tools(
        self,
        *,
        current_time: datetime,
        prompt_context: "value_objects.LLMPromptContext",
    ) -> list[LLMTool]:
        """Build tool definitions for this use case."""
