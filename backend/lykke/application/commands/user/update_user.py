"""Command to update an existing user."""

from dataclasses import dataclass

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.core.utils.phone_numbers import normalize_phone_number
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
            user = await uow.user_ro_repo.get(self.user.id)

            update_data = command.update_data
            if update_data.phone_number is not None:
                update_data = UserUpdateObject(
                    email=update_data.email,
                    phone_number=normalize_phone_number(update_data.phone_number),
                    hashed_password=update_data.hashed_password,
                    is_active=update_data.is_active,
                    is_superuser=update_data.is_superuser,
                    is_verified=update_data.is_verified,
                    settings_update=update_data.settings_update,
                    status=update_data.status,
                )

            # Apply updates using domain method (adds EntityUpdatedEvent)
            user = user.apply_update(update_data, UserUpdatedEvent)

            # Add entity to UoW for saving
            return uow.add(user)
