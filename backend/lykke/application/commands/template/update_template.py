"""Command to update an existing template override."""

from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.events.base import EntityUpdatedEvent
from lykke.domain.value_objects import TemplateUpdateObject
from lykke.domain.entities.template import TemplateEntity


@dataclass(frozen=True)
class UpdateTemplateCommand(Command):
    """Command to update an existing template override."""

    template_id: UUID
    update_data: TemplateUpdateObject


class UpdateTemplateHandler(BaseCommandHandler[UpdateTemplateCommand, TemplateEntity]):
    """Updates an existing template override."""

    async def handle(self, command: UpdateTemplateCommand) -> TemplateEntity:
        """Update an existing template override."""
        async with self.new_uow() as uow:
            template = await uow.template_ro_repo.get(command.template_id)
            template = template.apply_update(command.update_data, EntityUpdatedEvent)
            return uow.add(template)
