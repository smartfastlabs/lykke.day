"""Brain dump background worker tasks."""

from datetime import date as dt_date
from typing import Protocol
from uuid import UUID

from loguru import logger

from lykke.application.commands.brain_dump import ProcessBrainDumpCommand
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.infrastructure.gateways import RedisPubSubGateway
from lykke.infrastructure.workers.config import broker
from lykke.presentation.utils.structured_logging import structured_task

from .common import (
    get_process_brain_dump_handler,
    get_read_only_repository_factory,
    get_unit_of_work_factory,
)


class _BrainDumpHandler(Protocol):
    async def handle(self, command: ProcessBrainDumpCommand) -> None: ...


@broker.task  # type: ignore[untyped-decorator]
@structured_task()
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
    logger.info("Starting brain dump processing for user %s item %s", user_id, item_id)

    try:
        date = dt_date.fromisoformat(day_date)
    except ValueError:
        logger.warning(
            "Invalid brain dump date %s for user %s item %s",
            day_date,
            user_id,
            item_id,
        )
        return

    pubsub_gateway = pubsub_gateway or RedisPubSubGateway()
    try:
        handler = handler or get_process_brain_dump_handler(
            user_id=user_id,
            uow_factory=uow_factory or get_unit_of_work_factory(pubsub_gateway),
            ro_repo_factory=ro_repo_factory or get_read_only_repository_factory(),
        )

        try:
            await handler.handle(ProcessBrainDumpCommand(date=date, item_id=item_id))
            logger.debug(
                "Brain dump processing completed for user %s item %s",
                user_id,
                item_id,
            )
        except Exception:  # pylint: disable=broad-except
            logger.exception(
                "Error processing brain dump for user %s item %s",
                user_id,
                item_id,
            )
    finally:
        await pubsub_gateway.close()
