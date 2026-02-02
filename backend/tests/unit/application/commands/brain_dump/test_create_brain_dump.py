"""Unit tests for CreateBrainDumpHandler."""

from datetime import date as dt_date
from uuid import uuid4

import pytest
from dobles import allow

from lykke.application.commands.brain_dump import (
    CreateBrainDumpCommand,
    CreateBrainDumpHandler,
)
from lykke.application.worker_schedule import (
    reset_current_workers_to_schedule,
    set_current_workers_to_schedule,
)
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity, UserEntity
from lykke.domain.events.day_events import BrainDumpAddedEvent
from lykke.presentation.workers import tasks as worker_tasks
from tests.support.dobles import (
    create_day_repo_double,
    create_day_template_repo_double,
    create_read_only_repos_double,
    create_uow_double,
    create_uow_factory_double,
    create_user_repo_double,
)


class _WorkersToSchedule:
    def __init__(self) -> None:
        self.calls: list[tuple[object, dict[str, object]]] = []

    def schedule(self, worker: object, **kwargs: object) -> None:
        self.calls.append((worker, kwargs))

    async def flush(self) -> None:
        return None


@pytest.mark.asyncio
async def test_create_brain_dump_creates_item():
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_definition_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)
    day_repo = create_day_repo_double()
    allow(day_repo).get.and_return(day)

    day_template_repo = create_day_template_repo_double()
    allow(day_template_repo).get.and_return(template)
    allow(day_template_repo).search_one.and_return(template)

    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )
    user_repo = create_user_repo_double()
    allow(user_repo).get.and_return(user)

    ro_repos = create_read_only_repos_double(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    uow = create_uow_double(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    uow_factory = create_uow_factory_double(uow)
    handler = CreateBrainDumpHandler(ro_repos, uow_factory, user_id)

    workers_to_schedule = _WorkersToSchedule()
    token = set_current_workers_to_schedule(workers_to_schedule)
    try:
        result = await handler.handle(
            CreateBrainDumpCommand(date=task_date, text="Test brain dump")
        )
    finally:
        reset_current_workers_to_schedule(token)

    assert result.text == "Test brain dump"
    assert result.status == value_objects.BrainDumpStatus.ACTIVE
    events = result.collect_events()
    assert any(isinstance(event, BrainDumpAddedEvent) for event in events)
    assert len(workers_to_schedule.calls) == 1
    worker, kwargs = workers_to_schedule.calls[0]
    assert worker is worker_tasks.process_brain_dump_item_task
    assert kwargs["user_id"] == user_id
    assert kwargs["day_date"] == task_date.isoformat()
    assert kwargs["item_id"] == result.id


@pytest.mark.asyncio
async def test_create_brain_dump_day_not_found():
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_definition_ids=[],
        time_blocks=[],
    )

    day_repo = create_day_repo_double()
    allow(day_repo).get.and_raise(NotFoundError("Day not found"))

    day_template_repo = create_day_template_repo_double()
    allow(day_template_repo).get.and_return(template)
    allow(day_template_repo).search_one.and_return(template)

    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )
    user_repo = create_user_repo_double()
    allow(user_repo).get.and_return(user)

    ro_repos = create_read_only_repos_double(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    uow = create_uow_double(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        user_repo=user_repo,
    )
    uow_factory = create_uow_factory_double(uow)
    handler = CreateBrainDumpHandler(ro_repos, uow_factory, user_id)

    with pytest.raises(NotFoundError, match="Day"):
        await handler.handle(
            CreateBrainDumpCommand(date=task_date, text="Test brain dump")
        )
