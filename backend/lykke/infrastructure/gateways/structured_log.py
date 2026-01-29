"""Structured log gateway for admin event backlog."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from loguru import logger
from redis import asyncio as aioredis  # type: ignore

from lykke.core.config import settings
from lykke.core.constants import (
    DOMAIN_EVENT_LOG_KEY,
    DOMAIN_EVENT_STREAM_CHANNEL,
    MAX_DOMAIN_EVENT_LOG_SIZE,
)


class StructuredLogGateway:
    """Gateway for emitting structured log events into admin backlog."""

    def __init__(self, redis_pool: aioredis.ConnectionPool | None = None) -> None:
        self._redis_pool = redis_pool
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            if self._redis_pool is not None:
                self._redis = aioredis.Redis(
                    connection_pool=self._redis_pool,
                    encoding="utf-8",
                    decode_responses=True,
                )
            else:
                self._redis = await aioredis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                )
        return self._redis

    async def log_event(
        self,
        *,
        event_type: str,
        event_data: dict[str, Any],
        occurred_at: datetime | None = None,
    ) -> None:
        """Emit a structured log event to the admin backlog and stream."""
        timestamp = occurred_at or datetime.now(UTC)
        event_id = str(uuid.uuid4())
        log_entry = {
            "id": event_id,
            "event_type": event_type,
            "event_data": event_data,
            "stored_at": datetime.now(UTC).isoformat(),
        }
        payload = json.dumps(log_entry)
        redis = await self._get_redis()

        try:
            await redis.zadd(
                DOMAIN_EVENT_LOG_KEY, {payload: int(timestamp.timestamp() * 1000)}
            )
            await redis.zremrangebyrank(
                DOMAIN_EVENT_LOG_KEY, 0, -(MAX_DOMAIN_EVENT_LOG_SIZE + 1)
            )
            await redis.publish(DOMAIN_EVENT_STREAM_CHANNEL, payload)
        except Exception as exc:
            logger.error(f"Failed to log structured event {event_type}: {exc}")
            raise

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.close()
            self._redis = None
