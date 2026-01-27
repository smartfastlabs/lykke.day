"""Unit tests for calendar worker tasks."""

from uuid import uuid4

import pytest
from dobles import InstanceDouble, allow

from lykke.application.unit_of_work import ReadOnlyRepositoryFactory
from lykke.domain.entities import CalendarEntity
from lykke.presentation.workers.tasks import calendar as calendar_tasks
from tests.support.dobles import create_read_only_repos_double
from tests.unit.presentation.worker_task_helpers import (
    create_gateway_recorder,
    create_handler_recorder,
)


@pytest.mark.asyncio
async def test_sync_calendar_task_calls_handler() -> None:
    gateway, gateway_state = create_gateway_recorder()
    handler, handler_calls = create_handler_recorder()

    await calendar_tasks.sync_calendar_task(
        user_id=uuid4(),
        handler=handler,
        pubsub_gateway=gateway,
    )

    assert handler_calls
    assert gateway_state["closed"] is True


@pytest.mark.asyncio
async def test_sync_single_calendar_task_calls_handler() -> None:
    gateway, gateway_state = create_gateway_recorder()
    handler, handler_calls = create_handler_recorder()

    await calendar_tasks.sync_single_calendar_task(
        user_id=uuid4(),
        calendar_id=uuid4(),
        handler=handler,
        pubsub_gateway=gateway,
    )

    assert handler_calls
    assert gateway_state["closed"] is True


@pytest.mark.asyncio
async def test_resubscribe_calendar_task_uses_calendar_repo() -> None:
    gateway, gateway_state = create_gateway_recorder()
    handler, handler_calls = create_handler_recorder()

    calendar = CalendarEntity(
        user_id=uuid4(),
        name="Work",
        auth_token_id=uuid4(),
        platform_id="cal-1",
        platform="google",
    )
    ro_repos = create_read_only_repos_double()
    allow(ro_repos.calendar_ro_repo).get.and_return(calendar)
    ro_factory = InstanceDouble(
        f"{ReadOnlyRepositoryFactory.__module__}.{ReadOnlyRepositoryFactory.__name__}"
    )
    allow(ro_factory).create.and_return(ro_repos)

    await calendar_tasks.resubscribe_calendar_task(
        user_id=uuid4(),
        calendar_id=uuid4(),
        handler=handler,
        ro_repo_factory=ro_factory,
        pubsub_gateway=gateway,
    )

    assert handler_calls
    assert gateway_state["closed"] is True
