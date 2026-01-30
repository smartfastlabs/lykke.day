"""Unit tests for ProcessBrainDumpHandler."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date as dt_date, datetime, time
from typing import Any
from uuid import uuid4

import pytest
from dobles import allow

from lykke.application.commands.brain_dump import (
    ProcessBrainDumpCommand,
    ProcessBrainDumpHandler,
)
from lykke.application.gateways.llm_protocol import LLMTool, LLMToolRunResult
from lykke.domain import value_objects
from lykke.domain.entities import BrainDumpEntity, DayEntity, DayTemplateEntity
from lykke.domain.events.day_events import BrainDumpTypeChangedEvent
from tests.support.dobles import (
    create_brain_dump_repo_double,
    create_day_repo_double,
    create_read_only_repos_double,
    create_uow_double,
    create_uow_factory_double,
)


class _LLMGateway:
    async def run_usecase(
        self,
        system_prompt: str,
        context_prompt: str,
        ask_prompt: str,
        tools: list[LLMTool],
        metadata: dict[str, Any] | None = None,
    ) -> LLMToolRunResult | None:
        _ = system_prompt
        _ = context_prompt
        _ = ask_prompt
        _ = tools
        _ = metadata
        return None


class _LLMGatewayFactory:
    def create_gateway(self, provider: value_objects.LLMProvider) -> _LLMGateway:
        _ = provider
        return _LLMGateway()


@dataclass
class _Recorder:
    commands: list[object]

    async def handle(self, command: Any) -> None:
        self.commands.append(command)


@pytest.mark.asyncio
async def test_process_brain_dump_add_task_creates_adhoc_task() -> None:
    user_id = uuid4()
    date = dt_date(2025, 11, 27)
    template = DayTemplateEntity(user_id=user_id, slug="default")
    day = DayEntity.create_for_date(date, user_id=user_id, template=template)
    item = BrainDumpEntity(user_id=user_id, date=date, text="Write project brief")

    result = {
        "name": "Write project brief",
        "category": value_objects.TaskCategory.WORK,
        "description": "Draft the first version of the brief",
        "start_time": time(9, 0),
        "tags": [value_objects.TaskTag.IMPORTANT],
    }
    prompt_context = value_objects.LLMPromptContext(
        day=day,
        tasks=[],
        calendar_entries=[],
        brain_dump_items=[],
        messages=[],
        push_notifications=[],
    )

    task_recorder = _Recorder(commands=[])

    brain_dump_repo = create_brain_dump_repo_double()
    allow(brain_dump_repo).get.with_args(item.id).and_return(item)

    day_repo = create_day_repo_double()
    day_id = DayEntity.id_from_date_and_user(date, user_id)
    allow(day_repo).get.with_args(day_id).and_return(day)

    ro_repos = create_read_only_repos_double(
        day_repo=day_repo,
        brain_dump_repo=brain_dump_repo,
    )
    uow = create_uow_double(
        day_repo=day_repo,
        brain_dump_repo=brain_dump_repo,
    )

    handler = ProcessBrainDumpHandler(
        ro_repos,
        create_uow_factory_double(uow),
        user_id,
        _LLMGatewayFactory(),
        object(),
        task_recorder,
        _Recorder(commands=[]),
        _Recorder(commands=[]),
        _Recorder(commands=[]),
    )

    async def run_llm_side_effect() -> None:
        tools = handler.build_tools(
            current_time=datetime.now(UTC),
            prompt_context=prompt_context,
            llm_provider=value_objects.LLMProvider.OPENAI,
        )
        tool = next(tool for tool in tools if tool.name == "add_task")
        await tool.callback(**result)

    handler.run_llm = run_llm_side_effect  # type: ignore[method-assign]

    await handler.handle(ProcessBrainDumpCommand(date=date, item_id=item.id))

    assert len(task_recorder.commands) == 1
    command = task_recorder.commands[0]
    assert command.name == "Write project brief"
    assert command.category == value_objects.TaskCategory.WORK
    assert command.scheduled_date == date
    assert command.time_window is not None
    assert command.time_window.start_time == time(9, 0)


@pytest.mark.asyncio
async def test_process_brain_dump_update_task_records_action() -> None:
    user_id = uuid4()
    date = dt_date(2025, 11, 27)
    template = DayTemplateEntity(user_id=user_id, slug="default")
    day = DayEntity.create_for_date(date, user_id=user_id, template=template)
    item = BrainDumpEntity(user_id=user_id, date=date, text="Finished the report")

    task_id = uuid4()
    prompt_context = value_objects.LLMPromptContext(
        day=day,
        tasks=[],
        calendar_entries=[],
        brain_dump_items=[],
        messages=[],
        push_notifications=[],
    )

    task_action_recorder = _Recorder(commands=[])

    brain_dump_repo = create_brain_dump_repo_double()
    allow(brain_dump_repo).get.with_args(item.id).and_return(item)

    day_repo = create_day_repo_double()
    day_id = DayEntity.id_from_date_and_user(date, user_id)
    allow(day_repo).get.with_args(day_id).and_return(day)

    ro_repos = create_read_only_repos_double(
        day_repo=day_repo,
        brain_dump_repo=brain_dump_repo,
    )
    uow = create_uow_double(
        day_repo=day_repo,
        brain_dump_repo=brain_dump_repo,
    )

    handler = ProcessBrainDumpHandler(
        ro_repos,
        create_uow_factory_double(uow),
        user_id,
        _LLMGatewayFactory(),
        object(),
        _Recorder(commands=[]),
        _Recorder(commands=[]),
        _Recorder(commands=[]),
        task_action_recorder,
    )

    async def run_llm_side_effect() -> None:
        tools = handler.build_tools(
            current_time=datetime.now(UTC),
            prompt_context=prompt_context,
            llm_provider=value_objects.LLMProvider.OPENAI,
        )
        tool = next(tool for tool in tools if tool.name == "update_task")
        await tool.callback(task_id=task_id, action="complete")

    handler.run_llm = run_llm_side_effect  # type: ignore[method-assign]

    await handler.handle(ProcessBrainDumpCommand(date=date, item_id=item.id))

    assert len(task_action_recorder.commands) == 1
    command = task_action_recorder.commands[0]
    assert command.task_id == task_id
    assert command.action.type == value_objects.ActionType.COMPLETE


@pytest.mark.asyncio
async def test_process_brain_dump_update_reminder_updates_status() -> None:
    user_id = uuid4()
    date = dt_date(2025, 11, 27)
    template = DayTemplateEntity(user_id=user_id, slug="default")
    day = DayEntity.create_for_date(date, user_id=user_id, template=template)
    item = BrainDumpEntity(user_id=user_id, date=date, text="Mark reminder complete")

    reminder_id = uuid4()
    prompt_context = value_objects.LLMPromptContext(
        day=day,
        tasks=[],
        calendar_entries=[],
        brain_dump_items=[],
        messages=[],
        push_notifications=[],
    )

    reminder_status_recorder = _Recorder(commands=[])

    brain_dump_repo = create_brain_dump_repo_double()
    allow(brain_dump_repo).get.with_args(item.id).and_return(item)

    day_repo = create_day_repo_double()
    day_id = DayEntity.id_from_date_and_user(date, user_id)
    allow(day_repo).get.with_args(day_id).and_return(day)

    ro_repos = create_read_only_repos_double(
        day_repo=day_repo,
        brain_dump_repo=brain_dump_repo,
    )
    uow = create_uow_double(
        day_repo=day_repo,
        brain_dump_repo=brain_dump_repo,
    )

    handler = ProcessBrainDumpHandler(
        ro_repos,
        create_uow_factory_double(uow),
        user_id,
        _LLMGatewayFactory(),
        object(),
        _Recorder(commands=[]),
        _Recorder(commands=[]),
        reminder_status_recorder,
        _Recorder(commands=[]),
    )

    async def run_llm_side_effect() -> None:
        tools = handler.build_tools(
            current_time=datetime.now(UTC),
            prompt_context=prompt_context,
            llm_provider=value_objects.LLMProvider.OPENAI,
        )
        tool = next(tool for tool in tools if tool.name == "update_reminder")
        await tool.callback(
            reminder_id=reminder_id,
            status=value_objects.ReminderStatus.COMPLETE,
        )

    handler.run_llm = run_llm_side_effect  # type: ignore[method-assign]

    await handler.handle(ProcessBrainDumpCommand(date=date, item_id=item.id))

    assert len(reminder_status_recorder.commands) == 1
    command = reminder_status_recorder.commands[0]
    assert command.reminder_id == reminder_id
    assert command.status == value_objects.ReminderStatus.COMPLETE


@pytest.mark.asyncio
async def test_process_brain_dump_marks_item_as_command_on_tool_call() -> None:
    user_id = uuid4()
    date = dt_date(2025, 11, 27)
    template = DayTemplateEntity(user_id=user_id, slug="default")
    day = DayEntity.create_for_date(date, user_id=user_id, template=template)
    item = BrainDumpEntity(user_id=user_id, date=date, text="Follow up on invoice")

    prompt_context = value_objects.LLMPromptContext(
        day=day,
        tasks=[],
        calendar_entries=[],
        brain_dump_items=[],
        messages=[],
        push_notifications=[],
    )

    brain_dump_repo = create_brain_dump_repo_double()
    allow(brain_dump_repo).get.with_args(item.id).and_return(item)

    day_repo = create_day_repo_double()
    day_id = DayEntity.id_from_date_and_user(date, user_id)
    allow(day_repo).get.with_args(day_id).and_return(day)

    ro_repos = create_read_only_repos_double(
        day_repo=day_repo,
        brain_dump_repo=brain_dump_repo,
    )
    uow = create_uow_double(
        day_repo=day_repo,
        brain_dump_repo=brain_dump_repo,
    )

    handler = ProcessBrainDumpHandler(
        ro_repos,
        create_uow_factory_double(uow),
        user_id,
        _LLMGatewayFactory(),
        object(),
        _Recorder(commands=[]),
        _Recorder(commands=[]),
        _Recorder(commands=[]),
        _Recorder(commands=[]),
    )

    async def run_llm_side_effect() -> None:
        tools = handler.build_tools(
            current_time=datetime.now(UTC),
            prompt_context=prompt_context,
            llm_provider=value_objects.LLMProvider.OPENAI,
        )
        tool = next(tool for tool in tools if tool.name == "add_task")
        await tool.callback(
            name="Follow up on invoice",
            category=value_objects.TaskCategory.WORK,
        )

    handler.run_llm = run_llm_side_effect  # type: ignore[method-assign]

    await handler.handle(ProcessBrainDumpCommand(date=date, item_id=item.id))

    assert len(uow.added) == 1
    updated = uow.added[0]
    assert updated.type == value_objects.BrainDumpType.COMMAND
    events = updated.collect_events()
    assert any(isinstance(event, BrainDumpTypeChangedEvent) for event in events)
    assert any(isinstance(event, BrainDumpTypeChangedEvent) for event in events)
    assert any(isinstance(event, BrainDumpTypeChangedEvent) for event in events)
