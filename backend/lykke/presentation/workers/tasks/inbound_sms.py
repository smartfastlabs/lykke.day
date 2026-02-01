"""Inbound SMS background worker tasks."""

from typing import Protocol
from uuid import UUID

from loguru import logger

from lykke.application.commands.message import ProcessInboundSmsCommand
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.infrastructure.gateways import RedisPubSubGateway
from lykke.infrastructure.workers.config import broker

from .common import (
    get_process_inbound_sms_handler,
    get_read_only_repository_factory,
    get_unit_of_work_factory,
)


class _InboundSmsHandler(Protocol):
    async def handle(self, command: ProcessInboundSmsCommand) -> None: ...


@broker.task  # type: ignore[untyped-decorator]
async def process_inbound_sms_message_task(
    user_id: UUID,
    message_id: UUID,
    *,
    handler: _InboundSmsHandler | None = None,
    uow_factory: UnitOfWorkFactory | None = None,
    ro_repo_factory: ReadOnlyRepositoryFactory | None = None,
    pubsub_gateway: RedisPubSubGateway | None = None,
) -> None:
    """Process an inbound SMS message for a specific user."""
    logger.info(
        "Starting inbound SMS processing for user %s message %s", user_id, message_id
    )

    pubsub_gateway = pubsub_gateway or RedisPubSubGateway()
    try:
        handler = handler or get_process_inbound_sms_handler(
            user_id=user_id,
            uow_factory=uow_factory or get_unit_of_work_factory(pubsub_gateway),
            ro_repo_factory=ro_repo_factory or get_read_only_repository_factory(),
        )

        try:
            await handler.handle(ProcessInboundSmsCommand(message_id=message_id))
            logger.debug(
                "Inbound SMS processing completed for user %s message %s",
                user_id,
                message_id,
            )
        except Exception:  # pylint: disable=broad-except
            logger.exception(
                "Error processing inbound SMS for user %s message %s",
                user_id,
                message_id,
            )
    finally:
        await pubsub_gateway.close()
