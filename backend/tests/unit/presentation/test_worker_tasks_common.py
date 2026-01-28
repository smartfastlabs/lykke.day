"""Unit tests for worker task helpers."""

from lykke.infrastructure.gateways import GoogleCalendarGateway
from lykke.infrastructure.repositories import UserRepository
from lykke.presentation.workers.tasks import (
    common as worker_common,
    registration as worker_registration,
)


def test_register_worker_event_handlers() -> None:
    calls: list[tuple[object, object]] = []

    def register_all_handlers(*, ro_repo_factory: object, uow_factory: object) -> None:
        calls.append((ro_repo_factory, uow_factory))

    worker_registration.register_worker_event_handlers(
        register_handlers=register_all_handlers,
        ro_repo_factory="ro",
        uow_factory="uow",
    )

    assert calls == [("ro", "uow")]


def test_get_google_gateway_returns_concrete_gateway() -> None:
    assert isinstance(worker_common.get_google_gateway(), GoogleCalendarGateway)


def test_get_user_repository_returns_repository() -> None:
    assert isinstance(worker_common.get_user_repository(), UserRepository)


def test_register_worker_event_handlers_logs() -> None:
    calls: list[tuple[object, object]] = []

    def register_all_handlers(*, ro_repo_factory: object, uow_factory: object) -> None:
        calls.append((ro_repo_factory, uow_factory))

    worker_registration.register_worker_event_handlers(
        register_handlers=register_all_handlers,
        ro_repo_factory="ro",
        uow_factory="uow",
    )

    assert calls
