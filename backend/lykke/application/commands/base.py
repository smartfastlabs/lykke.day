"""Base classes for CQRS commands."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar
from uuid import UUID

from lykke.application.unit_of_work import (
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
    """Base class for command handlers with explicit dependency wiring."""

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
    ) -> None:
        """Initialize the command handler with its dependencies."""
        self.user_id = user_id
        self._uow_factory = uow_factory
        self._ro_repos = ro_repos
        # Explicitly expose read-only repositories for convenience
        self.auth_token_ro_repo = ro_repos.auth_token_ro_repo
        self.bot_personality_ro_repo = ro_repos.bot_personality_ro_repo
        self.calendar_entry_ro_repo = ro_repos.calendar_entry_ro_repo
        self.calendar_entry_series_ro_repo = ro_repos.calendar_entry_series_ro_repo
        self.calendar_ro_repo = ro_repos.calendar_ro_repo
        self.conversation_ro_repo = ro_repos.conversation_ro_repo
        self.day_ro_repo = ro_repos.day_ro_repo
        self.day_template_ro_repo = ro_repos.day_template_ro_repo
        self.factoid_ro_repo = ro_repos.factoid_ro_repo
        self.message_ro_repo = ro_repos.message_ro_repo
        self.push_subscription_ro_repo = ro_repos.push_subscription_ro_repo
        self.routine_ro_repo = ro_repos.routine_ro_repo
        self.task_definition_ro_repo = ro_repos.task_definition_ro_repo
        self.task_ro_repo = ro_repos.task_ro_repo
        self.time_block_definition_ro_repo = ro_repos.time_block_definition_ro_repo
        self.user_ro_repo = ro_repos.user_ro_repo

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
