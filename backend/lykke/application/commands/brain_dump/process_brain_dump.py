"""Command to process brain dump items with LLM."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from typing import TYPE_CHECKING, Literal
from uuid import UUID

from loguru import logger

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.commands.day import (
    AddReminderToDayCommand,
    AddReminderToDayHandler,
    UpdateReminderStatusCommand,
    UpdateReminderStatusHandler,
)
from lykke.application.commands.task import (
    CreateAdhocTaskCommand,
    CreateAdhocTaskHandler,
    RecordTaskActionCommand,
    RecordTaskActionHandler,
)
from lykke.application.gateways.llm_protocol import LLMTool
from lykke.application.llm import LLMHandlerMixin, LLMRunResult, UseCasePromptInput
from lykke.application.queries.get_llm_prompt_context import (
    GetLLMPromptContextHandler,
    GetLLMPromptContextQuery,
)
from lykke.core.utils.day_context_serialization import serialize_day_context
from lykke.core.utils.llm_snapshot import build_referenced_entities
from lykke.domain import value_objects

if TYPE_CHECKING:
    from datetime import date as dt_date, datetime, time
    from uuid import UUID

    from lykke.application.unit_of_work import ReadOnlyRepositories, UnitOfWorkFactory
    from lykke.domain.entities import BrainDumpEntity


@dataclass(frozen=True)
class ProcessBrainDumpCommand(Command):
    """Command to process a single brain dump item."""

    date: dt_date
    item_id: UUID


class ProcessBrainDumpHandler(
    LLMHandlerMixin, BaseCommandHandler[ProcessBrainDumpCommand, None]
):
    """Process brain dump items into follow-up actions."""

    name = "process_brain_dump"
    template_usecase = "process_brain_dump"

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
        get_llm_prompt_context_handler: GetLLMPromptContextHandler,
        create_adhoc_task_handler: CreateAdhocTaskHandler,
        add_reminder_handler: AddReminderToDayHandler,
        update_reminder_status_handler: UpdateReminderStatusHandler,
        record_task_action_handler: RecordTaskActionHandler,
    ) -> None:
        super().__init__(ro_repos, uow_factory, user_id)
        self._get_llm_prompt_context_handler = get_llm_prompt_context_handler
        self._create_adhoc_task_handler = create_adhoc_task_handler
        self._add_reminder_handler = add_reminder_handler
        self._update_reminder_status_handler = update_reminder_status_handler
        self._record_task_action_handler = record_task_action_handler
        self._brain_dump_item: BrainDumpEntity | None = None
        self._brain_dump_date: dt_date | None = None

    async def handle(self, command: ProcessBrainDumpCommand) -> None:
        """Run LLM processing for a brain dump item and apply actions."""
        try:
            item = await self.brain_dump_ro_repo.get(command.item_id)
        except Exception:
            logger.debug(
                "Brain dump item %s not found for day %s",
                command.item_id,
                command.date,
            )
            return
        if item.date != command.date:
            logger.debug(
                "Brain dump item %s not found for day %s",
                command.item_id,
                command.date,
            )
            return

        self._brain_dump_item = item
        self._brain_dump_date = command.date
        llm_run_result = await self.run_llm()
        if llm_run_result is not None:
            await self._record_llm_run_result(
                date=command.date,
                item_id=item.id,
                result=llm_run_result,
            )

    async def build_prompt_input(self, date: dt_date) -> UseCasePromptInput:
        if self._brain_dump_item is None or self._brain_dump_date is None:
            raise RuntimeError("Brain dump context was not initialized")
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
        llm_provider: value_objects.LLMProvider,
    ) -> list[LLMTool]:
        if self._brain_dump_item is None or self._brain_dump_date is None:
            raise RuntimeError("Brain dump context was not initialized")
        brain_dump_item = self._brain_dump_item
        brain_dump_date = self._brain_dump_date
        _ = current_time
        _ = prompt_context
        _ = llm_provider

        async def add_task(
            name: str,
            category: value_objects.TaskCategory,
            description: str | None = None,
            available_time: time | None = None,
            start_time: time | None = None,
            end_time: time | None = None,
            cutoff_time: time | None = None,
            tags: list[value_objects.TaskTag] | None = None,
        ) -> None:
            """Create a new task based on the brain dump item."""
            await self._mark_brain_dump_item_as_command(
                date=brain_dump_date,
                item_id=brain_dump_item.id,
            )

            time_window = None
            if any([available_time, start_time, end_time, cutoff_time]):
                time_window = value_objects.TimeWindow(
                    available_time=available_time,
                    start_time=start_time,
                    end_time=end_time,
                    cutoff_time=cutoff_time,
                )

            task_tags = tags or []
            await self._create_adhoc_task_handler.handle(
                CreateAdhocTaskCommand(
                    scheduled_date=brain_dump_date,
                    name=name,
                    category=category,
                    description=description,
                    time_window=time_window,
                    tags=task_tags,
                )
            )

        async def add_reminder(reminder: str) -> None:
            """Create a new reminder based on the brain dump item."""
            await self._mark_brain_dump_item_as_command(
                date=brain_dump_date,
                item_id=brain_dump_item.id,
            )
            await self._add_reminder_handler.handle(
                AddReminderToDayCommand(date=brain_dump_date, reminder=reminder)
            )

        async def update_task(
            task_id: UUID,
            action: Literal["complete", "punt"],
        ) -> None:
            """Update an existing task when the brain dump implies a status change."""
            await self._mark_brain_dump_item_as_command(
                date=brain_dump_date,
                item_id=brain_dump_item.id,
            )
            if action == "complete":
                action_type = value_objects.ActionType.COMPLETE
            else:
                action_type = value_objects.ActionType.PUNT

            await self._record_task_action_handler.handle(
                RecordTaskActionCommand(
                    task_id=task_id,
                    action=value_objects.Action(
                        type=action_type, data={"source": "llm"}
                    ),
                )
            )

        async def update_reminder(
            reminder_id: UUID,
            status: value_objects.ReminderStatus,
        ) -> None:
            """Update an existing reminder's status."""
            await self._mark_brain_dump_item_as_command(
                date=brain_dump_date,
                item_id=brain_dump_item.id,
            )
            await self._update_reminder_status_handler.handle(
                UpdateReminderStatusCommand(
                    date=brain_dump_date,
                    reminder_id=reminder_id,
                    status=status,
                )
            )

        async def no_action(reason: str | None = None) -> None:
            """Take no action if the brain dump is informational only."""
            if reason:
                logger.debug(
                    "Brain dump item %s has no action: %s",
                    brain_dump_item.id,
                    reason,
                )

        return [
            LLMTool(
                callback=add_task,
                prompt_notes=[
                    "Use when the item is a to-do or action.",
                    "category must be one of the TaskCategory enum values (UPPERCASE).",
                    "Time fields (available_time, start_time, end_time, cutoff_time) should be 24h format HH:MM.",
                ],
            ),
            LLMTool(
                callback=add_reminder,
                prompt_notes=["Use for simple, quick reminders."],
            ),
            LLMTool(
                callback=update_task,
                prompt_notes=[
                    "Use only when the item refers to an existing task.",
                    'action must be "complete" or "punt".',
                ],
            ),
            LLMTool(
                callback=update_reminder,
                prompt_notes=[
                    "Use only when the item refers to an existing reminder.",
                    "status must be one of the ReminderStatus enum values (UPPERCASE).",
                ],
            ),
            LLMTool(
                callback=no_action,
                prompt_notes=["If unsure or no action needed, choose this."],
            ),
        ]

    async def _mark_brain_dump_item_as_command(
        self, *, date: dt_date, item_id: UUID
    ) -> None:
        async with self.new_uow() as uow:
            try:
                item = await uow.brain_dump_ro_repo.get(item_id)
            except Exception:
                logger.debug(
                    "Brain dump item %s not found for day %s",
                    item_id,
                    date,
                )
                return
            if item.date != date:
                logger.debug(
                    "Brain dump item %s not found for day %s",
                    item_id,
                    date,
                )
                return
            updated = item.update_type(value_objects.BrainDumpType.COMMAND)
            if updated.has_events():
                uow.add(updated)

    def _build_llm_run_result_snapshot(
        self, result: LLMRunResult
    ) -> value_objects.LLMRunResultSnapshot:
        prompt_context_snapshot = serialize_day_context(
            result.prompt_context, current_time=result.current_time
        )
        referenced_entities = build_referenced_entities(result.prompt_context)
        tool_calls = [
            value_objects.LLMToolCallResultSnapshot(
                tool_name=tool_result.tool_name,
                arguments=tool_result.arguments,
                result=tool_result.result,
            )
            for tool_result in result.tool_results
        ]
        return value_objects.LLMRunResultSnapshot(
            tool_calls=tool_calls,
            prompt_context=prompt_context_snapshot,
            current_time=result.current_time,
            llm_provider=result.llm_provider,
            system_prompt=result.system_prompt,
            context_prompt=result.context_prompt,
            ask_prompt=result.ask_prompt,
            tools_prompt=result.tools_prompt,
            referenced_entities=referenced_entities,
        )

    async def _record_llm_run_result(
        self, *, date: dt_date, item_id: UUID, result: LLMRunResult
    ) -> None:
        snapshot = self._build_llm_run_result_snapshot(result)
        async with self.new_uow() as uow:
            try:
                item = await uow.brain_dump_ro_repo.get(item_id)
            except Exception:
                logger.debug(
                    "Brain dump item %s not found for day %s",
                    item_id,
                    date,
                )
                return
            if item.date != date:
                logger.debug(
                    "Brain dump item %s not found for day %s",
                    item_id,
                    date,
                )
                return
            updated = item.update_llm_run_result(snapshot)
            if updated is item:
                return
            uow.add(updated)
