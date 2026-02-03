"""Unit tests for task status related handlers."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from lykke.application.events.handlers.task_status_logger import TaskStatusLoggerHandler
from lykke.domain.entities import UserEntity
from lykke.domain.events.task_events import TaskCompletedEvent, TaskStatusChangedEvent
from tests.support.dobles import create_read_only_repos_double


class _RepositoryFactory:
    def __init__(self, ro_repos: object) -> None:
        self._ro_repos = ro_repos

    def create(self, user: object) -> object:
        _ = user
        return self._ro_repos


@pytest.mark.asyncio
async def test_task_status_logger_handles_events() -> None:
    user_id = uuid4()
    user = UserEntity(id=user_id, email="test@example.com", hashed_password="!")
    handler = TaskStatusLoggerHandler(
        user=user,
        repository_factory=_RepositoryFactory(create_read_only_repos_double()),
    )

    await handler.handle(
        TaskStatusChangedEvent(
            user_id=user_id,
            task_id=uuid4(),
            old_status="ready",
            new_status="complete",
        )
    )
    await handler.handle(
        TaskCompletedEvent(
            user_id=user_id,
            task_id=uuid4(),
            completed_at=datetime.now(UTC),
            task_scheduled_date=datetime(2025, 11, 27, tzinfo=UTC).date(),
            task_name="Task",
            task_type="work",
            task_category="work",
            entity_id=uuid4(),
            entity_type="task",
            entity_date=datetime(2025, 11, 27, tzinfo=UTC).date(),
        )
    )

    class _OtherEvent:
        pass

    await handler.handle(_OtherEvent())  # type: ignore[arg-type]
