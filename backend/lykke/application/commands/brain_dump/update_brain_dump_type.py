"""Command to update a brain dump's type."""

from dataclasses import dataclass
from datetime import date as dt_date
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.repositories import BrainDumpRepositoryReadOnlyProtocol
from lykke.core.exceptions import DomainError
from lykke.domain import value_objects


@dataclass(frozen=True)
class UpdateBrainDumpTypeCommand(Command):
    """Command to update a brain dump's type."""

    date: dt_date
    item_id: UUID
    item_type: value_objects.BrainDumpType


class UpdateBrainDumpTypeHandler(BaseCommandHandler[UpdateBrainDumpTypeCommand, None]):
    """Updates a brain dump's type."""

    brain_dump_ro_repo: BrainDumpRepositoryReadOnlyProtocol

    async def handle(self, command: UpdateBrainDumpTypeCommand) -> None:
        """Update a brain dump's type."""
        async with self.new_uow() as uow:
            item = await self.brain_dump_ro_repo.get(command.item_id)
            if item.date != command.date:
                raise DomainError(
                    f"Brain dump {command.item_id} not found for {command.date}"
                )

            updated = item.update_type(command.item_type)
            if updated.has_events():
                uow.add(updated)
