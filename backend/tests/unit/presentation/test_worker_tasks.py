"""Unit tests for background worker tasks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date as dt_date, datetime, time
from typing import Any, Callable
from uuid import UUID, uuid4

import pytest

from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntity, DayEntity, DayTemplateEntity, UserEntity
from lykke.presentation.workers import tasks as worker_tasks
from tests.support.dobles import (
    create_day_repo_double,
    create_read_only_repos_double,
    create_uow_double,
)


@dataclass
class _Gateway:
    closed: bool = False

    async def close(self) -> None:
        self.closed = True


@dataclass
class _HandlerRecorder:
    calls: list[object]

    async def handle(self, command: object) -> None:
        self.calls.append(command)


@dataclass
class _TaskRecorder:
    calls: list[dict[str, Any]]

    async def kiq(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)


@dataclass
class _UserRepo:
    users: list[UserEntity]

    async def all(self) -> list[UserEntity]:
        return self.users

    async def get(self, _: UUID) -> UserEntity:
        return self.users[0]


def _build_user(
    user_id: UUID,
    *,
    llm_provider: value_objects.LLMProvider | None = None,
    morning_overview_time: str | None = None,
    timezone: str | None = None,
) -> UserEntity:
    return UserEntity(
        id=user_id,
        email="user@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(
            llm_provider=llm_provider,
            morning_overview_time=morning_overview_time,
            timezone=timezone,
        ),
    )


def _patch_gateway(monkeypatch: pytest.MonkeyPatch) -> _Gateway:
    gateway = _Gateway()
    monkeypatch.setattr(worker_tasks, "RedisPubSubGateway", lambda: gateway)
    return gateway


def _patch_factory_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(worker_tasks, "get_unit_of_work_factory", lambda _: "uow")
    monkeypatch.setattr(worker_tasks, "get_read_only_repository_factory", lambda: "ro")
    monkeypatch.setattr(worker_tasks, "get_google_gateway", lambda: "google")


def test_register_worker_event_handlers(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[object, object]] = []

    def register_all_handlers(*, ro_repo_factory: object, uow_factory: object) -> None:
        calls.append((ro_repo_factory, uow_factory))

    monkeypatch.setattr(worker_tasks, "register_all_handlers", register_all_handlers)
    monkeypatch.setattr(worker_tasks, "get_read_only_repository_factory", lambda: "ro")
    monkeypatch.setattr(worker_tasks, "get_unit_of_work_factory", lambda: "uow")

    worker_tasks.register_worker_event_handlers()

    assert calls == [("ro", "uow")]


@pytest.mark.asyncio
async def test_sync_calendar_task_calls_handler(monkeypatch: pytest.MonkeyPatch) -> None:
    gateway = _patch_gateway(monkeypatch)
    _patch_factory_helpers(monkeypatch)
    handler = _HandlerRecorder(calls=[])
    monkeypatch.setattr(
        worker_tasks, "get_sync_all_calendars_handler", lambda **_: handler
    )

    await worker_tasks.sync_calendar_task(user_id=uuid4())

    assert handler.calls
    assert gateway.closed is True


@pytest.mark.asyncio
async def test_sync_single_calendar_task_calls_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway = _patch_gateway(monkeypatch)
    _patch_factory_helpers(monkeypatch)
    handler = _HandlerRecorder(calls=[])
    monkeypatch.setattr(
        worker_tasks, "get_sync_calendar_handler", lambda **_: handler
    )

    await worker_tasks.sync_single_calendar_task(
        user_id=uuid4(), calendar_id=uuid4()
    )

    assert handler.calls
    assert gateway.closed is True


@pytest.mark.asyncio
async def test_resubscribe_calendar_task_uses_calendar_repo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway = _patch_gateway(monkeypatch)
    _patch_factory_helpers(monkeypatch)
    handler = _HandlerRecorder(calls=[])
    monkeypatch.setattr(
        worker_tasks, "get_subscribe_calendar_handler", lambda **_: handler
    )

    calendar = CalendarEntity(
        user_id=uuid4(),
        name="Work",
        auth_token_id=uuid4(),
        platform_id="cal-1",
        platform="google",
    )
    ro_repos = create_read_only_repos_double()

    async def get_calendar(_: UUID) -> object:
        return calendar

    ro_repos.calendar_ro_repo.get = get_calendar

    class _Factory:
        def create(self, _: UUID) -> object:
            return ro_repos

    monkeypatch.setattr(worker_tasks, "get_read_only_repository_factory", lambda: _Factory())

    await worker_tasks.resubscribe_calendar_task(
        user_id=uuid4(), calendar_id=uuid4()
    )

    assert handler.calls
    assert gateway.closed is True


@pytest.mark.asyncio
async def test_schedule_all_users_day_task_enqueues() -> None:
    users = [_build_user(uuid4()), _build_user(uuid4())]
    recorder = _TaskRecorder(calls=[])
    worker_tasks.schedule_user_day_task.kiq = recorder.kiq

    await worker_tasks.schedule_all_users_day_task(user_repo=_UserRepo(users=users))

    assert len(recorder.calls) == 2


@pytest.mark.asyncio
async def test_schedule_user_day_task_handles_value_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway = _patch_gateway(monkeypatch)
    handler = _HandlerRecorder(calls=[])

    async def raise_value_error(_: object) -> None:
        raise ValueError("missing template")

    handler.handle = raise_value_error
    monkeypatch.setattr(worker_tasks, "get_schedule_day_handler", lambda **_: handler)
    monkeypatch.setattr(worker_tasks, "get_unit_of_work_factory", lambda _: "uow")
    monkeypatch.setattr(worker_tasks, "get_read_only_repository_factory", lambda: "ro")
    monkeypatch.setattr(worker_tasks, "get_current_date", lambda _: dt_date(2025, 11, 27))

    await worker_tasks.schedule_user_day_task(
        user_id=uuid4(), user_repo=_UserRepo(users=[_build_user(uuid4())])
    )

    assert gateway.closed is True


@pytest.mark.asyncio
async def test_schedule_user_day_task_handles_generic_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway = _patch_gateway(monkeypatch)
    handler = _HandlerRecorder(calls=[])

    async def raise_error(_: object) -> None:
        raise RuntimeError("boom")

    handler.handle = raise_error
    monkeypatch.setattr(worker_tasks, "get_schedule_day_handler", lambda **_: handler)
    monkeypatch.setattr(worker_tasks, "get_unit_of_work_factory", lambda _: "uow")
    monkeypatch.setattr(worker_tasks, "get_read_only_repository_factory", lambda: "ro")
    monkeypatch.setattr(worker_tasks, "get_current_date", lambda _: dt_date(2025, 11, 27))

    await worker_tasks.schedule_user_day_task(
        user_id=uuid4(), user_repo=_UserRepo(users=[_build_user(uuid4())])
    )

    assert gateway.closed is True


@pytest.mark.asyncio
async def test_evaluate_smart_notifications_for_all_users_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    users = [
        _build_user(uuid4(), llm_provider=value_objects.LLMProvider.OPENAI),
        _build_user(uuid4(), llm_provider=None),
    ]
    recorder = _TaskRecorder(calls=[])
    worker_tasks.evaluate_smart_notification_task.kiq = recorder.kiq

    await worker_tasks.evaluate_smart_notifications_for_all_users_task(
        user_repo=_UserRepo(users=users)
    )

    assert len(recorder.calls) == 1


@pytest.mark.asyncio
async def test_evaluate_kiosk_notifications_for_all_users_task() -> None:
    users = [
        _build_user(uuid4(), llm_provider=value_objects.LLMProvider.OPENAI),
        _build_user(uuid4(), llm_provider=None),
    ]
    recorder = _TaskRecorder(calls=[])
    worker_tasks.evaluate_kiosk_notification_task.kiq = recorder.kiq

    await worker_tasks.evaluate_kiosk_notifications_for_all_users_task(
        user_repo=_UserRepo(users=users)
    )

    assert len(recorder.calls) == 1


@pytest.mark.asyncio
async def test_evaluate_smart_notification_task_calls_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway = _patch_gateway(monkeypatch)
    _patch_factory_helpers(monkeypatch)
    handler = _HandlerRecorder(calls=[])
    monkeypatch.setattr(
        worker_tasks, "get_smart_notification_handler", lambda **_: handler
    )

    await worker_tasks.evaluate_smart_notification_task(user_id=uuid4(), triggered_by="scheduled")

    assert handler.calls
    assert gateway.closed is True


@pytest.mark.asyncio
async def test_evaluate_kiosk_notification_task_calls_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway = _patch_gateway(monkeypatch)
    _patch_factory_helpers(monkeypatch)
    handler = _HandlerRecorder(calls=[])
    monkeypatch.setattr(
        worker_tasks, "get_kiosk_notification_handler", lambda **_: handler
    )

    await worker_tasks.evaluate_kiosk_notification_task(user_id=uuid4(), triggered_by="scheduled")

    assert handler.calls
    assert gateway.closed is True


@pytest.mark.asyncio
async def test_trigger_alarms_for_all_users_task_enqueues() -> None:
    users = [_build_user(uuid4()), _build_user(uuid4())]
    recorder = _TaskRecorder(calls=[])
    worker_tasks.trigger_alarms_for_user_task.kiq = recorder.kiq

    await worker_tasks.trigger_alarms_for_all_users_task(user_repo=_UserRepo(users=users))

    assert len(recorder.calls) == 2


@pytest.mark.asyncio
async def test_trigger_alarms_for_user_task_triggers_alarm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway = _patch_gateway(monkeypatch)
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

    async def get_day(day_id_arg: UUID) -> DayEntity:
        if day_id_arg == day_id:
            return day
        raise RuntimeError("missing")

    day_repo.get = get_day
    uow = create_uow_double(day_repo=day_repo)

    class _Factory:
        def create(self, _: UUID) -> object:
            return uow

    monkeypatch.setattr(worker_tasks, "get_unit_of_work_factory", lambda _: _Factory())
    monkeypatch.setattr(worker_tasks, "get_current_date", lambda _: day.date)
    monkeypatch.setattr(worker_tasks, "get_current_datetime", lambda: datetime(2025, 11, 27, 8, 0, tzinfo=UTC))

    await worker_tasks.trigger_alarms_for_user_task(
        user_id=user_id, user_repo=_UserRepo(users=[_build_user(user_id)])
    )

    assert uow.added
    assert gateway.closed is True


@pytest.mark.asyncio
async def test_heartbeat_task() -> None:
    await worker_tasks.heartbeat_task()


@pytest.mark.asyncio
async def test_evaluate_morning_overviews_for_all_users_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    eligible_user = _build_user(
        uuid4(),
        llm_provider=value_objects.LLMProvider.OPENAI,
        morning_overview_time="08:00",
        timezone="UTC",
    )
    invalid_user = _build_user(
        uuid4(),
        llm_provider=value_objects.LLMProvider.OPENAI,
        morning_overview_time="bad",
        timezone="UTC",
    )
    late_user = _build_user(
        uuid4(),
        llm_provider=value_objects.LLMProvider.OPENAI,
        morning_overview_time="09:00",
        timezone="UTC",
    )
    users = [eligible_user, invalid_user, late_user]

    recorder = _TaskRecorder(calls=[])
    worker_tasks.evaluate_morning_overview_task.kiq = recorder.kiq

    class _PushRepo:
        async def search(self, _: object) -> list[object]:
            return []

    class _RORepos:
        push_notification_ro_repo = _PushRepo()

    class _Factory:
        def create(self, _: UUID) -> object:
            return _RORepos()

    monkeypatch.setattr(worker_tasks, "get_read_only_repository_factory", lambda: _Factory())
    monkeypatch.setattr(worker_tasks, "get_current_time", lambda _: time(8, 5))
    monkeypatch.setattr(
        worker_tasks,
        "get_current_datetime_in_timezone",
        lambda _: datetime(2025, 11, 27, 8, 0, tzinfo=UTC),
    )

    await worker_tasks.evaluate_morning_overviews_for_all_users_task(
        user_repo=_UserRepo(users=users)
    )

    assert len(recorder.calls) == 1


@pytest.mark.asyncio
async def test_evaluate_morning_overview_task_calls_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway = _patch_gateway(monkeypatch)
    _patch_factory_helpers(monkeypatch)
    handler = _HandlerRecorder(calls=[])
    monkeypatch.setattr(
        worker_tasks, "get_morning_overview_handler", lambda **_: handler
    )

    await worker_tasks.evaluate_morning_overview_task(user_id=uuid4())

    assert handler.calls
    assert gateway.closed is True


@pytest.mark.asyncio
async def test_process_brain_dump_item_task_handles_invalid_date() -> None:
    await worker_tasks.process_brain_dump_item_task(
        user_id=uuid4(), day_date="bad", item_id=uuid4()
    )


@pytest.mark.asyncio
async def test_process_brain_dump_item_task_calls_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gateway = _patch_gateway(monkeypatch)
    _patch_factory_helpers(monkeypatch)
    handler = _HandlerRecorder(calls=[])
    monkeypatch.setattr(
        worker_tasks, "get_process_brain_dump_handler", lambda **_: handler
    )

    await worker_tasks.process_brain_dump_item_task(
        user_id=uuid4(),
        day_date="2025-11-27",
        item_id=uuid4(),
    )

    assert handler.calls
    assert gateway.closed is True


@pytest.mark.asyncio
async def test_example_triggered_task() -> None:
    result = await worker_tasks.example_triggered_task("hello")

    assert result == {"status": "completed", "message": "hello"}
