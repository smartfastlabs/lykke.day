"""Base classes for LLM use cases."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date as datetime_date

from lykke.domain import value_objects


class BaseUseCase(ABC):
    """Base class for LLM use cases."""

    name: str
    template_usecase: str

    @abstractmethod
    async def build_prompt_context(
        self, date: datetime_date
    ) -> value_objects.LLMPromptContext:
        """Build the prompt context for this use case."""
