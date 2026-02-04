"""Command to update tactics linked to a trigger."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.repositories import (
    TacticRepositoryReadOnlyProtocol,
    TriggerRepositoryReadOnlyProtocol,
)
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import TacticEntity


@dataclass(frozen=True)
class UpdateTriggerTacticsCommand(Command):
    """Command to replace tactics linked to a trigger."""

    trigger_id: UUID
    tactic_ids: list[UUID]


class UpdateTriggerTacticsHandler(
    BaseCommandHandler[UpdateTriggerTacticsCommand, list[TacticEntity]]
):
    """Replaces tactics linked to a trigger."""

    tactic_ro_repo: TacticRepositoryReadOnlyProtocol
    trigger_ro_repo: TriggerRepositoryReadOnlyProtocol

    async def handle(
        self, command: UpdateTriggerTacticsCommand
    ) -> list[TacticEntity]:
        """Replace all tactics linked to a trigger."""
        async with self.new_uow() as uow:
            trigger = await self.trigger_ro_repo.get(command.trigger_id)
            unique_ids = list(dict.fromkeys(command.tactic_ids))

            if unique_ids:
                tactics = await self.tactic_ro_repo.search(
                    value_objects.TacticQuery(ids=unique_ids)
                )
                if len(tactics) != len(unique_ids):
                    raise NotFoundError("One or more tactics not found")

            await uow.set_trigger_tactics(trigger.id, unique_ids)
            return await self.trigger_ro_repo.list_tactics_for_trigger(
                trigger.id
            )
