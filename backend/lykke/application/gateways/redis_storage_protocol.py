"""Protocol for Redis-backed key/value storage gateway."""
# pylint: disable=unnecessary-ellipsis

from typing import Any, Protocol


class RedisStorageGatewayProtocol(Protocol):
    """Protocol for JSON-capable Redis key/value storage."""

    async def set_json(
        self,
        key: str,
        value: dict[str, Any],
        *,
        ttl_seconds: int | None = None,
    ) -> None:
        """Store JSON-serializable dict payload at key with optional TTL."""
        ...

    async def get_json(self, key: str) -> dict[str, Any] | None:
        """Load dict payload for key, returning None when key is missing."""
        ...

    async def delete(self, key: str) -> None:
        """Delete key if it exists."""
        ...

    async def close(self) -> None:
        """Close any gateway-owned Redis connection resources."""
        ...
