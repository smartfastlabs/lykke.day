"""Base classes for CQRS commands."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar, get_type_hints
from uuid import UUID

from planned.application.unit_of_work import (
    ReadOnlyRepositories,
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
    """Base class for command handlers that automatically injects requested repositories.

    Subclasses should declare which repositories they need as class attributes
    with type annotations. Only the declared repositories will be extracted from
    ReadOnlyRepositories and made available as instance attributes.

    The handler also provides access to UnitOfWork through the new_uow() method.

    Example:
        class UpdateCalendarsHandler(BaseCommandHandler):
            calendar_ro_repo: CalendarRepositoryReadOnlyProtocol

            async def run(self, calendar_id: UUID) -> CalendarEntity:
                calendar = await self.calendar_ro_repo.get(calendar_id)
                async with self.new_uow() as uow:
                    uow.add(calendar)
                    return calendar
    """

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
    ) -> None:
        """Initialize the command handler with requested repositories.

        Args:
            ro_repos: All available read-only repositories
            uow_factory: Factory for creating UnitOfWork instances
            user_id: The user ID for this command context
        """
        self.user_id = user_id
        self._uow_factory = uow_factory
        self._ro_repos = ro_repos

        # Get type hints from the class (including from base classes)
        annotations = get_type_hints(self.__class__, include_extras=True)

        # Extract only the repositories that this handler has declared
        for attr_name, _attr_type in annotations.items():
            # Check if this is a repository attribute (not a method or other attribute)
            if not attr_name.startswith("_") and hasattr(ro_repos, attr_name):
                # Extract the repository from ro_repos and set it as an instance attribute
                setattr(self, attr_name, getattr(ro_repos, attr_name))

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
