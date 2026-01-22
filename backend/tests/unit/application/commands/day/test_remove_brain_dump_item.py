"""Unit tests for RemoveBrainDumpItemHandler."""

from datetime import date as dt_date
from uuid import uuid4

import pytest

from lykke.application.commands.day import (
    RemoveBrainDumpItemCommand,
    RemoveBrainDumpItemHandler,
)
from lykke.core.exceptions import DomainError, NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, DayTemplateEntity, UserEntity
from lykke.domain.events.day_events import BrainDumpItemRemovedEvent


class _FakeDayReadOnlyRepo:
    def __init__(self, day: DayEntity | None = None) -> None:
        self._day = day

    async def get(self, day_id):
        if self._day and day_id == self._day.id:
            return self._day
        raise NotFoundError(f"Day {day_id} not found")


class _FakeDayTemplateReadOnlyRepo:
    def __init__(self, template: DayTemplateEntity) -> None:
        self._template = template

    async def search_one(self, query):
        return self._template


class _FakeUserReadOnlyRepo:
    def __init__(self, user: UserEntity) -> None:
        self._user = user

    async def get(self, _user_id):
        return self._user


class _FakeReadOnlyRepos:
    def __init__(
        self,
        day_repo: _FakeDayReadOnlyRepo,
        day_template_repo: _FakeDayTemplateReadOnlyRepo,
        user_repo: _FakeUserReadOnlyRepo,
    ) -> None:
        fake = object()
        self.audit_log_ro_repo = fake
        self.auth_token_ro_repo = fake
        self.bot_personality_ro_repo = fake
        self.calendar_entry_ro_repo = fake
        self.calendar_entry_series_ro_repo = fake
        self.calendar_ro_repo = fake
        self.conversation_ro_repo = fake
        self.day_ro_repo = day_repo
        self.day_template_ro_repo = day_template_repo
        self.factoid_ro_repo = fake
        self.message_ro_repo = fake
        self.notification_ro_repo = fake
        self.push_notification_ro_repo = fake
        self.push_subscription_ro_repo = fake
        self.routine_ro_repo = fake
        self.task_definition_ro_repo = fake
        self.task_ro_repo = fake
        self.template_ro_repo = fake
        self.time_block_definition_ro_repo = fake
        self.usecase_config_ro_repo = fake
        self.user_ro_repo = user_repo


class _FakeUoW:
    def __init__(self, day_repo, day_template_repo, user_repo) -> None:
        self.added = []
        self.day_ro_repo = day_repo
        self.day_template_ro_repo = day_template_repo
        self.user_ro_repo = user_repo

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    def add(self, entity):
        self.added.append(entity)
        return entity


class _FakeUoWFactory:
    def __init__(self, day_repo, day_template_repo, user_repo) -> None:
        self.uow = _FakeUoW(day_repo, day_template_repo, user_repo)

    def create(self, _user_id):
        return self.uow


@pytest.mark.asyncio
async def test_remove_brain_dump_item_removes():
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)
    item = day.add_brain_dump_item("Test brain dump")
    day.collect_events()

    day_repo = _FakeDayReadOnlyRepo(day)
    day_template_repo = _FakeDayTemplateReadOnlyRepo(template)
    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )
    user_repo = _FakeUserReadOnlyRepo(user)

    ro_repos = _FakeReadOnlyRepos(day_repo, day_template_repo, user_repo)
    uow_factory = _FakeUoWFactory(day_repo, day_template_repo, user_repo)
    handler = RemoveBrainDumpItemHandler(ro_repos, uow_factory, user_id)

    result = await handler.handle(
        RemoveBrainDumpItemCommand(date=task_date, item_id=item.id)
    )

    assert len(result.brain_dump_items) == 0
    events = result.collect_events()
    assert len(events) == 1
    assert isinstance(events[0], BrainDumpItemRemovedEvent)


@pytest.mark.asyncio
async def test_remove_brain_dump_item_day_not_found():
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day_repo = _FakeDayReadOnlyRepo(None)
    day_template_repo = _FakeDayTemplateReadOnlyRepo(template)
    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )
    user_repo = _FakeUserReadOnlyRepo(user)

    ro_repos = _FakeReadOnlyRepos(day_repo, day_template_repo, user_repo)
    uow_factory = _FakeUoWFactory(day_repo, day_template_repo, user_repo)
    handler = RemoveBrainDumpItemHandler(ro_repos, uow_factory, user_id)

    with pytest.raises(NotFoundError, match="Day"):
        await handler.handle(
            RemoveBrainDumpItemCommand(date=task_date, item_id=uuid4())
        )


@pytest.mark.asyncio
async def test_remove_brain_dump_item_raises_error():
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)

    template = DayTemplateEntity(
        user_id=user_id,
        slug="default",
        routine_ids=[],
        time_blocks=[],
    )

    day = DayEntity.create_for_date(task_date, user_id, template)
    day_repo = _FakeDayReadOnlyRepo(day)
    day_template_repo = _FakeDayTemplateReadOnlyRepo(template)
    user = UserEntity(
        id=user_id,
        email="test@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(template_defaults=["default"] * 7),
    )
    user_repo = _FakeUserReadOnlyRepo(user)

    ro_repos = _FakeReadOnlyRepos(day_repo, day_template_repo, user_repo)
    uow_factory = _FakeUoWFactory(day_repo, day_template_repo, user_repo)
    handler = RemoveBrainDumpItemHandler(ro_repos, uow_factory, user_id)

    with pytest.raises(DomainError, match="Brain dump item"):
        await handler.handle(
            RemoveBrainDumpItemCommand(date=task_date, item_id=uuid4())
        )
