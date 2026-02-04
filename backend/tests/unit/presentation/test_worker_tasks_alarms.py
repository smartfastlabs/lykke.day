"""Unit tests for alarm worker tasks."""

from datetime import UTC, date as dt_date, datetime, time
from uuid import uuid4

import pytest
from dobles import allow

from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity
from lykke.presentation.workers.tasks import alarms as alarm_tasks
from tests.support.dobles import (
    create_day_repo_double,
    create_uow_double,
    create_uow_factory_double,
)
from tests.unit.presentation.worker_task_helpers import (
    build_user,
    create_gateway_recorder,
    create_task_recorder,
    create_user_repo,
)


@pytest.mark.asyncio
async def test_trigger_alarms_for_all_users_task_enqueues() -> None:
    users = [build_user(uuid4()), build_user(uuid4())]
    task, calls = create_task_recorder()
    user_repo = create_user_repo(users)

    await alarm_tasks.trigger_alarms_for_all_users_task(
        user_repo=user_repo,
        enqueue_task=task,
    )

    assert len(calls) == 2


@pytest.mark.asyncio
async def test_trigger_alarms_for_user_task_triggers_alarm() -> None:
    gateway, gateway_state = create_gateway_recorder()
    user_id = uuid4()
    template = DayTemplateEntity(
        user_id=user_id, slug="default", routine_definition_ids=[], time_blocks=[]
    )
    day = DayEntity.create_for_date(dt_date(2025, 11, 27), user_id, template)
    alarm = value_objects.Alarm(
        name="Alarm",
        time=time(8, 0),
        datetime=datetime(2025, 11, 27, 8, 0, tzinfo=UTC),
    )
    day.add_alarm(alarm)

    day_repo = create_day_repo_double()
    day_id = DayEntity.id_from_date_and_user(day.date, user_id)

    allow(day_repo).get.and_return(day)
    uow = create_uow_double(day_repo=day_repo)
    uow_factory = create_uow_factory_double(uow)

    await alarm_tasks.trigger_alarms_for_user_task(
        user_id=user_id,
        user_repo=create_user_repo([build_user(user_id)]),
        day_repo=day_repo,
        uow_factory=uow_factory,
        pubsub_gateway=gateway,
        current_date_provider=lambda _: day.date,
        current_datetime_provider=lambda: datetime(2025, 11, 27, 8, 0, tzinfo=UTC),
    )

    assert uow.added
    assert gateway_state["closed"] is True
