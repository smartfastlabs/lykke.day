"""Command to process brain dump items with LLM."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as dt_date
from typing import Any
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
from lykke.application.llm_usecases import LLMUseCaseRunner, ProcessBrainDumpUseCase
from lykke.application.queries.get_llm_prompt_context import GetLLMPromptContextHandler
from lykke.application.unit_of_work import ReadOnlyRepositories, UnitOfWorkFactory
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity


@dataclass(frozen=True)
class ProcessBrainDumpCommand(Command):
    """Command to process a single brain dump item."""

    date: dt_date
    item_id: UUID


class ProcessBrainDumpHandler(BaseCommandHandler[ProcessBrainDumpCommand, None]):
    """Process brain dump items into follow-up actions."""

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
        llm_usecase_runner: LLMUseCaseRunner,
        get_llm_prompt_context_handler: GetLLMPromptContextHandler,
        create_adhoc_task_handler: CreateAdhocTaskHandler,
        add_reminder_handler: AddReminderToDayHandler,
        update_reminder_status_handler: UpdateReminderStatusHandler,
        record_task_action_handler: RecordTaskActionHandler,
    ) -> None:
        super().__init__(ro_repos, uow_factory, user_id)
        self._llm_usecase_runner = llm_usecase_runner
        self._get_llm_prompt_context_handler = get_llm_prompt_context_handler
        self._create_adhoc_task_handler = create_adhoc_task_handler
        self._add_reminder_handler = add_reminder_handler
        self._update_reminder_status_handler = update_reminder_status_handler
        self._record_task_action_handler = record_task_action_handler

    async def handle(self, command: ProcessBrainDumpCommand) -> None:
        """Run LLM processing for a brain dump item and apply actions."""
        day_id = DayEntity.id_from_date_and_user(command.date, self.user_id)
        day = await self.day_ro_repo.get(day_id)
        item = next(
            (item for item in day.brain_dump_items if item.id == command.item_id),
            None,
        )
        if item is None:
            logger.debug(
                "Brain dump item %s not found for day %s",
                command.item_id,
                command.date,
            )
            return

        usecase = ProcessBrainDumpUseCase(
            get_llm_prompt_context_handler=self._get_llm_prompt_context_handler,
            brain_dump_item=item,
            brain_dump_date=command.date,
        )
        usecase_result = await self._llm_usecase_runner.run(usecase=usecase)
        if usecase_result is None:
            return

        tool_name = usecase_result.tool_name
        result = usecase_result.result
        if tool_name == "no_action":
            logger.debug(
                "No action for brain dump item %s (user %s)",
                command.item_id,
                self.user_id,
            )
            return
        await self._mark_brain_dump_item_as_command(
            date=command.date,
            item_id=command.item_id,
        )
        if not isinstance(result, dict):
            logger.error(
                "Unexpected result for brain dump tool %s: %s", tool_name, result
            )
            return

        if tool_name == "add_task":
            await self._handle_add_task(command.date, result)
            return
        if tool_name == "add_reminder":
            await self._handle_add_reminder(command.date, result)
            return
        if tool_name == "update_task":
            await self._handle_update_task(result)
            return
        if tool_name == "update_reminder":
            await self._handle_update_reminder(command.date, result)
            return

        logger.error("Unknown brain dump tool: %s", tool_name)

    async def _mark_brain_dump_item_as_command(
        self, *, date: dt_date, item_id: UUID
    ) -> None:
        async with self.new_uow() as uow:
            day_id = DayEntity.id_from_date_and_user(date, self.user_id)
            day = await uow.day_ro_repo.get(day_id)

            item_index = None
            existing_item = None
            for i, item in enumerate(day.brain_dump_items):
                if item.id == item_id:
                    item_index = i
                    existing_item = item
                    break

            if item_index is None or existing_item is None:
                logger.debug(
                    "Brain dump item %s not found for day %s",
                    item_id,
                    date,
                )
                return

            if existing_item.type == value_objects.BrainDumpItemType.COMMAND:
                return

            updated_item = value_objects.BrainDumpItem(
                id=existing_item.id,
                text=existing_item.text,
                status=existing_item.status,
                created_at=existing_item.created_at,
                type=value_objects.BrainDumpItemType.COMMAND,
            )

            updated_items = list(day.brain_dump_items)
            updated_items[item_index] = updated_item
            day.brain_dump_items = updated_items
            uow.add(day)

    async def _handle_add_task(self, date: dt_date, result: dict[str, Any]) -> None:
        name = result.get("name")
        category = result.get("category")
        if not isinstance(name, str) or not isinstance(
            category, value_objects.TaskCategory
        ):
            logger.error("Invalid add_task result: %s", result)
            return

        timing_type = result.get("timing_type")
        available_time = result.get("available_time")
        start_time = result.get("start_time")
        end_time = result.get("end_time")
        has_times = any([available_time, start_time, end_time])

        if timing_type is None and has_times:
            timing_type = value_objects.TimingType.FLEXIBLE

        schedule = None
        if isinstance(timing_type, value_objects.TimingType):
            schedule = value_objects.TaskSchedule(
                timing_type=timing_type,
                available_time=available_time,
                start_time=start_time,
                end_time=end_time,
            )

        tags = result.get("tags") or []
        if not isinstance(tags, list):
            tags = []
        tags = [tag for tag in tags if isinstance(tag, value_objects.TaskTag)]

        await self._create_adhoc_task_handler.handle(
            CreateAdhocTaskCommand(
                scheduled_date=date,
                name=name,
                category=category,
                description=result.get("description"),
                schedule=schedule,
                tags=tags,
            )
        )

    async def _handle_add_reminder(self, date: dt_date, result: dict[str, Any]) -> None:
        reminder = result.get("reminder")
        if not isinstance(reminder, str):
            logger.error("Invalid add_reminder result: %s", result)
            return
        await self._add_reminder_handler.handle(
            AddReminderToDayCommand(date=date, reminder=reminder)
        )

    async def _handle_update_task(self, result: dict[str, Any]) -> None:
        task_id = result.get("task_id")
        action = result.get("action")
        if not isinstance(task_id, UUID) or not isinstance(action, str):
            logger.error("Invalid update_task result: %s", result)
            return
        if action == "complete":
            action_type = value_objects.ActionType.COMPLETE
        elif action == "punt":
            action_type = value_objects.ActionType.PUNT
        else:
            logger.error("Unsupported update_task action: %s", action)
            return

        await self._record_task_action_handler.handle(
            RecordTaskActionCommand(
                task_id=task_id,
                action=value_objects.Action(type=action_type, data={"source": "llm"}),
            )
        )

    async def _handle_update_reminder(
        self, date: dt_date, result: dict[str, Any]
    ) -> None:
        reminder_id = result.get("reminder_id")
        status = result.get("status")
        if not isinstance(reminder_id, UUID) or not isinstance(
            status, value_objects.ReminderStatus
        ):
            logger.error("Invalid update_reminder result: %s", result)
            return
        await self._update_reminder_status_handler.handle(
            UpdateReminderStatusCommand(
                date=date,
                reminder_id=reminder_id,
                status=status,
            )
        )
