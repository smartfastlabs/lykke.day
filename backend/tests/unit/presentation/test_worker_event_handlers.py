"""Regression tests for worker domain event handler registration."""

import importlib
import sys
from unittest.mock import patch


def test_worker_tasks_register_domain_event_handlers_on_import() -> None:
    """Ensure worker tasks register domain event handlers.

    REGRESSION TEST: Workers process calendar sync events but previously
    did not register domain event handlers, so push notifications never fired.
    """
    module_name = "lykke.presentation.workers.tasks"

    # Ensure a clean import so module-level registration runs
    if module_name in sys.modules:
        del sys.modules[module_name]

    with patch("lykke.application.events.register_all_handlers") as register_mock:
        importlib.import_module(module_name)

    register_mock.assert_called_once()
