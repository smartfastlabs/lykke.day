"""Unit tests for alarm worker tasks."""

from datetime import UTC, date as dt_date, datetime, time
from uuid import uuid4

import pytest
from dobles import InstanceDouble, allow

from lykke.application.commands.day import TriggerAlarmsForUserCommand
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity
from lykke.presentation.workers.tasks import alarms as alarm_tasks
from tests.support.dobles import (
    create_day_repo_double,
    create_read_only_repos_double,
    create_uow_double,
    create_uow_factory_double,
)
from tests.unit.presentation.worker_task_helpers import (
    build_user,
    create_identity_access,
    create_gateway_recorder,
    create_task_recorder,
)


@pytest.mark.asyncio
async def test_trigger_alarms_for_all_users_task_enqueues() -> None:
    users = [build_user(uuid4()), build_user(uuid4())]
    task, calls = create_task_recorder()
    identity_access = create_identity_access(users)

    await alarm_tasks.trigger_alarms_for_all_users_task(
        identity_access=identity_access,
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
    allow(day_repo).get.and_return(day)

    ro_repos = create_read_only_repos_double(day_repo=day_repo)
    ro_factory = InstanceDouble(
        f"{ReadOnlyRepositoryFactory.__module__}.{ReadOnlyRepositoryFactory.__name__}"
    )
    allow(ro_factory).create.and_return(ro_repos)

    uow = create_uow_double(day_repo=day_repo)
    uow_factory = create_uow_factory_double(uow)

    await alarm_tasks.trigger_alarms_for_user_task(
        user_id=user_id,
        identity_access=create_identity_access([build_user(user_id)]),
        uow_factory=uow_factory,
        ro_repo_factory=ro_factory,
        pubsub_gateway=gateway,
        command=TriggerAlarmsForUserCommand(
            evaluation_datetime=datetime(2025, 11, 27, 8, 0, tzinfo=UTC),
            target_date=day.date,
        ),
    )

    assert uow.added
    assert gateway_state["closed"] is True
