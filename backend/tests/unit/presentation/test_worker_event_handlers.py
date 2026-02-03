"""Regression tests for worker domain event handler registration."""

import importlib
import sys

from lykke.presentation.workers.tasks import registration as worker_registration


def test_worker_tasks_register_domain_event_handlers_on_import() -> None:
    """Ensure worker tasks register domain event handlers.

    REGRESSION TEST: Workers process calendar sync events but previously
    did not register domain event handlers, so push notifications never fired.
    """
    module_name = "lykke.presentation.workers.tasks"
    calls: list[tuple[object, object]] = []

    def register_all_handlers(
        *,
        ro_repo_factory: object,
        uow_factory: object,
        user_loader: object | None = None,
        handler_factory: object | None = None,
    ) -> None:
        _ = (handler_factory, user_loader)
        calls.append((ro_repo_factory, uow_factory))

    worker_registration.set_register_handlers_override(register_all_handlers)

    # Ensure a clean import so module-level registration runs
    if module_name in sys.modules:
        del sys.modules[module_name]

    importlib.import_module(module_name)
    worker_registration.set_register_handlers_override(None)

    assert calls
