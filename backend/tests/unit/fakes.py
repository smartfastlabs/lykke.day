"""Shared fake implementations for unit tests."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import (
    DayEntity,
    DayTemplateEntity,
    RoutineEntity,
    TaskEntity,
    TimeBlockDefinitionEntity,
    UserEntity,
)


class _FakeDayTemplateReadOnlyRepo:
    """Fake day template repository for testing."""

    def __init__(self, template: DayTemplateEntity) -> None:
        self._template = template

    async def get(self, template_id: UUID):
        if template_id == self._template.id:
            return self._template
        raise NotFoundError(f"Template {template_id} not found")

    async def search_one(self, _query):
        return self._template


class _FakeDayReadOnlyRepo:
    """Fake day repository for testing."""

    def __init__(self, day: DayEntity | None = None) -> None:
        self._day = day

    async def get(self, day_id: UUID):
        if self._day and day_id == self._day.id:
            return self._day
        raise NotFoundError(f"Day {day_id} not found")


class _FakeTaskReadOnlyRepo:
    """Fake task repository for testing."""

    def __init__(
        self,
        tasks: list[TaskEntity] | TaskEntity | None = None,
        task: TaskEntity | None = None,
    ) -> None:
        if isinstance(tasks, TaskEntity):
            self._tasks = [tasks]
        elif tasks is not None:
            self._tasks = tasks
        elif task is not None:
            self._tasks = [task]
        else:
            self._tasks = []

    async def get(self, task_id: UUID):
        for task in self._tasks:
            if task_id == task.id:
                return task
        raise NotFoundError(f"Task {task_id} not found")

    async def search(self, query):
        date = getattr(query, "date", None)
        if date is None:
            return self._tasks
        return [task for task in self._tasks if task.scheduled_date == date]


class _FakeCalendarEntryReadOnlyRepo:
    """Fake calendar entry repository for testing."""

    def __init__(self, entries: list[object] | None = None) -> None:
        self._entries = entries or []

    async def search(self, _query):
        return self._entries


class _FakeTimeBlockDefinitionReadOnlyRepo:
    """Fake time block definition repository for testing."""

    def __init__(self, definitions: dict[UUID, TimeBlockDefinitionEntity]) -> None:
        self._definitions = definitions

    async def get(self, def_id: UUID) -> TimeBlockDefinitionEntity:
        if def_id in self._definitions:
            return self._definitions[def_id]
        raise NotFoundError(f"TimeBlockDefinition {def_id} not found")


class _FakeRoutineReadOnlyRepo:
    """Fake routine repository for testing."""

    def __init__(
        self, routine: RoutineEntity | None = None, routines: list[RoutineEntity] | None = None
    ) -> None:
        if routines is not None:
            self._routines = routines
        elif routine is not None:
            self._routines = [routine]
        else:
            self._routines = []

    async def get(self, routine_id: UUID):
        for routine in self._routines:
            if routine_id == routine.id:
                return routine
        raise NotFoundError(f"Routine {routine_id} not found")

    async def all(self):
        return self._routines


class _FakeTaskDefinitionReadOnlyRepo:
    """Fake task definition repository for testing."""

    def __init__(self, definitions: list[object] | None = None) -> None:
        self._definitions = definitions or []

    async def search(self, _query):
        return self._definitions


class _FakeUseCaseConfigReadOnlyRepo:
    """Fake use case config repository for testing."""

    def __init__(self, configs: list[object] | None = None) -> None:
        self._configs = configs or []

    async def search(self, _query):
        return self._configs


class _FakeUserReadOnlyRepo:
    """Fake user repository for testing."""

    def __init__(self, user: UserEntity) -> None:
        self._user = user

    async def get(self, user_id: UUID):
        if user_id == self._user.id:
            return self._user
        raise NotFoundError(f"User {user_id} not found")


class _FakeReadOnlyRepos:
    """Lightweight container matching ReadOnlyRepositories protocol."""

    def __init__(
        self,
        *,
        audit_log_repo: Any | None = None,
        auth_token_repo: Any | None = None,
        bot_personality_repo: Any | None = None,
        calendar_entry_repo: Any | None = None,
        calendar_entry_series_repo: Any | None = None,
        calendar_repo: Any | None = None,
        conversation_repo: Any | None = None,
        day_repo: Any | None = None,
        day_template_repo: Any | None = None,
        factoid_repo: Any | None = None,
        message_repo: Any | None = None,
        notification_repo: Any | None = None,
        push_notification_repo: Any | None = None,
        push_subscription_repo: Any | None = None,
        routine_repo: Any | None = None,
        task_definition_repo: Any | None = None,
        task_repo: Any | None = None,
        time_block_definition_repo: Any | None = None,
        usecase_config_repo: Any | None = None,
        user_repo: Any | None = None,
    ) -> None:
        fake = object()
        self.audit_log_ro_repo = audit_log_repo or fake
        self.auth_token_ro_repo = auth_token_repo or fake
        self.bot_personality_ro_repo = bot_personality_repo or fake
        self.calendar_entry_ro_repo = calendar_entry_repo or fake
        self.calendar_entry_series_ro_repo = calendar_entry_series_repo or fake
        self.calendar_ro_repo = calendar_repo or fake
        self.conversation_ro_repo = conversation_repo or fake
        self.day_ro_repo = day_repo or fake
        self.day_template_ro_repo = day_template_repo or fake
        self.factoid_ro_repo = factoid_repo or fake
        self.message_ro_repo = message_repo or fake
        self.notification_ro_repo = notification_repo or fake
        self.push_notification_ro_repo = push_notification_repo or fake
        self.push_subscription_ro_repo = push_subscription_repo or fake
        self.routine_ro_repo = routine_repo or fake
        self.task_definition_ro_repo = task_definition_repo or fake
        self.task_ro_repo = task_repo or fake
        self.time_block_definition_ro_repo = time_block_definition_repo or fake
        self.usecase_config_ro_repo = usecase_config_repo or fake
        self.user_ro_repo = user_repo or fake


class _FakeUoW:
    """Minimal UnitOfWork that collects created/added entities."""

    def __init__(
        self,
        *,
        task_repo: Any | None = None,
        day_repo: Any | None = None,
        day_template_repo: Any | None = None,
        user_repo: Any | None = None,
        calendar_entry_repo: Any | None = None,
        time_block_definition_repo: Any | None = None,
        created_entities: list[object] | None = None,
    ) -> None:
        self.added: list[object] = []
        self.created_entities = created_entities or []
        self.created = self.created_entities
        self.bulk_deleted_tasks: list[object] = []
        self.task_ro_repo = task_repo
        self.day_ro_repo = day_repo
        self.day_template_ro_repo = day_template_repo
        self.user_ro_repo = user_repo
        self.calendar_entry_ro_repo = calendar_entry_repo
        self.time_block_definition_ro_repo = time_block_definition_repo

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    def add(self, entity):
        self.added.append(entity)
        return entity

    async def create(self, entity):
        self.created_entities.append(entity)
        if hasattr(entity, "create"):
            entity.create()
        return entity

    async def bulk_delete_tasks(self, query):
        self.bulk_deleted_tasks.append(query)


class _FakeUoWFactory:
    def __init__(self, uow: _FakeUoW) -> None:
        self.uow = uow

    def create(self, _user_id):
        return self.uow


class _FakePreviewDayHandler:
    """Fake preview day handler for testing."""

    def __init__(
        self,
        day: DayEntity,
        tasks: list[TaskEntity],
        calendar_entries: list[object] | None = None,
    ) -> None:
        self._day = day
        self._tasks = tasks
        self._calendar_entries = calendar_entries or []

    async def preview_day(self, _date, template_id=None):
        return value_objects.DayContext(
            day=self._day,
            tasks=self._tasks,
            calendar_entries=self._calendar_entries,
        )
