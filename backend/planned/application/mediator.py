"""Mediator for dispatching commands and queries to their handlers.

The mediator provides a clean interface for executing CQRS operations
without the caller needing to know about specific handler implementations.
"""

from typing import Any, TypeVar, overload

from planned.application.commands.base import Command, CommandHandler
from planned.application.commands.bulk_create_entities import (
    BulkCreateEntitiesCommand,
    BulkCreateEntitiesHandler,
)
from planned.application.commands.create_entity import (
    CreateEntityCommand,
    CreateEntityHandler,
)
from planned.application.commands.delete_entity import (
    DeleteEntityCommand,
    DeleteEntityHandler,
)
from planned.application.commands.record_task_action import (
    RecordTaskActionCommand,
    RecordTaskActionHandler,
)
from planned.application.commands.schedule_day import (
    ScheduleDayCommand,
    ScheduleDayHandler,
)
from planned.application.commands.update_day import UpdateDayCommand, UpdateDayHandler
from planned.application.commands.update_entity import (
    UpdateEntityCommand,
    UpdateEntityHandler,
)
from planned.application.queries.base import Query, QueryHandler
from planned.application.queries.get_day_context import (
    GetDayContextHandler,
    GetDayContextQuery,
)
from planned.application.queries.get_entity import GetEntityHandler, GetEntityQuery
from planned.application.queries.list_entities import (
    ListEntitiesHandler,
    ListEntitiesQuery,
)
from planned.application.queries.preview_day import PreviewDayHandler, PreviewDayQuery
from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import Day, DayContext, Task
from planned.domain.value_objects.query import PagedQueryResponse

# TypeVar for generic entity operations
EntityT = TypeVar("EntityT")


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

        # Generic entity operations preserve types
        template = await mediator.query(GetEntityQuery[DayTemplate](...))
    """

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

        # Initialize query handlers
        self._query_handlers: dict[type[Query], QueryHandler[Any, Any]] = {
            GetDayContextQuery: GetDayContextHandler(uow_factory),
            PreviewDayQuery: PreviewDayHandler(uow_factory),
            # Generic CRUD queries
            GetEntityQuery: GetEntityHandler(uow_factory),
            ListEntitiesQuery: ListEntitiesHandler(uow_factory),
        }

        # Initialize command handlers
        self._command_handlers: dict[type[Command], CommandHandler[Any, Any]] = {
            ScheduleDayCommand: ScheduleDayHandler(uow_factory),
            UpdateDayCommand: UpdateDayHandler(uow_factory),
            RecordTaskActionCommand: RecordTaskActionHandler(uow_factory),
            # Generic CRUD commands
            CreateEntityCommand: CreateEntityHandler(uow_factory),
            UpdateEntityCommand: UpdateEntityHandler(uow_factory),
            DeleteEntityCommand: DeleteEntityHandler(uow_factory),
            BulkCreateEntitiesCommand: BulkCreateEntitiesHandler(uow_factory),
        }

    # ========================================================================
    # Query overloads - each query type has a specific return type
    # ========================================================================

    @overload
    async def query(self, query: GetDayContextQuery) -> DayContext: ...

    @overload
    async def query(self, query: PreviewDayQuery) -> DayContext: ...

    @overload
    async def query(self, query: GetEntityQuery[EntityT]) -> EntityT: ...

    @overload
    async def query(
        self, query: ListEntitiesQuery[EntityT]
    ) -> list[EntityT] | PagedQueryResponse[EntityT]: ...

    async def query(self, query: Query) -> Any:
        """Execute a query and return the result.

        Args:
            query: The query to execute

        Returns:
            The query result

        Raises:
            KeyError: If no handler is registered for the query type
        """
        handler = self._query_handlers.get(type(query).__mro__[0])
        if handler is None:
            # Try without generic parameter (for GetEntityQuery[T] -> GetEntityQuery)
            for base in type(query).__mro__:
                if hasattr(base, "__origin__"):
                    handler = self._query_handlers.get(base.__origin__)
                    if handler:
                        break
                else:
                    handler = self._query_handlers.get(base)
                    if handler:
                        break
        if handler is None:
            raise KeyError(
                f"No handler registered for query type: {type(query).__name__}"
            )
        return await handler.handle(query)

    # ========================================================================
    # Command overloads - each command type has a specific return type
    # ========================================================================

    @overload
    async def execute(self, command: ScheduleDayCommand) -> DayContext: ...

    @overload
    async def execute(self, command: UpdateDayCommand) -> Day: ...

    @overload
    async def execute(self, command: RecordTaskActionCommand) -> Task: ...

    @overload
    async def execute(self, command: CreateEntityCommand[EntityT]) -> EntityT: ...

    @overload
    async def execute(self, command: UpdateEntityCommand[EntityT]) -> EntityT: ...

    @overload
    async def execute(self, command: DeleteEntityCommand) -> None: ...

    @overload
    async def execute(
        self, command: BulkCreateEntitiesCommand[EntityT]
    ) -> list[EntityT]: ...

    async def execute(self, command: Command) -> Any:
        """Execute a command and return the result.

        Args:
            command: The command to execute

        Returns:
            The command result

        Raises:
            KeyError: If no handler is registered for the command type
        """
        handler = self._command_handlers.get(type(command).__mro__[0])
        if handler is None:
            # Try without generic parameter (for CreateEntityCommand[T] -> CreateEntityCommand)
            for base in type(command).__mro__:
                if hasattr(base, "__origin__"):
                    handler = self._command_handlers.get(base.__origin__)
                    if handler:
                        break
                else:
                    handler = self._command_handlers.get(base)
                    if handler:
                        break
        if handler is None:
            raise KeyError(
                f"No handler registered for command type: {type(command).__name__}"
            )
        return await handler.handle(command)
