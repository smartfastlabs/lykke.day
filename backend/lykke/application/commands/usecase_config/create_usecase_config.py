"""Command to create or update a usecase config."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities.usecase_config import UseCaseConfigEntity
from lykke.domain.events.base import EntityUpdatedEvent
from lykke.domain.value_objects import UseCaseConfigQuery


@dataclass(frozen=True)
class CreateUseCaseConfigCommand(Command):
    """Command to create or update a usecase config."""

    user_id: UUID
    usecase: str
    config: dict[str, Any]


class CreateUseCaseConfigHandler(
    BaseCommandHandler[CreateUseCaseConfigCommand, UseCaseConfigEntity]
):
    """Creates or updates a usecase config."""

    async def handle(self, command: CreateUseCaseConfigCommand) -> UseCaseConfigEntity:
        """Create or update a usecase config."""
        async with self.new_uow(command.user_id) as uow:
            # Check if config already exists
            existing = await uow.usecase_config_ro_repo.search(
                UseCaseConfigQuery(usecase=command.usecase)
            )
            if existing:
                # Update existing config - get the existing entity and modify it
                existing_config = existing[0]
                from datetime import UTC, datetime

                # Clone the existing entity with updated values
                # Note: clone() creates a new instance, so _domain_events will be a new empty list
                updated_config = existing_config.clone(
                    config=command.config,
                    updated_at=datetime.now(UTC),
                )
                # Add EntityUpdatedEvent so UoW knows to update, not insert
                # Use BaseUpdateObject since UseCaseConfig doesn't have a specific update object type
                from lykke.domain.value_objects.update import BaseUpdateObject

                updated_config.add_event(
                    EntityUpdatedEvent(
                        update_object=BaseUpdateObject(),
                        user_id=existing_config.user_id,
                    )
                )
                # Ensure the entity is added to UoW for tracking
                uow.add(updated_config)
                return updated_config
            else:
                # Create new config
                new_config = UseCaseConfigEntity(
                    user_id=command.user_id,
                    usecase=command.usecase,
                    config=command.config,
                )
                return await uow.create(new_config)
