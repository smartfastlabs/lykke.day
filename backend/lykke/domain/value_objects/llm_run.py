from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from .ai_chat import LLMProvider
from .base import BaseValueObject


@dataclass(kw_only=True)
class LLMReferencedEntitySnapshot(BaseValueObject):
    """Serializable snapshot of an entity referenced by an LLM run."""

    entity_type: str
    entity_id: UUID


@dataclass(kw_only=True)
class LLMToolCallResultSnapshot(BaseValueObject):
    """Serializable snapshot of a single LLM tool call result."""

    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    result: Any


@dataclass(kw_only=True)
class LLMRunResultSnapshot(BaseValueObject):
    """Serializable snapshot of an LLM run."""

    current_time: datetime
    llm_provider: LLMProvider
    system_prompt: str
    referenced_entities: list[LLMReferencedEntitySnapshot] = field(default_factory=list)
    # Exact request payload sent to the LLM (optional, for debugging)
    messages: list[dict[str, Any]] | None = None
    tools: list[dict[str, Any]] | None = None
    tool_choice: Any = None
    model_params: dict[str, Any] | None = None
