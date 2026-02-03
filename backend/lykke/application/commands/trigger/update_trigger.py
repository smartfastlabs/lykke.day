"""Command to update an existing trigger."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.repositories import TriggerRepositoryReadOnlyProtocol
from lykke.domain.entities import TriggerEntity
from lykke.domain.events.trigger_tactic_events import TriggerUpdatedEvent
from lykke.domain.value_objects import TriggerUpdateObject


@dataclass(frozen=True)
class UpdateTriggerCommand(Command):
    """Command to update an existing trigger."""

    trigger_id: UUID
    update_data: TriggerUpdateObject


class UpdateTriggerHandler(BaseCommandHandler[UpdateTriggerCommand, TriggerEntity]):
    """Updates an existing trigger."""

    trigger_ro_repo: TriggerRepositoryReadOnlyProtocol

    async def handle(self, command: UpdateTriggerCommand) -> TriggerEntity:
        """Update an existing trigger."""
        async with self.new_uow() as uow:
            trigger = await self.trigger_ro_repo.get(command.trigger_id)
            updated = trigger.apply_update(command.update_data, TriggerUpdatedEvent)
            uow.add(updated)
            return updated
