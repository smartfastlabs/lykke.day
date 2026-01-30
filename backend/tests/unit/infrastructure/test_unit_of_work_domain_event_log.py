"""Unit tests for UnitOfWork structured-log backlog logging."""

import json
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from lykke.core.constants import (
    MAX_DOMAIN_EVENT_LOG_SIZE,
    STRUCTURED_LOG_BACKLOG_KEY,
    STRUCTURED_LOG_STREAM_CHANNEL,
)
from lykke.domain.events.task_events import TaskCompletedEvent
from lykke.infrastructure.gateways import StubPubSubGateway
from lykke.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


class _FakeRedis:
    def __init__(self) -> None:
        self.zadd_calls: list[tuple[str, dict[str, int]]] = []
        self.zrem_calls: list[tuple[str, int, int]] = []
        self.publish_calls: list[tuple[str, str]] = []
        self.closed = False

    async def zadd(self, key: str, mapping: dict[str, int]) -> None:
        self.zadd_calls.append((key, mapping))

    async def zremrangebyrank(self, key: str, start: int, end: int) -> None:
        self.zrem_calls.append((key, start, end))

    async def publish(self, channel: str, message: str) -> None:
        self.publish_calls.append((channel, message))

    async def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_broadcast_domain_events_logs_and_streams(monkeypatch) -> None:
    """Ensure post-commit broadcast logs to backlog and admin stream."""
    fake_redis = _FakeRedis()
    created: list[_FakeRedis] = []

    async def _fake_from_url(*_args, **_kwargs) -> _FakeRedis:
        created.append(fake_redis)
        return fake_redis

    from lykke.infrastructure import unit_of_work as uow_module

    monkeypatch.setattr(uow_module.aioredis, "from_url", _fake_from_url)

    user_id = uuid4()
    task_id = uuid4()
    event = TaskCompletedEvent(
        user_id=user_id,
        task_id=task_id,
        completed_at=datetime.now(UTC),
    )

    uow = SqlAlchemyUnitOfWork(user_id=user_id, pubsub_gateway=StubPubSubGateway())

    await uow._broadcast_domain_events_to_redis([event])

    assert created == [fake_redis]
    assert fake_redis.closed is True

    assert len(fake_redis.zadd_calls) == 1
    zadd_key, zadd_mapping = fake_redis.zadd_calls[0]
    assert zadd_key == STRUCTURED_LOG_BACKLOG_KEY
    assert len(zadd_mapping) == 1

    log_json = next(iter(zadd_mapping.keys()))
    log_entry = json.loads(log_json)
    assert log_entry["event_type"].endswith("TaskCompletedEvent")
    assert log_entry["event_data"]["user_id"] == str(user_id)
    assert log_entry["event_data"]["task_id"] == str(task_id)
    assert "stored_at" in log_entry

    assert fake_redis.zrem_calls == [
        (STRUCTURED_LOG_BACKLOG_KEY, 0, -(MAX_DOMAIN_EVENT_LOG_SIZE + 1))
    ]

    assert fake_redis.publish_calls == [(STRUCTURED_LOG_STREAM_CHANNEL, log_json)]
