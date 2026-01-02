"""Mediator for dispatching commands and queries to their handlers.

The mediator provides a clean interface for executing CQRS operations
without the caller needing to know about specific handler implementations.
"""

from typing import Any

from planned.application.commands.base import Command, CommandHandler
from planned.application.commands.record_task_action import (
    RecordTaskActionCommand,
    RecordTaskActionHandler,
)
from planned.application.commands.schedule_day import (
    ScheduleDayCommand,
    ScheduleDayHandler,
)
from planned.application.commands.update_day import UpdateDayCommand, UpdateDayHandler
from planned.application.queries.base import Query, QueryHandler
from planned.application.queries.get_day_context import (
    GetDayContextHandler,
    GetDayContextQuery,
)
from planned.application.queries.preview_day import PreviewDayHandler, PreviewDayQuery
from planned.application.unit_of_work import UnitOfWorkFactory


class Mediator:
    """Dispatches commands and queries to their appropriate handlers.

    The mediator decouples the caller from the handler implementation,
    making it easy to:
    - Add cross-cutting concerns (logging, validation, etc.)
    - Swap handler implementations
    - Test handlers in isolation

    Example:
        mediator = Mediator(uow_factory)

        # Execute a query
        context = await mediator.query(GetDayContextQuery(user=user, date=today))

        # Execute a command
        day = await mediator.execute(ScheduleDayCommand(user_id=user.id, date=today))
    """

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

        # Initialize handlers
        self._query_handlers: dict[type[Query], QueryHandler[Any, Any]] = {
            GetDayContextQuery: GetDayContextHandler(uow_factory),
            PreviewDayQuery: PreviewDayHandler(uow_factory),
        }

        self._command_handlers: dict[type[Command], CommandHandler[Any, Any]] = {
            ScheduleDayCommand: ScheduleDayHandler(uow_factory),
            UpdateDayCommand: UpdateDayHandler(uow_factory),
            RecordTaskActionCommand: RecordTaskActionHandler(uow_factory),
        }

    async def query(self, query: Query) -> Any:
        """Execute a query and return the result.

        Args:
            query: The query to execute

        Returns:
            The query result

        Raises:
            KeyError: If no handler is registered for the query type
        """
        handler = self._query_handlers.get(type(query))
        if handler is None:
            raise KeyError(f"No handler registered for query type: {type(query).__name__}")
        return await handler.handle(query)

    async def execute(self, command: Command) -> Any:
        """Execute a command and return the result.

        Args:
            command: The command to execute

        Returns:
            The command result

        Raises:
            KeyError: If no handler is registered for the command type
        """
        handler = self._command_handlers.get(type(command))
        if handler is None:
            raise KeyError(
                f"No handler registered for command type: {type(command).__name__}"
            )
        return await handler.handle(command)
