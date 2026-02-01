"""LLM-driven processing for inbound SMS messages.

Triggered asynchronously after an inbound SMS is persisted.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from typing import TYPE_CHECKING, Literal
from uuid import UUID

from loguru import logger

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.commands.day.add_alarm import (
    AddAlarmToDayCommand,
    AddAlarmToDayHandler,
)
from lykke.application.commands.task import (
    CreateAdhocTaskCommand,
    CreateAdhocTaskHandler,
    RecordTaskActionCommand,
    RecordTaskActionHandler,
)
from lykke.application.gateways.llm_gateway_factory_protocol import (
    LLMGatewayFactoryProtocol,
)
from lykke.application.gateways.llm_protocol import LLMTool
from lykke.application.gateways.sms_provider_protocol import SMSProviderProtocol
from lykke.application.llm import LLMHandlerMixin, LLMRunResult, UseCasePromptInput
from lykke.application.queries.get_llm_prompt_context import (
    GetLLMPromptContextHandler,
    GetLLMPromptContextQuery,
)
from lykke.core.utils.day_context_serialization import serialize_day_context
from lykke.core.utils.llm_snapshot import build_referenced_entities
from lykke.domain import value_objects
from lykke.domain.entities import MessageEntity
from lykke.domain.events.ai_chat_events import MessageSentEvent

if TYPE_CHECKING:
    from datetime import date as dt_date, datetime

    from lykke.application.unit_of_work import ReadOnlyRepositories, UnitOfWorkFactory


@dataclass(frozen=True)
class ProcessInboundSmsCommand(Command):
    """Command to process a stored inbound SMS message via LLM."""

    message_id: UUID


class ProcessInboundSmsHandler(
    LLMHandlerMixin, BaseCommandHandler[ProcessInboundSmsCommand, None]
):
    """Process an inbound SMS message into follow-up actions (reply, task, alarm, etc.)."""

    name = "process_inbound_sms"
    template_usecase = "process_inbound_sms"

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
        llm_gateway_factory: LLMGatewayFactoryProtocol,
        get_llm_prompt_context_handler: GetLLMPromptContextHandler,
        create_adhoc_task_handler: CreateAdhocTaskHandler,
        record_task_action_handler: RecordTaskActionHandler,
        add_alarm_to_day_handler: AddAlarmToDayHandler,
        sms_gateway: SMSProviderProtocol,
    ) -> None:
        super().__init__(ro_repos, uow_factory, user_id)
        self._llm_gateway_factory = llm_gateway_factory
        self._get_llm_prompt_context_handler = get_llm_prompt_context_handler
        self._create_adhoc_task_handler = create_adhoc_task_handler
        self._record_task_action_handler = record_task_action_handler
        self._add_alarm_to_day_handler = add_alarm_to_day_handler
        self._sms_gateway = sms_gateway

        self._inbound_message: MessageEntity | None = None

    async def handle(self, command: ProcessInboundSmsCommand) -> None:
        """Run LLM processing for an inbound message and apply actions."""
        try:
            message = await self.message_ro_repo.get(command.message_id)
        except Exception:  # pylint: disable=broad-except
            logger.debug("Inbound message %s not found", command.message_id)
            return

        # Only process inbound/user messages.
        if message.role != value_objects.MessageRole.USER:
            logger.debug(
                "Skipping processing for message %s role %s",
                message.id,
                message.role.value,
            )
            return

        from_number = message.meta.get("from_number")
        if not isinstance(from_number, str) or not from_number.strip():
            logger.debug(
                "Skipping inbound message %s: missing from_number metadata", message.id
            )
            return

        self._inbound_message = message
        llm_run_result = await self.run_llm()
        if llm_run_result is not None:
            await self._record_llm_run_result(
                message_id=message.id, result=llm_run_result
            )

    async def build_prompt_input(self, date: dt_date) -> UseCasePromptInput:
        if self._inbound_message is None:
            raise RuntimeError("Inbound message context was not initialized")

        prompt_context = await self._get_llm_prompt_context_handler.handle(
            GetLLMPromptContextQuery(date=date)
        )
        return UseCasePromptInput(
            prompt_context=prompt_context,
            extra_template_vars={"inbound_message": self._inbound_message},
        )

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
        self, *, message_id: UUID, result: LLMRunResult
    ) -> None:
        snapshot = self._build_llm_run_result_snapshot(result)
        async with self.new_uow() as uow:
            try:
                message = await uow.message_ro_repo.get(message_id)
            except Exception:  # pylint: disable=broad-except
                logger.debug(
                    "Message %s not found while recording llm_run_result", message_id
                )
                return
            updated = message.update_llm_run_result(snapshot)
            if updated is message:
                return
            uow.add(updated)

    def build_tools(
        self,
        *,
        current_time: datetime,
        prompt_context: value_objects.LLMPromptContext,
        llm_provider: value_objects.LLMProvider,
    ) -> list[LLMTool]:
        if self._inbound_message is None:
            raise RuntimeError("Inbound message context was not initialized")

        inbound_message = self._inbound_message
        _ = current_time
        _ = llm_provider

        from_number = inbound_message.meta.get("from_number")
        if not isinstance(from_number, str) or not from_number.strip():
            raise RuntimeError("Inbound message has no from_number")

        day_date = prompt_context.day.date

        async def reply(message: str) -> None:
            """Reply to the user via SMS."""
            body = message.strip()
            if not body:
                return

            # Persist the outgoing message first (auditable), then send SMS.
            async with self.new_uow() as uow:
                outgoing = MessageEntity(
                    user_id=self.user_id,
                    role=value_objects.MessageRole.ASSISTANT,
                    type=value_objects.MessageType.SMS_OUTBOUND,
                    content=body,
                    meta={
                        "provider": "twilio",
                        "to_number": from_number,
                        "in_reply_to_message_id": str(inbound_message.id),
                    },
                )
                outgoing.create()
                outgoing.add_event(
                    MessageSentEvent(
                        user_id=self.user_id,
                        message_id=outgoing.id,
                        role=outgoing.role.value,
                        content_preview=outgoing.get_content_preview(),
                    )
                )
                uow.add(outgoing)

            try:
                await self._sms_gateway.send_message(from_number, body)
            except Exception as exc:  # pylint: disable=broad-except
                logger.error("Failed sending SMS reply to %s: %s", from_number, exc)

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
            """Create a new task based on the inbound SMS."""
            time_window = None
            if any([available_time, start_time, end_time, cutoff_time]):
                time_window = value_objects.TimeWindow(
                    available_time=available_time,
                    start_time=start_time,
                    end_time=end_time,
                    cutoff_time=cutoff_time,
                )

            await self._create_adhoc_task_handler.handle(
                CreateAdhocTaskCommand(
                    scheduled_date=day_date,
                    name=name,
                    category=category,
                    description=description,
                    time_window=time_window,
                    tags=tags or [],
                )
            )

        async def add_reminder(reminder: str) -> None:
            """Create a new reminder (task type REMINDER) based on the inbound SMS."""
            await self._create_adhoc_task_handler.handle(
                CreateAdhocTaskCommand(
                    scheduled_date=day_date,
                    name=reminder,
                    category=value_objects.TaskCategory.PLANNING,
                    type=value_objects.TaskType.REMINDER,
                )
            )

        async def update_task(
            task_id: UUID, action: Literal["complete", "punt"]
        ) -> None:
            """Update an existing task when the inbound SMS implies a status change."""
            action_type = (
                value_objects.ActionType.COMPLETE
                if action == "complete"
                else value_objects.ActionType.PUNT
            )
            await self._record_task_action_handler.handle(
                RecordTaskActionCommand(
                    task_id=task_id,
                    action=value_objects.Action(
                        type=action_type, data={"source": "llm"}
                    ),
                )
            )

        async def add_alarm(
            alarm_time: time,
            name: str | None = None,
            url: str = "",
            alarm_type: value_objects.AlarmType = value_objects.AlarmType.URL,
        ) -> None:
            """Add an alarm to today's day (user-local time)."""
            await self._add_alarm_to_day_handler.handle(
                AddAlarmToDayCommand(
                    date=day_date,
                    name=name,
                    time=alarm_time,
                    alarm_type=alarm_type,
                    url=url,
                )
            )

        async def no_action(reason: str | None = None) -> None:
            """Take no action if the inbound SMS is informational only."""
            if reason:
                logger.debug(
                    "Inbound message %s has no action: %s", inbound_message.id, reason
                )

        return [
            LLMTool(
                callback=reply,
                prompt_notes=[
                    "Use when the user expects a response via SMS.",
                    "Keep replies concise and actionable.",
                ],
            ),
            LLMTool(
                callback=add_task,
                prompt_notes=[
                    "Use when the SMS contains a to-do or action.",
                    "category must be one of the TaskCategory enum values (UPPERCASE).",
                    "Time fields should be 24h format HH:MM.",
                ],
            ),
            LLMTool(
                callback=add_reminder,
                prompt_notes=["Use for simple, quick reminders."],
            ),
            LLMTool(
                callback=add_alarm,
                prompt_notes=[
                    "Use when the user asks to set an alarm.",
                    "alarm_time should be 24h format HH:MM.",
                ],
            ),
            LLMTool(
                callback=update_task,
                prompt_notes=[
                    "Use only when the SMS refers to an existing task.",
                    'action must be "complete" or "punt".',
                    "Never invent task IDs; only use IDs shown in the context.",
                ],
            ),
            LLMTool(
                callback=no_action,
                prompt_notes=["If unsure or no action needed, choose this."],
            ),
        ]
