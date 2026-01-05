"""Base classes for CQRS commands."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

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
                    day.create()  # Mark as newly created
                    uow.add(day)
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
