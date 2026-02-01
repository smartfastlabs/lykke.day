"""Redis-backed gateway for per-user domain event backlog."""

from __future__ import annotations

import json
from datetime import datetime
from uuid import UUID

from loguru import logger
from redis import asyncio as aioredis  # type: ignore

from lykke.application.gateways.domain_event_backlog_protocol import (
    DomainEventBacklogGatewayProtocol,
    DomainEventBacklogItem,
    DomainEventBacklogListResult,
)
from lykke.core.config import settings
from lykke.core.constants import DOMAIN_EVENT_BACKLOG_KEY_PREFIX

_DEFAULT_SCAN_CHUNK_SIZE = 1000


def _to_score_ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def _build_backlog_key(user_id: UUID) -> str:
    return f"{DOMAIN_EVENT_BACKLOG_KEY_PREFIX}:{user_id}"


class RedisDomainEventBacklogGateway(DomainEventBacklogGatewayProtocol):
    """Redis-backed gateway for per-user domain event backlog."""

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
        user_id: UUID,
        search: str | None,
        event_type: str | None,
        start_time: datetime | None,
        end_time: datetime | None,
        limit: int,
        offset: int,
    ) -> DomainEventBacklogListResult:
        redis = await self._get_redis()
        backlog_key = _build_backlog_key(user_id)

        min_score: str = "-inf"
        max_score: str = "+inf"
        if start_time is not None:
            min_score = str(_to_score_ms(start_time))
        if end_time is not None:
            max_score = str(_to_score_ms(end_time))

        items: list[DomainEventBacklogItem] = []
        total_matches = 0
        scan_offset = 0

        search_lower = search.lower() if search else None
        event_type_lower = event_type.lower() if event_type else None

        while True:
            chunk: list[str] = await redis.zrevrangebyscore(
                backlog_key,
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

                    parsed = DomainEventBacklogItem(
                        id=str(event_payload["id"]),
                        event_type=str(event_payload["event_type"]),
                        event_data=raw_event_data,
                        stored_at=datetime.fromisoformat(
                            str(event_payload["stored_at"])
                        ),
                    )
                except Exception as exc:  # pylint: disable=broad-except
                    logger.warning(
                        f"Failed to parse domain event backlog entry: {exc}"
                    )
                    continue

                if event_type_lower and event_type_lower not in parsed.event_type.lower():
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

        return DomainEventBacklogListResult(
            items=items,
            total=total_matches,
            limit=limit,
            offset=offset,
            has_next=offset + limit < total_matches,
            has_previous=offset > 0,
        )

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.close()
            self._redis = None
