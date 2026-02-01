"""Query for building a synthetic LLM run snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, create_model

from lykke.application.gateways.llm_protocol import LLMTool
from lykke.application.llm.prompt_rendering import (
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
from lykke.application.unit_of_work import ReadOnlyRepositories
from lykke.core.utils.dates import get_current_date, get_current_datetime_in_timezone
from lykke.core.utils.day_context_serialization import serialize_day_context
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

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        user_id: UUID,
        get_llm_prompt_context_handler: GetLLMPromptContextHandler,
    ) -> None:
        super().__init__(ro_repos, user_id)
        self._get_llm_prompt_context_handler = get_llm_prompt_context_handler

    async def handle(
        self, query: PreviewLLMSnapshotQuery
    ) -> value_objects.LLMRunResultSnapshot | None:
        """Build a synthetic snapshot without running the LLM."""
        if query.usecase not in {"notification", "process_inbound_sms"}:
            return None

        user = await self.user_ro_repo.get(self.user_id)
        if not user.settings or not user.settings.llm_provider:
            return None

        current_time = get_current_datetime_in_timezone(user.settings.timezone)
        current_date = get_current_date(user.settings.timezone)
        prompt_context = await self._get_llm_prompt_context_handler.handle(
            GetLLMPromptContextQuery(date=current_date)
        )

        if query.usecase == "notification":
            tools = self._build_notification_tools()
        else:
            send_acknowledgment = await self._get_send_acknowledgment(query.usecase)
            tools = self._build_inbound_sms_tools(send_acknowledgment)

        tools_prompt = render_tools_prompt(tools)

        if query.usecase == "notification":
            extra_template_vars: dict[str, Any] = {"tools_prompt": tools_prompt}
        else:
            inbound_message = MessageEntity(
                user_id=self.user_id,
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

        request_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context_prompt},
            {"role": "user", "content": ask_prompt},
        ]
        request_tools = [
            {"name": t.name or "tool", "description": t.description or ""}
            for t in tools
        ]
        request_model_params = {"llm_provider": user.settings.llm_provider.value}

        return value_objects.LLMRunResultSnapshot(
            tool_calls=[
                value_objects.LLMToolCallResultSnapshot(
                    tool_name=tool.name or "tool",
                    arguments=self._default_tool_call_arguments(tool.name or "tool"),
                    result=None,
                )
                for tool in tools
            ],
            prompt_context=serialize_day_context(
                prompt_context, current_time=current_time
            ),
            current_time=current_time,
            llm_provider=user.settings.llm_provider,
            system_prompt=system_prompt,
            context_prompt=context_prompt,
            ask_prompt=ask_prompt,
            tools_prompt=tools_prompt,
            referenced_entities=build_referenced_entities(prompt_context),
            request_messages=request_messages,
            request_tools=request_tools,
            request_tool_choice="auto",
            request_model_params=request_model_params,
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

        return [
            LLMTool(
                name="decide_notification",
                callback=decide_notification,
                description="Decide whether to send a smart notification.",
            )
        ]

    @staticmethod
    def _build_inbound_sms_tools(send_acknowledgment: bool) -> list[LLMTool]:
        async def reply(message: str | None = None) -> None:
            """Reply to the user via SMS (optional message for no action)."""
            _ = message
            return None

        async def ask_question(message: str) -> None:
            """Ask the user a follow-up question."""
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
            """Create a new task based on the inbound SMS."""
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
            """Create a new reminder (task type REMINDER) based on the inbound SMS."""
            _ = (reminder, message)
            return None

        async def update_task(
            task_id: UUID,
            action: Literal["complete", "punt"],
            message: str | None = None,
        ) -> None:
            """Update an existing task when the inbound SMS implies a status change."""
            _ = (task_id, action, message)
            return None

        async def add_alarm(
            alarm_time: time,
            name: str | None = None,
            url: str = "",
            alarm_type: value_objects.AlarmType = value_objects.AlarmType.URL,
            message: str | None = None,
        ) -> None:
            """Add an alarm to today's day (user-local time)."""
            _ = (alarm_time, name, url, alarm_type, message)
            return None

        message_field: tuple[Any, Any] = (
            (str, Field(..., description="Acknowledgment message."))
            if send_acknowledgment
            else (str | None, Field(default=None, description="Optional message."))
        )
        reply_args = create_model(
            "PreviewInboundSmsReplyArgs",
            message=(str | None, Field(default=None)),
        )
        ask_question_args = create_model(
            "PreviewInboundSmsAskQuestionArgs",
            message=(str, Field(...)),
        )
        add_task_args = create_model(
            "PreviewInboundSmsAddTaskArgs",
            name=(str, Field(...)),
            category=(value_objects.TaskCategory, Field(...)),
            description=(str | None, Field(default=None)),
            available_time=(time | None, Field(default=None)),
            start_time=(time | None, Field(default=None)),
            end_time=(time | None, Field(default=None)),
            cutoff_time=(time | None, Field(default=None)),
            tags=(list[value_objects.TaskTag] | None, Field(default=None)),
            message=message_field,
        )
        add_reminder_args = create_model(
            "PreviewInboundSmsAddReminderArgs",
            reminder=(str, Field(...)),
            message=message_field,
        )
        update_task_args = create_model(
            "PreviewInboundSmsUpdateTaskArgs",
            task_id=(UUID, Field(...)),
            action=(Literal["complete", "punt"], Field(...)),
            message=message_field,
        )
        add_alarm_args = create_model(
            "PreviewInboundSmsAddAlarmArgs",
            alarm_time=(time, Field(...)),
            name=(str | None, Field(default=None)),
            url=(str, Field(default="")),
            alarm_type=(
                value_objects.AlarmType,
                Field(default=value_objects.AlarmType.URL),
            ),
            message=message_field,
        )

        return [
            LLMTool(callback=reply, args_model=reply_args),
            LLMTool(callback=ask_question, args_model=ask_question_args),
            LLMTool(callback=add_task, args_model=add_task_args),
            LLMTool(callback=add_reminder, args_model=add_reminder_args),
            LLMTool(callback=add_alarm, args_model=add_alarm_args),
            LLMTool(callback=update_task, args_model=update_task_args),
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
