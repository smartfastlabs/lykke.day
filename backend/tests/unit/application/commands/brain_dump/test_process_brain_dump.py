"""Unit tests for ProcessBrainDumpHandler."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date as dt_date, datetime, time
from typing import Any
from uuid import uuid4

import pytest
from dobles import InstanceDouble, allow

from lykke.application.commands.brain_dump import (
    ProcessBrainDumpCommand,
    ProcessBrainDumpHandler,
)
from lykke.application.llm_usecases import LLMRunResult
from lykke.domain import value_objects
from lykke.domain.entities import BrainDumpEntity, DayEntity, DayTemplateEntity
from lykke.domain.events.day_events import BrainDumpItemTypeChangedEvent
from tests.support.dobles import (
    create_brain_dump_repo_double,
    create_day_repo_double,
    create_read_only_repos_double,
    create_uow_double,
    create_uow_factory_double,
)


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
        "timing_type": value_objects.TimingType.FLEXIBLE,
        "start_time": time(9, 0),
        "tags": [value_objects.TaskTag.IMPORTANT],
    }
    runner = InstanceDouble("lykke.application.llm_usecases.runner.LLMUseCaseRunner")
    runner.calls: list[object] = []

    async def run_side_effect(*, usecase: Any) -> LLMRunResult | None:
        runner.calls.append(usecase)
        return LLMRunResult(
            tool_name="add_task",
            result=result,
            prompt_context=value_objects.LLMPromptContext(
                day=day,
                tasks=[],
                calendar_entries=[],
                brain_dump_items=[],
                messages=[],
                push_notifications=[],
            ),
            current_time=datetime.now(UTC),
            llm_provider=value_objects.LLMProvider.OPENAI,
            system_prompt="system",
            context_prompt="context",
            ask_prompt="ask",
        )
    runner.run = run_side_effect

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
        runner,
        object(),
        task_recorder,
        _Recorder(commands=[]),
        _Recorder(commands=[]),
        _Recorder(commands=[]),
    )

    await handler.handle(ProcessBrainDumpCommand(date=date, item_id=item.id))

    assert len(task_recorder.commands) == 1
    command = task_recorder.commands[0]
    assert command.name == "Write project brief"
    assert command.category == value_objects.TaskCategory.WORK
    assert command.scheduled_date == date
    assert command.schedule is not None
    assert command.schedule.timing_type == value_objects.TimingType.FLEXIBLE
    assert command.schedule.start_time == time(9, 0)


@pytest.mark.asyncio
async def test_process_brain_dump_update_task_records_action() -> None:
    user_id = uuid4()
    date = dt_date(2025, 11, 27)
    template = DayTemplateEntity(user_id=user_id, slug="default")
    day = DayEntity.create_for_date(date, user_id=user_id, template=template)
    item = BrainDumpEntity(user_id=user_id, date=date, text="Finished the report")

    task_id = uuid4()
    runner = InstanceDouble("lykke.application.llm_usecases.runner.LLMUseCaseRunner")
    runner.calls: list[object] = []

    async def run_side_effect(*, usecase: Any) -> LLMRunResult | None:
        runner.calls.append(usecase)
        return LLMRunResult(
            tool_name="update_task",
            result={"task_id": task_id, "action": "complete"},
            prompt_context=value_objects.LLMPromptContext(
                day=day,
                tasks=[],
                calendar_entries=[],
                brain_dump_items=[],
                messages=[],
                push_notifications=[],
            ),
            current_time=datetime.now(UTC),
            llm_provider=value_objects.LLMProvider.OPENAI,
            system_prompt="system",
            context_prompt="context",
            ask_prompt="ask",
        )
    runner.run = run_side_effect

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
        runner,
        object(),
        _Recorder(commands=[]),
        _Recorder(commands=[]),
        _Recorder(commands=[]),
        task_action_recorder,
    )

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
    runner = InstanceDouble("lykke.application.llm_usecases.runner.LLMUseCaseRunner")
    runner.calls: list[object] = []

    async def run_side_effect(*, usecase: Any) -> LLMRunResult | None:
        runner.calls.append(usecase)
        return LLMRunResult(
            tool_name="update_reminder",
            result={
                "reminder_id": reminder_id,
                "status": value_objects.ReminderStatus.COMPLETE,
            },
            prompt_context=value_objects.LLMPromptContext(
                day=day,
                tasks=[],
                calendar_entries=[],
                brain_dump_items=[],
                messages=[],
                push_notifications=[],
            ),
            current_time=datetime.now(UTC),
            llm_provider=value_objects.LLMProvider.OPENAI,
            system_prompt="system",
            context_prompt="context",
            ask_prompt="ask",
        )
    runner.run = run_side_effect

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
        runner,
        object(),
        _Recorder(commands=[]),
        _Recorder(commands=[]),
        reminder_status_recorder,
        _Recorder(commands=[]),
    )

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

    runner = InstanceDouble("lykke.application.llm_usecases.runner.LLMUseCaseRunner")
    runner.calls: list[object] = []

    async def run_side_effect(*, usecase: Any) -> LLMRunResult | None:
        runner.calls.append(usecase)
        return LLMRunResult(
            tool_name="add_task",
            result={
                "name": "Follow up on invoice",
                "category": value_objects.TaskCategory.WORK,
            },
            prompt_context=value_objects.LLMPromptContext(
                day=day,
                tasks=[],
                calendar_entries=[],
                brain_dump_items=[],
                messages=[],
                push_notifications=[],
            ),
            current_time=datetime.now(UTC),
            llm_provider=value_objects.LLMProvider.OPENAI,
            system_prompt="system",
            context_prompt="context",
            ask_prompt="ask",
        )
    runner.run = run_side_effect

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
        runner,
        object(),
        _Recorder(commands=[]),
        _Recorder(commands=[]),
        _Recorder(commands=[]),
        _Recorder(commands=[]),
    )

    await handler.handle(ProcessBrainDumpCommand(date=date, item_id=item.id))

    assert len(uow.added) == 1
    updated = uow.added[0]
    assert updated.type == value_objects.BrainDumpItemType.COMMAND
    events = updated.collect_events()
    assert any(isinstance(event, BrainDumpItemTypeChangedEvent) for event in events)
