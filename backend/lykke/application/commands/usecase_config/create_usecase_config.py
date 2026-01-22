"""Command to create or update a usecase config."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities.usecase_config import UseCaseConfigEntity
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

    async def handle(
        self, command: CreateUseCaseConfigCommand
    ) -> UseCaseConfigEntity:
        """Create or update a usecase config."""
        async with self.new_uow(command.user_id) as uow:
            # Check if config already exists
            existing = await uow.usecase_config_ro_repo.search(
                UseCaseConfigQuery(usecase=command.usecase)
            )
            if existing:
                # Update existing config
                existing_config = existing[0]
                from datetime import UTC, datetime
                updated_config = UseCaseConfigEntity(
                    id=existing_config.id,
                    user_id=command.user_id,
                    usecase=command.usecase,
                    config=command.config,
                    created_at=existing_config.created_at,
                    updated_at=datetime.now(UTC),
                )
                return uow.add(updated_config)
            else:
                # Create new config
                new_config = UseCaseConfigEntity(
                    user_id=command.user_id,
                    usecase=command.usecase,
                    config=command.config,
                )
                return await uow.create(new_config)
