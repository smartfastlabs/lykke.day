"""Command handler dependency injection functions organized by entity.

This module previously contained wrapper functions for command handlers,
but most have been replaced by the generic factory functions in
dependencies.factories.get_command_handler().

Special handlers with additional dependencies (e.g., google_gateway) are
still defined in their respective modules (e.g., calendar.py, push_subscription.py).
"""

