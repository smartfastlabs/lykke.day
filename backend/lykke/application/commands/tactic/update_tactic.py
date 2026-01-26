"""Command to update an existing tactic."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities import TacticEntity
from lykke.domain.events.trigger_tactic_events import TacticUpdatedEvent
from lykke.domain.value_objects import TacticUpdateObject


@dataclass(frozen=True)
class UpdateTacticCommand(Command):
    """Command to update an existing tactic."""

    tactic_id: UUID
    update_data: TacticUpdateObject


class UpdateTacticHandler(BaseCommandHandler[UpdateTacticCommand, TacticEntity]):
    """Updates an existing tactic."""

    async def handle(self, command: UpdateTacticCommand) -> TacticEntity:
        """Update an existing tactic."""
        async with self.new_uow() as uow:
            tactic = await uow.tactic_ro_repo.get(command.tactic_id)
            updated = tactic.apply_update(command.update_data, TacticUpdatedEvent)
            uow.add(updated)
            return updated
