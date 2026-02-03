"""Command to delete a usecase config."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.repositories import UseCaseConfigRepositoryReadOnlyProtocol


@dataclass(frozen=True)
class DeleteUseCaseConfigCommand(Command):
    """Command to delete a usecase config."""

    usecase_config_id: UUID


class DeleteUseCaseConfigHandler(BaseCommandHandler[DeleteUseCaseConfigCommand, None]):
    """Deletes a usecase config."""

    usecase_config_ro_repo: UseCaseConfigRepositoryReadOnlyProtocol

    async def handle(self, command: DeleteUseCaseConfigCommand) -> None:
        """Delete a usecase config."""
        async with self.new_uow() as uow:
            config = await self.usecase_config_ro_repo.get(command.usecase_config_id)
            if config:
                await uow.delete(config)
