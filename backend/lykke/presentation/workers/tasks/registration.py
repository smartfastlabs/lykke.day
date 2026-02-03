"""Registration helpers for background worker event handlers."""

from collections.abc import Callable

from loguru import logger
from uuid import UUID

from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.domain.entities import UserEntity
from lykke.infrastructure.repositories import UserRepository

from .common import get_read_only_repository_factory, get_unit_of_work_factory

_REGISTER_HANDLERS_OVERRIDE: Callable[..., None] | None = None


def set_register_handlers_override(handler: Callable[..., None] | None) -> None:
    """Override the register_all_handlers callable (tests only)."""
    global _REGISTER_HANDLERS_OVERRIDE
    _REGISTER_HANDLERS_OVERRIDE = handler


def register_worker_event_handlers(
    *,
    register_handlers: Callable[..., None] | None = None,
    ro_repo_factory: ReadOnlyRepositoryFactory | None = None,
    uow_factory: UnitOfWorkFactory | None = None,
) -> None:
    """Register domain event handlers for background workers.

    Workers execute commands that emit domain events (e.g., calendar sync).
    Without registration, handlers like push notifications never run.
    """
    if register_handlers is None and _REGISTER_HANDLERS_OVERRIDE is None:
        from lykke.application.events import register_all_handlers

        register_handlers = register_all_handlers
    else:
        register_handlers = register_handlers or _REGISTER_HANDLERS_OVERRIDE

    if register_handlers:
        ro_repo_factory = ro_repo_factory or get_read_only_repository_factory()
        uow_factory = uow_factory or get_unit_of_work_factory()
        from lykke.presentation.handler_factory import build_domain_event_handler

        async def _load_user(user_id: UUID) -> UserEntity | None:
            user_repo = UserRepository()
            try:
                return await user_repo.get(user_id)
            except Exception:
                return None

        register_handlers(
            ro_repo_factory=ro_repo_factory,
            uow_factory=uow_factory,
            user_loader=_load_user,
            handler_factory=build_domain_event_handler,
        )
        logger.info("Registered domain event handlers for worker process")
