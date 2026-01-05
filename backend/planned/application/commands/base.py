"""Base classes for CQRS commands."""

import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar, get_type_hints
from uuid import UUID

from planned.application.queries.base import BaseQueryHandler
from planned.application.unit_of_work import (
    ReadOnlyRepositories,
    ReadOnlyRepositoryFactory,
    UnitOfWorkFactory,
    UnitOfWorkProtocol,
)

# Command type and result type
CommandT = TypeVar("CommandT", bound="Command")
ResultT = TypeVar("ResultT")


@dataclass(frozen=True)
class Command:
    """Base class for commands.

    Commands are immutable data objects representing an intent to change state.
    They should contain all data needed to execute the operation.
    Commands may cause side effects (database writes, events, etc).
    """


class BaseCommandHandler:
    """Base class for command handlers that automatically injects requested repositories and handlers.

    Subclasses should declare which repositories and handlers they need as class attributes
    with type annotations. Only the declared repositories will be extracted from
    ReadOnlyRepositories and made available as instance attributes. Handlers will be
    automatically instantiated and injected.

    The handler also provides access to UnitOfWork through the new_uow() method.

    Example:
        class UpdateCalendarsHandler(BaseCommandHandler):
            calendar_ro_repo: CalendarRepositoryReadOnlyProtocol
            preview_day_handler: PreviewDayHandler

            async def run(self, calendar_id: UUID) -> CalendarEntity:
                calendar = await self.calendar_ro_repo.get(calendar_id)
                preview = await self.preview_day_handler.preview_day(date.today())
                async with self.new_uow() as uow:
                    uow.add(calendar)
                    return calendar
    """

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
        ro_repo_factory: ReadOnlyRepositoryFactory | None = None,
    ) -> None:
        """Initialize the command handler with requested repositories and handlers.

        Args:
            ro_repos: All available read-only repositories
            uow_factory: Factory for creating UnitOfWork instances
            user_id: The user ID for this command context
            ro_repo_factory: Optional factory for creating read-only repositories.
                Required if the handler needs to inject other handlers.
        """
        self.user_id = user_id
        self._uow_factory = uow_factory
        self._ro_repos = ro_repos
        self._ro_repo_factory = ro_repo_factory

        # Get type hints from the class (including from base classes)
        annotations = get_type_hints(self.__class__, include_extras=True)

        # Extract repositories and handlers that this handler has declared
        for attr_name, attr_type in annotations.items():
            # Skip private attributes and methods
            if attr_name.startswith("_"):
                continue

            # Check if this is a repository attribute
            if hasattr(ro_repos, attr_name):
                # Extract the repository from ro_repos and set it as an instance attribute
                setattr(self, attr_name, getattr(ro_repos, attr_name))
            # Check if this is a handler type (BaseCommandHandler or BaseQueryHandler subclass)
            elif self._is_handler_type(attr_type):
                handler_instance = self._create_handler(attr_type, attr_name)
                setattr(self, attr_name, handler_instance)

    def _is_handler_type(self, attr_type: type) -> bool:
        """Check if a type is a handler (BaseCommandHandler or BaseQueryHandler subclass).

        Args:
            attr_type: The type to check

        Returns:
            True if the type is a handler, False otherwise
        """
        if not inspect.isclass(attr_type):
            return False

        # Check if it's a subclass of BaseCommandHandler or BaseQueryHandler
        # Use MRO to avoid forward reference issues
        mro = inspect.getmro(attr_type)
        base_command_handler = type(self).__bases__[
            0
        ]  # Get BaseCommandHandler from self
        return base_command_handler in mro or BaseQueryHandler in mro

    def _create_handler(self, handler_class: type, attr_name: str) -> Any:
        """Create an instance of a handler.

        Args:
            handler_class: The handler class to instantiate
            attr_name: The attribute name (for error messages)

        Returns:
            An instance of the handler

        Raises:
            ValueError: If ro_repo_factory is required but not provided
        """
        # Check if it's a command handler by checking MRO
        mro = inspect.getmro(handler_class)
        base_command_handler = type(self).__bases__[
            0
        ]  # Get BaseCommandHandler from self
        if base_command_handler in mro:
            # Command handlers need: ro_repos, uow_factory, user_id, ro_repo_factory
            if self._ro_repo_factory is None:
                raise ValueError(
                    f"ro_repo_factory is required to inject {attr_name} "
                    f"({handler_class.__name__})"
                )
            return handler_class(
                self._ro_repos,
                self._uow_factory,
                self.user_id,
                self._ro_repo_factory,
            )
        elif issubclass(handler_class, BaseQueryHandler):
            # Query handlers need: ro_repos, user_id
            return handler_class(self._ro_repos, self.user_id)
        else:
            raise ValueError(f"Unknown handler type: {handler_class}")

    def new_uow(self, user_id: UUID | None = None) -> UnitOfWorkProtocol:
        """Create a new UnitOfWork instance.

        Args:
            user_id: Optional user ID. If not provided, uses self.user_id.

        Returns:
            A UnitOfWork context manager instance.
        """
        return self._uow_factory.create(user_id or self.user_id)


class CommandHandler(ABC, Generic[CommandT, ResultT]):
    """Base class for command handlers.

    Each handler processes exactly one type of command.
    Command handlers:
    - Validate the command
    - Execute business logic
    - Persist changes via Unit of Work
    - Return a result

    Example:
        class ScheduleDayHandler(CommandHandler[ScheduleDayCommand, DayContext]):
            async def handle(self, cmd: ScheduleDayCommand) -> DayContext:
                async with self.uow_factory.create(cmd.user_id) as uow:
                    day = await self._create_day(uow, cmd)
                    day.schedule(template)
                    await uow.create(day)
                    return day_context
    """

    @abstractmethod
    async def handle(self, command: CommandT) -> ResultT:
        """Execute the command and return the result.

        Args:
            command: The command to execute

        Returns:
            The result of the command execution
        """
