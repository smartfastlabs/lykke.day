"""Redis-backed structured log backlog gateway (admin backlog + stream).

This backlog is produced by `StructuredLogGateway` and (also) by UnitOfWork's
post-commit broadcast of domain events into the structured log backlog.

The underlying Redis key/channel names are defined in `core.constants` as:
- `STRUCTURED_LOG_BACKLOG_KEY` (sorted-set backlog)
- `STRUCTURED_LOG_STREAM_CHANNEL` (pub/sub stream)
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from loguru import logger
from redis import asyncio as aioredis  # type: ignore

from lykke.application.gateways.structured_log_backlog_protocol import (
    StructuredLogBacklogGatewayProtocol,
    StructuredLogBacklogItem,
    StructuredLogBacklogListResult,
    StructuredLogBacklogStreamGatewayProtocol,
    StructuredLogBacklogStreamSubscription,
)
from lykke.core.config import settings
from lykke.core.constants import (
    STRUCTURED_LOG_BACKLOG_KEY,
    STRUCTURED_LOG_STREAM_CHANNEL,
)

_DEFAULT_SCAN_CHUNK_SIZE = 1000


def _to_score_ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


class _RedisStructuredLogBacklogStreamSubscription(
    StructuredLogBacklogStreamSubscription
):
    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis
        self._pubsub: Any | None = None

    async def __aenter__(self) -> _RedisStructuredLogBacklogStreamSubscription:
        self._pubsub = self._redis.pubsub()
        await self._pubsub.subscribe(STRUCTURED_LOG_STREAM_CHANNEL)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        await self.close()

    async def get_message(self, timeout: float | None = None) -> dict[str, Any] | None:
        if self._pubsub is None:
            return None

        raw = await self._pubsub.get_message(
            ignore_subscribe_messages=True, timeout=timeout
        )
        if not raw or raw.get("type") != "message":
            return None

        data = raw.get("data")
        if not isinstance(data, str):
            return None
        try:
            payload = json.loads(data)
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning(
                f"Failed to decode structured log backlog stream payload: {exc}"
            )
            return None
        if not isinstance(payload, dict):
            return None
        return payload

    async def close(self) -> None:
        if self._pubsub is not None:
            try:
                await self._pubsub.unsubscribe(STRUCTURED_LOG_STREAM_CHANNEL)
            except Exception:  # pylint: disable=broad-except
                pass
            try:
                await self._pubsub.close()
            except Exception:  # pylint: disable=broad-except
                pass
            self._pubsub = None


class RedisStructuredLogBacklogGateway(
    StructuredLogBacklogGatewayProtocol, StructuredLogBacklogStreamGatewayProtocol
):
    """Redis-backed gateway for structured log backlog + stream."""

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

    async def list_events(
        self,
        *,
        search: str | None,
        user_id: str | None,
        event_type: str | None,
        start_time: datetime | None,
        end_time: datetime | None,
        limit: int,
        offset: int,
    ) -> StructuredLogBacklogListResult:
        redis = await self._get_redis()

        min_score: str = "-inf"
        max_score: str = "+inf"
        if start_time is not None:
            min_score = str(_to_score_ms(start_time))
        if end_time is not None:
            max_score = str(_to_score_ms(end_time))

        items: list[StructuredLogBacklogItem] = []
        total_matches = 0
        scan_offset = 0

        search_lower = search.lower() if search else None
        event_type_lower = event_type.lower() if event_type else None

        while True:
            chunk: list[str] = await redis.zrevrangebyscore(
                STRUCTURED_LOG_BACKLOG_KEY,
                max_score,
                min_score,
                start=scan_offset,
                num=_DEFAULT_SCAN_CHUNK_SIZE,
            )
            if not chunk:
                break
            scan_offset += len(chunk)

            for raw_event in chunk:
                try:
                    event_payload = json.loads(raw_event)
                    if not isinstance(event_payload, dict):
                        continue
                    raw_event_data = event_payload.get("event_data")
                    if not isinstance(raw_event_data, dict):
                        continue

                    parsed = StructuredLogBacklogItem(
                        id=str(event_payload["id"]),
                        event_type=str(event_payload["event_type"]),
                        event_data=raw_event_data,
                        stored_at=datetime.fromisoformat(
                            str(event_payload["stored_at"])
                        ),
                    )
                except Exception as exc:  # pylint: disable=broad-except
                    logger.warning(
                        f"Failed to parse structured log backlog entry: {exc}"
                    )
                    continue

                if user_id:
                    event_user_id = parsed.event_data.get("user_id")
                    if not event_user_id or user_id not in str(event_user_id):
                        continue

                if event_type_lower:
                    if event_type_lower not in parsed.event_type.lower():
                        continue

                if search_lower:
                    try:
                        searchable = json.dumps(event_payload).lower()
                    except Exception:  # pylint: disable=broad-except
                        searchable = str(event_payload).lower()
                    if search_lower not in searchable:
                        continue

                if total_matches >= offset and len(items) < limit:
                    items.append(parsed)
                total_matches += 1

        return StructuredLogBacklogListResult(
            items=items,
            total=total_matches,
            limit=limit,
            offset=offset,
            has_next=offset + limit < total_matches,
            has_previous=offset > 0,
        )

    def subscribe_to_stream(self) -> StructuredLogBacklogStreamSubscription:
        gateway = self

        class _LazySub(StructuredLogBacklogStreamSubscription):
            def __init__(self) -> None:
                self._inner: _RedisStructuredLogBacklogStreamSubscription | None = None

            async def __aenter__(self) -> _LazySub:
                redis = await gateway._get_redis()
                self._inner = _RedisStructuredLogBacklogStreamSubscription(redis)
                await self._inner.__aenter__()
                return self

            async def __aexit__(
                self,
                exc_type: type[BaseException] | None,
                exc_val: BaseException | None,
                exc_tb: object,
            ) -> None:
                await self.close()

            async def get_message(
                self, timeout: float | None = None
            ) -> dict[str, Any] | None:
                if self._inner is None:
                    return None
                return await self._inner.get_message(timeout=timeout)

            async def close(self) -> None:
                if self._inner is not None:
                    await self._inner.close()
                    self._inner = None

        return _LazySub()

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.close()
            self._redis = None
