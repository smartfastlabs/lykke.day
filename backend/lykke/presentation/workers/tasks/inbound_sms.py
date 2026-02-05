"""Inbound SMS background worker tasks."""

from typing import Any, Protocol, cast
from uuid import UUID

from loguru import logger

from lykke.application.commands.message import ProcessInboundSmsCommand
from lykke.application.commands.onboarding import ProcessSmsOnboardingCommand
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.domain import value_objects
from lykke.infrastructure.gateways import RedisPubSubGateway
from lykke.infrastructure.workers.config import broker

from .common import (
    get_process_sms_onboarding_handler,
    get_process_inbound_sms_handler,
    get_read_only_repository_factory,
    get_unit_of_work_factory,
    load_user,
)

def _should_use_sms_onboarding(
    *,
    user_status: value_objects.UserStatus,
    usecase_config: dict[str, object] | None,
) -> bool:
    """Decide whether inbound SMS should be handled by onboarding."""
    if user_status == value_objects.UserStatus.NEW_LEAD:
        return True
    if not usecase_config:
        return False
    state = usecase_config.get("collection_state")
    return isinstance(state, dict) and state.get("status") == "active"


class _InboundSmsHandler(Protocol):
    async def handle(self, command: Any) -> Any: ...


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
        f"Starting inbound SMS processing for user {user_id} message {message_id}"
    )

    pubsub_gateway = pubsub_gateway or RedisPubSubGateway()
    try:
        use_onboarding = False
        if handler is None:
            try:
                user = await load_user(user_id)
            except Exception:
                logger.warning(f"User not found for inbound SMS task {user_id}")
                return
            uow_factory_resolved = uow_factory or get_unit_of_work_factory(pubsub_gateway)
            ro_repo_factory_resolved = ro_repo_factory or get_read_only_repository_factory()

            # Route to onboarding when user is NEW_LEAD or onboarding is active.
            ro_repos = ro_repo_factory_resolved.create(user)
            onboarding_active = False
            try:
                configs = await ro_repos.usecase_config_ro_repo.search(
                    value_objects.UseCaseConfigQuery(usecase="sms_onboarding")
                )
                config = configs[0].config if configs and isinstance(configs[0].config, dict) else None
                onboarding_active = _should_use_sms_onboarding(
                    user_status=user.status, usecase_config=config
                )
            except Exception:  # pylint: disable=broad-except
                onboarding_active = False

            if onboarding_active:
                use_onboarding = True
                handler = get_process_sms_onboarding_handler(
                    user=user,
                    uow_factory=uow_factory_resolved,
                    ro_repo_factory=ro_repo_factory_resolved,
                )
            else:
                handler = get_process_inbound_sms_handler(
                    user=user,
                    uow_factory=uow_factory_resolved,
                    ro_repo_factory=ro_repo_factory_resolved,
                )
        else:
            use_onboarding = (
                hasattr(handler, "template_usecase")
                and getattr(handler, "template_usecase") == "sms_onboarding"
            )

        try:
            assert handler is not None
            if use_onboarding:
                await cast("Any", handler).handle(
                    ProcessSmsOnboardingCommand(message_id=message_id)
                )
            else:
                await cast("Any", handler).handle(
                    ProcessInboundSmsCommand(message_id=message_id)
                )
            logger.debug(
                f"Inbound SMS processing completed for user {user_id} message {message_id}",
            )
        except Exception:  # pylint: disable=broad-except
            logger.exception(
                f"Error processing inbound SMS for user {user_id} message {message_id}",
            )
    finally:
        await pubsub_gateway.close()
