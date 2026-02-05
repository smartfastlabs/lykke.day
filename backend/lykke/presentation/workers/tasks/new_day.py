"""New day event background worker tasks.

These tasks publish `NewDayEvent` to the user's `domain-events` Redis channel.

IMPORTANT: `NewDayEvent` is intentionally decoupled from day scheduling.
Days may be scheduled ahead of time (e.g. user views tomorrow), but the
"new day" signal should only be emitted on the actual day (per user timezone),
in the middle of the night, similar to `schedule_all_users_day_task`.
"""

from collections.abc import Callable
from datetime import date as dt_date
from typing import Annotated, Protocol
from uuid import UUID

from loguru import logger
from taskiq_dependencies import Depends

from lykke.application.identity import UnauthenticatedIdentityAccessProtocol
from lykke.core.utils.dates import get_current_date
from lykke.core.utils.domain_event_serialization import serialize_domain_event
from lykke.domain.entities import DayEntity
from lykke.domain.events.day_events import NewDayEvent
from lykke.infrastructure.gateways import RedisPubSubGateway
from lykke.infrastructure.workers.config import broker

from .common import get_identity_access


class _EnqueueTask(Protocol):
    async def kiq(self, **kwargs: object) -> None: ...


class _PubSubGateway(Protocol):
    async def publish_to_user_channel(
        self,
        user_id: UUID,
        channel_type: str,
        message: dict[str, object],
    ) -> None: ...

    async def close(self) -> None: ...


@broker.task(schedule=[{"cron": "5 3 * * *"}])  # type: ignore[untyped-decorator]
async def emit_new_day_event_for_all_users_task(
    identity_access: Annotated[
        UnauthenticatedIdentityAccessProtocol, Depends(get_identity_access)
    ],
    *,
    enqueue_task: _EnqueueTask | None = None,
) -> None:
    """Load all users and enqueue a NewDayEvent publish task for each user."""
    logger.info("Starting new-day event task for all users")

    users = await identity_access.list_all_users()
    logger.info(f"Found {len(users)} users to emit new-day events for")

    task = enqueue_task or emit_new_day_event_for_user_task
    for user in users:
        await task.kiq(user_id=user.id)

    logger.info(f"Enqueued new-day event tasks for {len(users)} users")


@broker.task  # type: ignore[untyped-decorator]
async def emit_new_day_event_for_user_task(
    user_id: UUID,
    identity_access: Annotated[
        UnauthenticatedIdentityAccessProtocol, Depends(get_identity_access)
    ],
    *,
    pubsub_gateway: _PubSubGateway | None = None,
    current_date_provider: Callable[[str | None], dt_date] | None = None,
) -> None:
    """Publish a NewDayEvent for today's date in the user's timezone."""
    logger.info(f"Publishing NewDayEvent for user {user_id}")

    pubsub_gateway = pubsub_gateway or RedisPubSubGateway()
    try:
        user = await identity_access.get_user_by_id(user_id)
        timezone = user.settings.timezone if user and user.settings else None

        current_date_provider = current_date_provider or get_current_date
        target_date = current_date_provider(timezone)

        day_id = DayEntity.id_from_date_and_user(target_date, user_id)
        event = NewDayEvent(
            user_id=user_id,
            day_id=day_id,
            date=target_date,
            entity_id=day_id,
            entity_type="day",
            entity_date=target_date,
        )

        await pubsub_gateway.publish_to_user_channel(
            user_id=user_id,
            channel_type="domain-events",
            message=serialize_domain_event(event),
        )
        logger.debug(f"Published NewDayEvent for {target_date} (user {user_id})")
    finally:
        await pubsub_gateway.close()
