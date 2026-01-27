"""Unit tests for notification worker tasks."""

from datetime import UTC, datetime, time
from uuid import uuid4

import pytest
from dobles import InstanceDouble, allow

from lykke.application.unit_of_work import ReadOnlyRepositoryFactory
from lykke.domain import value_objects
from lykke.presentation.workers.tasks import notifications as notification_tasks
from tests.support.dobles import create_read_only_repos_double
from tests.unit.presentation.worker_task_helpers import (
    build_user,
    create_gateway_recorder,
    create_handler_recorder,
    create_task_recorder,
    create_user_repo,
)


@pytest.mark.asyncio
async def test_evaluate_smart_notifications_for_all_users_task() -> None:
    users = [
        build_user(uuid4(), llm_provider=value_objects.LLMProvider.OPENAI),
        build_user(uuid4(), llm_provider=None),
    ]
    task, calls = create_task_recorder()
    user_repo = create_user_repo(users)

    await notification_tasks.evaluate_smart_notifications_for_all_users_task(
        user_repo=user_repo,
        enqueue_task=task,
    )

    assert len(calls) == 1


@pytest.mark.asyncio
async def test_evaluate_kiosk_notifications_for_all_users_task() -> None:
    users = [
        build_user(uuid4(), llm_provider=value_objects.LLMProvider.OPENAI),
        build_user(uuid4(), llm_provider=None),
    ]
    task, calls = create_task_recorder()
    user_repo = create_user_repo(users)

    await notification_tasks.evaluate_kiosk_notifications_for_all_users_task(
        user_repo=user_repo,
        enqueue_task=task,
    )

    assert len(calls) == 1


@pytest.mark.asyncio
async def test_evaluate_smart_notification_task_calls_handler() -> None:
    gateway, gateway_state = create_gateway_recorder()
    handler, handler_calls = create_handler_recorder()

    await notification_tasks.evaluate_smart_notification_task(
        user_id=uuid4(),
        triggered_by="scheduled",
        handler=handler,
        pubsub_gateway=gateway,
    )

    assert handler_calls
    assert gateway_state["closed"] is True


@pytest.mark.asyncio
async def test_evaluate_kiosk_notification_task_calls_handler() -> None:
    gateway, gateway_state = create_gateway_recorder()
    handler, handler_calls = create_handler_recorder()

    await notification_tasks.evaluate_kiosk_notification_task(
        user_id=uuid4(),
        triggered_by="scheduled",
        handler=handler,
        pubsub_gateway=gateway,
    )

    assert handler_calls
    assert gateway_state["closed"] is True


@pytest.mark.asyncio
async def test_evaluate_morning_overviews_for_all_users_task() -> None:
    eligible_user = build_user(
        uuid4(),
        llm_provider=value_objects.LLMProvider.OPENAI,
        morning_overview_time="08:00",
        timezone="UTC",
    )
    invalid_user = build_user(
        uuid4(),
        llm_provider=value_objects.LLMProvider.OPENAI,
        morning_overview_time="bad",
        timezone="UTC",
    )
    late_user = build_user(
        uuid4(),
        llm_provider=value_objects.LLMProvider.OPENAI,
        morning_overview_time="09:00",
        timezone="UTC",
    )
    users = [eligible_user, invalid_user, late_user]

    task, calls = create_task_recorder()
    user_repo = create_user_repo(users)

    ro_repos = create_read_only_repos_double()
    allow(ro_repos.push_notification_ro_repo).search.and_return([])
    ro_factory = InstanceDouble(
        f"{ReadOnlyRepositoryFactory.__module__}.{ReadOnlyRepositoryFactory.__name__}"
    )
    allow(ro_factory).create.and_return(ro_repos)

    await notification_tasks.evaluate_morning_overviews_for_all_users_task(
        user_repo=user_repo,
        enqueue_task=task,
        ro_repo_factory=ro_factory,
        current_time_provider=lambda _: time(8, 5),
        current_datetime_provider=lambda _: datetime(2025, 11, 27, 8, 0, tzinfo=UTC),
    )

    assert len(calls) == 1


@pytest.mark.asyncio
async def test_evaluate_morning_overview_task_calls_handler() -> None:
    gateway, gateway_state = create_gateway_recorder()
    handler, handler_calls = create_handler_recorder()

    await notification_tasks.evaluate_morning_overview_task(
        user_id=uuid4(),
        handler=handler,
        pubsub_gateway=gateway,
    )

    assert handler_calls
    assert gateway_state["closed"] is True
