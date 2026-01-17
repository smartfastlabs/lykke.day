"""Command to update an existing user."""

from dataclasses import dataclass

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.domain.entities import UserEntity
from lykke.domain.events.user_events import UserUpdatedEvent
from lykke.domain.value_objects import UserUpdateObject


@dataclass(frozen=True)
class UpdateUserCommand(Command):
    """Command to update an existing user."""

    update_data: UserUpdateObject


class UpdateUserHandler(BaseCommandHandler[UpdateUserCommand, UserEntity]):
    """Updates an existing user."""

    async def handle(self, command: UpdateUserCommand) -> UserEntity:
        """Update an existing user.

        Args:
            command: The command containing the update data

        Returns:
            The updated user entity

        Raises:
            NotFoundError: If user not found
        """
        async with self.new_uow() as uow:
            # Get the existing user
            user = await uow.user_ro_repo.get(self.user_id)

            # Apply updates using domain method (adds EntityUpdatedEvent)
            user = user.apply_update(command.update_data, UserUpdatedEvent)

            # Add entity to UoW for saving
            uow.add(user)
            return user

