"""Unit tests for BrainDumpProcessingTriggerHandler."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as dt_date
from typing import Any
from uuid import uuid4

import pytest

from lykke.application.events.handlers.brain_dump_processing_trigger import (
    BrainDumpProcessingTriggerHandler,
)
from lykke.domain.events.day_events import BrainDumpAddedEvent
from tests.support.dobles import create_read_only_repos_double


@dataclass
class _TaskRecorder:
    calls: list[dict[str, Any]]

    async def kiq(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)


@pytest.mark.asyncio
async def test_brain_dump_processing_enqueues_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid4()
    item_id = uuid4()
    recorder = _TaskRecorder(calls=[])

    monkeypatch.setattr(
        "lykke.presentation.workers.tasks.process_brain_dump_item_task",
        recorder,
    )

    handler = BrainDumpProcessingTriggerHandler(
        create_read_only_repos_double(), user_id
    )
    event = BrainDumpAddedEvent(
        user_id=user_id,
        day_id=uuid4(),
        date=dt_date(2025, 11, 27),
        item_id=item_id,
        item_text="New item",
    )

    await handler.handle(event)

    assert recorder.calls == [
        {
            "user_id": user_id,
            "day_date": "2025-11-27",
            "item_id": item_id,
        }
    ]


@pytest.mark.asyncio
async def test_brain_dump_processing_handles_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid4()
    item_id = uuid4()

    class _Task:
        async def kiq(self, **_: Any) -> None:
            raise RuntimeError("boom")

    monkeypatch.setattr(
        "lykke.presentation.workers.tasks.process_brain_dump_item_task",
        _Task(),
    )

    handler = BrainDumpProcessingTriggerHandler(
        create_read_only_repos_double(), user_id
    )
    event = BrainDumpAddedEvent(
        user_id=user_id,
        day_id=uuid4(),
        date=dt_date(2025, 11, 27),
        item_id=item_id,
        item_text="New item",
    )

    await handler.handle(event)


@pytest.mark.asyncio
async def test_brain_dump_processing_ignores_other_events() -> None:
    handler = BrainDumpProcessingTriggerHandler(
        create_read_only_repos_double(), uuid4()
    )

    class _OtherEvent:
        pass

    await handler.handle(_OtherEvent())  # type: ignore[arg-type]
