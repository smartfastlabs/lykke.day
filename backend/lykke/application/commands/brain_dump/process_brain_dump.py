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
from lykke.application.llm import LLMHandlerMixin, UseCasePromptInput
from lykke.application.queries.get_llm_prompt_context import (
    GetLLMPromptContextHandler,
    GetLLMPromptContextQuery,
)
from lykke.domain import value_objects

if TYPE_CHECKING:
    from datetime import date as dt_date, datetime, time
    from uuid import UUID

    from lykke.application.queries import GenerateUseCasePromptHandler
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
        generate_usecase_prompt_handler: GenerateUseCasePromptHandler,
        get_llm_prompt_context_handler: GetLLMPromptContextHandler,
        create_adhoc_task_handler: CreateAdhocTaskHandler,
        add_reminder_handler: AddReminderToDayHandler,
        update_reminder_status_handler: UpdateReminderStatusHandler,
        record_task_action_handler: RecordTaskActionHandler,
    ) -> None:
        super().__init__(ro_repos, uow_factory, user_id)
        self._generate_usecase_prompt_handler = generate_usecase_prompt_handler
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
        await self.run_llm()

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
            timing_type: value_objects.TimingType | None = None,
            available_time: time | None = None,
            start_time: time | None = None,
            end_time: time | None = None,
            tags: list[value_objects.TaskTag] | None = None,
        ) -> None:
            """Create a new task based on the brain dump item."""
            await self._mark_brain_dump_item_as_command(
                date=brain_dump_date,
                item_id=brain_dump_item.id,
            )

            has_times = any([available_time, start_time, end_time])
            if timing_type is None and has_times:
                timing_type = value_objects.TimingType.FLEXIBLE

            schedule = None
            if timing_type is not None:
                schedule = value_objects.TaskSchedule(
                    timing_type=timing_type,
                    available_time=available_time,
                    start_time=start_time,
                    end_time=end_time,
                )

            task_tags = tags or []
            await self._create_adhoc_task_handler.handle(
                CreateAdhocTaskCommand(
                    scheduled_date=brain_dump_date,
                    name=name,
                    category=category,
                    description=description,
                    schedule=schedule,
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
            updated = item.update_type(value_objects.BrainDumpItemType.COMMAND)
            if updated.has_events():
                uow.add(updated)
