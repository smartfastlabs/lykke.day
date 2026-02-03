"""Query for building a synthetic LLM run snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from typing import Any, Literal
from uuid import UUID

from lykke.application.gateways.llm_gateway_factory_protocol import (
    LLMGatewayFactoryProtocol,
)
from lykke.application.gateways.llm_protocol import LLMTool
from lykke.application.llm.prompt_rendering import (
    combine_system_prompt,
    render_ask_prompt,
    render_context_prompt,
    render_system_prompt,
)
from lykke.application.llm.tools_prompt import render_tools_prompt
from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.queries.get_llm_prompt_context import (
    GetLLMPromptContextHandler,
    GetLLMPromptContextQuery,
)
from lykke.core.exceptions import DomainError
from lykke.core.utils.dates import get_current_date, get_current_datetime_in_timezone
from lykke.core.utils.llm_snapshot import build_referenced_entities
from lykke.domain import value_objects
from lykke.domain.entities import MessageEntity


@dataclass(frozen=True)
class PreviewLLMSnapshotQuery(Query):
    """Query to build a synthetic LLM run snapshot."""

    usecase: str


class PreviewLLMSnapshotHandler(
    BaseQueryHandler[PreviewLLMSnapshotQuery, value_objects.LLMRunResultSnapshot | None]
):
    """Builds a synthetic LLM snapshot for a given usecase."""
    get_llm_prompt_context_handler: GetLLMPromptContextHandler
    llm_gateway_factory: LLMGatewayFactoryProtocol

    async def handle(
        self, query: PreviewLLMSnapshotQuery
    ) -> value_objects.LLMRunResultSnapshot | None:
        """Build a synthetic snapshot without running the LLM."""
        if query.usecase not in {
            "notification",
            "morning_overview",
            "process_inbound_sms",
        }:
            return None

        user = self.user
        if not user.settings or not user.settings.llm_provider:
            return None

        current_time = get_current_datetime_in_timezone(user.settings.timezone)
        current_date = get_current_date(user.settings.timezone)
        prompt_context = await self.get_llm_prompt_context_handler.handle(
            GetLLMPromptContextQuery(date=current_date)
        )

        if query.usecase == "notification":
            tools = self._build_notification_tools()
        elif query.usecase == "morning_overview":
            tools = self._build_morning_overview_tools()
        else:
            send_acknowledgment = await self._get_send_acknowledgment(query.usecase)
            tools = self._build_inbound_sms_tools(send_acknowledgment)

        tools_prompt = render_tools_prompt(tools)

        if query.usecase in {"notification", "morning_overview"}:
            extra_template_vars: dict[str, Any] = {"tools_prompt": tools_prompt}
        else:
            inbound_message = MessageEntity(
                user_id=self.user.id,
                role=value_objects.MessageRole.USER,
                type=value_objects.MessageType.SMS_INBOUND,
                content="Reminder: call the vet tomorrow at 9am.",
                meta={"provider": "twilio", "from_number": "+15555550123"},
                created_at=current_time,
            )
            extra_template_vars = {
                "tools_prompt": tools_prompt,
                "inbound_message": inbound_message,
                "send_acknowledgment": send_acknowledgment,
            }

        system_prompt = await render_system_prompt(
            usecase=query.usecase,
            user=user,
            usecase_config_ro_repo=self.usecase_config_ro_repo,
        )
        context_prompt = render_context_prompt(
            usecase=query.usecase,
            prompt_context=prompt_context,
            current_time=current_time,
            extra_template_vars=extra_template_vars,
        )
        ask_prompt = render_ask_prompt(
            usecase=query.usecase, extra_template_vars=extra_template_vars
        )
        combined_system_prompt = combine_system_prompt(
            system_prompt=system_prompt, context_prompt=context_prompt
        )

        try:
            llm_gateway = self.llm_gateway_factory.create_gateway(
                user.settings.llm_provider
            )
        except DomainError:
            return None

        request_payload = await llm_gateway.preview_usecase(
            combined_system_prompt,
            ask_prompt,
            tools,
            metadata={
                "user_id": str(self.user.id),
                "handler": "preview_llm_snapshot",
                "usecase": query.usecase,
                "llm_provider": user.settings.llm_provider.value,
            },
        )
        request_messages = request_payload.get("request_messages")
        request_tools = request_payload.get("request_tools")
        request_tool_choice = request_payload.get("request_tool_choice")
        request_model_params = request_payload.get("request_model_params")

        return value_objects.LLMRunResultSnapshot(
            current_time=current_time,
            llm_provider=user.settings.llm_provider,
            system_prompt=system_prompt,
            referenced_entities=build_referenced_entities(prompt_context),
            messages=request_messages,
            tools=request_tools,
            tool_choice=request_tool_choice,
            model_params=request_model_params,
        )

    @staticmethod
    def _build_notification_tools() -> list[LLMTool]:
        async def decide_notification(
            should_notify: bool,
            message: str | None = None,
            priority: str | None = None,
            reason: str | None = None,
        ) -> None:
            """Decide whether to send a smart notification."""
            _ = (should_notify, message, priority, reason)
            return None

        return [LLMTool(callback=decide_notification)]

    @staticmethod
    def _build_morning_overview_tools() -> list[LLMTool]:
        async def decide_morning_overview(
            should_notify: bool,
            message: str | None = None,
            priority: str | None = None,
            reason: str | None = None,
        ) -> None:
            """Decide whether to send a morning overview."""
            _ = (should_notify, message, priority, reason)
            return None

        return [LLMTool(callback=decide_morning_overview)]

    @staticmethod
    def _build_inbound_sms_tools(send_acknowledgment: bool) -> list[LLMTool]:
        _ = send_acknowledgment

        async def reply(message: str | None = None) -> None:
            """Reply to the user via SMS (optional message for no action).

            Notes:
            - Use when you want to respond or when no action is needed.
            - Leave message empty to take no action.
            """
            _ = message
            return None

        async def ask_question(message: str) -> None:
            """Ask the user a follow-up question.

            Notes:
            - Use when you need more information.
            """
            _ = message
            return None

        async def add_task(
            name: str,
            category: value_objects.TaskCategory,
            description: str | None = None,
            available_time: time | None = None,
            start_time: time | None = None,
            end_time: time | None = None,
            cutoff_time: time | None = None,
            tags: list[value_objects.TaskTag] | None = None,
            message: str | None = None,
        ) -> None:
            """Create a new task based on the inbound SMS.

            Notes:
            - Use when the SMS contains a to-do or action.
            - category must be one of the TaskCategory enum values (UPPERCASE).
            - Time fields should be 24h format HH:MM.
            - Include an acknowledgment message when required.
            """
            _ = (
                name,
                category,
                description,
                available_time,
                start_time,
                end_time,
                cutoff_time,
                tags,
                message,
            )
            return None

        async def add_reminder(reminder: str, message: str | None = None) -> None:
            """Create a new reminder (task type REMINDER) based on the inbound SMS.

            Notes:
            - Use for simple, quick reminders.
            - Include an acknowledgment message when required.
            """
            _ = (reminder, message)
            return None

        async def update_task(
            task_id: UUID,
            action: Literal["complete", "punt"],
            message: str | None = None,
        ) -> None:
            """Update an existing task when the inbound SMS implies a status change.

            Notes:
            - Use only when the SMS refers to an existing task.
            - action must be "complete" or "punt".
            - Never invent task IDs; only use IDs shown in the context.
            - Include an acknowledgment message when required.
            """
            _ = (task_id, action, message)
            return None

        async def add_alarm(
            alarm_time: time,
            name: str | None = None,
            url: str = "",
            alarm_type: value_objects.AlarmType = value_objects.AlarmType.URL,
            message: str | None = None,
        ) -> None:
            """Add an alarm to today's day (user-local time).

            Notes:
            - Use when the user asks to set an alarm.
            - alarm_time should be 24h format HH:MM.
            - Include an acknowledgment message when required.
            """
            _ = (alarm_time, name, url, alarm_type, message)
            return None

        return [
            LLMTool(callback=reply),
            LLMTool(callback=ask_question),
            LLMTool(callback=add_task),
            LLMTool(callback=add_reminder),
            LLMTool(callback=add_alarm),
            LLMTool(callback=update_task),
        ]

    async def _get_send_acknowledgment(self, usecase: str) -> bool:
        configs = await self.usecase_config_ro_repo.search(
            value_objects.UseCaseConfigQuery(usecase=usecase)
        )
        if not configs:
            return True
        send_acknowledgment = configs[0].config.get("send_acknowledgment")
        if isinstance(send_acknowledgment, bool):
            return send_acknowledgment
        return True

    @staticmethod
    def _default_tool_call_arguments(tool_name: str) -> dict[str, object | None]:
        if tool_name == "decide_notification":
            return {
                "should_notify": None,
                "message": None,
                "priority": None,
                "reason": None,
            }
        if tool_name == "decide_morning_overview":
            return {
                "should_notify": None,
                "message": None,
                "priority": None,
                "reason": None,
            }
        if tool_name == "reply":
            return {"message": None}
        if tool_name == "ask_question":
            return {"message": None}
        if tool_name == "add_task":
            return {
                "name": None,
                "category": None,
                "description": None,
                "available_time": None,
                "start_time": None,
                "end_time": None,
                "cutoff_time": None,
                "tags": None,
                "message": None,
            }
        if tool_name == "add_reminder":
            return {"reminder": None, "message": None}
        if tool_name == "update_task":
            return {"task_id": None, "action": None, "message": None}
        if tool_name == "add_alarm":
            return {
                "alarm_time": None,
                "name": None,
                "url": None,
                "alarm_type": None,
                "message": None,
            }
        return {}
