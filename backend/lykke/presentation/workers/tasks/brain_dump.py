"""Brain dump background worker tasks."""

from datetime import date as dt_date
from typing import Protocol
from uuid import UUID

from loguru import logger

from lykke.application.commands.brain_dump import ProcessBrainDumpCommand
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.infrastructure.gateways import RedisPubSubGateway
from lykke.infrastructure.workers.config import broker

from .common import (
    get_process_brain_dump_handler,
    get_read_only_repository_factory,
    get_unit_of_work_factory,
    load_user,
)


class _BrainDumpHandler(Protocol):
    async def handle(self, command: ProcessBrainDumpCommand) -> None: ...


@broker.task  # type: ignore[untyped-decorator]
async def process_brain_dump_item_task(
    user_id: UUID,
    day_date: str,
    item_id: UUID,
    *,
    handler: _BrainDumpHandler | None = None,
    uow_factory: UnitOfWorkFactory | None = None,
    ro_repo_factory: ReadOnlyRepositoryFactory | None = None,
    pubsub_gateway: RedisPubSubGateway | None = None,
) -> None:
    """Process a brain dump item for a specific user."""
    logger.info(
        f"Starting brain dump processing for user {user_id} item {item_id}"
    )

    try:
        date = dt_date.fromisoformat(day_date)
    except ValueError:
        logger.warning(
            f"Invalid brain dump date {day_date} for user {user_id} item {item_id}"
        )
        return

    pubsub_gateway = pubsub_gateway or RedisPubSubGateway()
    try:
        if handler is None:
            try:
                user = await load_user(user_id)
            except Exception:
                logger.warning(f"User not found for brain dump task {user_id}")
                return

            handler = get_process_brain_dump_handler(
                user=user,
                uow_factory=uow_factory or get_unit_of_work_factory(pubsub_gateway),
                ro_repo_factory=ro_repo_factory or get_read_only_repository_factory(),
            )

        try:
            await handler.handle(ProcessBrainDumpCommand(date=date, item_id=item_id))
            logger.debug(
                f"Brain dump processing completed for user {user_id} item {item_id}"
            )
        except Exception:  # pylint: disable=broad-except
            logger.exception(
                f"Error processing brain dump for user {user_id} item {item_id}"
            )
    finally:
        await pubsub_gateway.close()
