"""LLM use case for processing brain dump items."""

from __future__ import annotations

from datetime import datetime, time
from typing import TYPE_CHECKING, Any, Literal
from uuid import UUID

from lykke.application.gateways.llm_protocol import LLMTool
from lykke.application.queries.get_llm_prompt_context import (
    GetLLMPromptContextHandler,
    GetLLMPromptContextQuery,
)
from lykke.domain import value_objects

from .base import BaseUseCase, UseCasePromptInput

if TYPE_CHECKING:
    from datetime import date as datetime_date


class ProcessBrainDumpUseCase(BaseUseCase):
    """Use case for turning brain dump items into actions."""

    name = "process_brain_dump"
    template_usecase = "process_brain_dump"

    def __init__(
        self,
        *,
        get_llm_prompt_context_handler: GetLLMPromptContextHandler,
        brain_dump_item: value_objects.BrainDumpItem,
        brain_dump_date: datetime_date,
    ) -> None:
        self._get_llm_prompt_context_handler = get_llm_prompt_context_handler
        self._brain_dump_item = brain_dump_item
        self._brain_dump_date = brain_dump_date

    async def build_prompt_input(self, date: datetime_date) -> UseCasePromptInput:
        prompt_context = await self._get_llm_prompt_context_handler.handle(
            GetLLMPromptContextQuery(date=self._brain_dump_date)
        )
        return UseCasePromptInput(
            prompt_context=prompt_context,
            extra_template_vars={
                "brain_dump_item": self._brain_dump_item,
                "brain_dump_date": self._brain_dump_date,
            },
        )

    def build_tools(
        self,
        *,
        current_time: datetime,
        prompt_context: value_objects.LLMPromptContext,
    ) -> list[LLMTool]:
        def add_task(
            name: str,
            category: value_objects.TaskCategory,
            description: str | None = None,
            timing_type: value_objects.TimingType | None = None,
            available_time: time | None = None,
            start_time: time | None = None,
            end_time: time | None = None,
            tags: list[value_objects.TaskTag] | None = None,
        ) -> dict[str, Any]:
            """Create a new task based on the brain dump item."""
            return {
                "name": name,
                "category": category,
                "description": description,
                "timing_type": timing_type,
                "available_time": available_time,
                "start_time": start_time,
                "end_time": end_time,
                "tags": tags or [],
            }

        def add_reminder(reminder: str) -> dict[str, Any]:
            """Create a new reminder based on the brain dump item."""
            return {"reminder": reminder}

        def update_task(
            task_id: UUID,
            action: Literal["complete", "punt"],
        ) -> dict[str, Any]:
            """Update an existing task when the brain dump implies a status change."""
            return {"task_id": task_id, "action": action}

        def update_reminder(
            reminder_id: UUID, status: value_objects.ReminderStatus
        ) -> dict[str, Any]:
            """Update an existing reminder's status."""
            return {"reminder_id": reminder_id, "status": status}

        def no_action(reason: str | None = None) -> dict[str, Any]:
            """Take no action if the brain dump is informational only."""
            return {"reason": reason}

        return [
            LLMTool(
                name="add_task",
                callback=add_task,
                description="Create a new task inferred from the brain dump.",
            ),
            LLMTool(
                name="add_reminder",
                callback=add_reminder,
                description="Create a new reminder inferred from the brain dump.",
            ),
            LLMTool(
                name="update_task",
                callback=update_task,
                description="Update an existing task's status if implied.",
            ),
            LLMTool(
                name="update_reminder",
                callback=update_reminder,
                description="Update an existing reminder's status if implied.",
            ),
            LLMTool(
                name="no_action",
                callback=no_action,
                description="Use when no task or reminder should be created.",
            ),
        ]
