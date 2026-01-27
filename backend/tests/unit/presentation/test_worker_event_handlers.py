"""Regression tests for worker domain event handler registration."""

import importlib
import sys

from lykke.presentation.workers.tasks import common as worker_common


def test_worker_tasks_register_domain_event_handlers_on_import() -> None:
    """Ensure worker tasks register domain event handlers.

    REGRESSION TEST: Workers process calendar sync events but previously
    did not register domain event handlers, so push notifications never fired.
    """
    module_name = "lykke.presentation.workers.tasks"
    calls: list[tuple[object, object]] = []

    def register_all_handlers(*, ro_repo_factory: object, uow_factory: object) -> None:
        calls.append((ro_repo_factory, uow_factory))

    worker_common.set_register_handlers_override(register_all_handlers)

    # Ensure a clean import so module-level registration runs
    if module_name in sys.modules:
        del sys.modules[module_name]

    importlib.import_module(module_name)
    worker_common.set_register_handlers_override(None)

    assert calls
