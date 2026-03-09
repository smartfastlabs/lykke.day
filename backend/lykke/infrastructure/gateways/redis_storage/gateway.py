"""Redis-based key/value storage gateway."""
# pylint: disable=import-error

import json
from typing import Any, cast

from redis import asyncio as aioredis  # type: ignore

from lykke.application.gateways import RedisStorageGatewayProtocol
from lykke.core.config import settings


class RedisStorageGateway(RedisStorageGatewayProtocol):
    """Redis-backed key/value storage with JSON payload helpers."""

    def __init__(self, redis_pool: aioredis.ConnectionPool | None = None) -> None:
        self._redis: aioredis.Redis | None = None
        self._redis_pool = redis_pool
        self._owns_connection = redis_pool is None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            if self._redis_pool is not None:
                self._redis = aioredis.Redis(
                    connection_pool=self._redis_pool,
                    encoding="utf-8",
                    decode_responses=False,
                )
            else:
                self._redis = await aioredis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=False,
                )
        return self._redis

    async def set_json(
        self,
        key: str,
        value: dict[str, Any],
        *,
        ttl_seconds: int | None = None,
    ) -> None:
        redis = await self._get_redis()
        payload = json.dumps(value)
        if ttl_seconds is not None:
            await redis.setex(key, ttl_seconds, payload)
            return
        await redis.set(key, payload)

    async def get_json(self, key: str) -> dict[str, Any] | None:
        redis = await self._get_redis()
        payload_raw = await redis.get(key)
        if payload_raw is None:
            return None
        payload_text = (
            payload_raw.decode("utf-8")
            if isinstance(payload_raw, bytes)
            else str(payload_raw)
        )
        parsed = json.loads(payload_text)
        if isinstance(parsed, dict):
            return cast("dict[str, Any]", parsed)
        return None

    async def delete(self, key: str) -> None:
        redis = await self._get_redis()
        await redis.delete(key)

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.close()
            self._redis = None
