"""Command to update an existing user."""

from lykke.application.commands.base import BaseCommandHandler
from lykke.domain.entities import UserEntity
from lykke.domain.value_objects import UserUpdateObject


class UpdateUserHandler(BaseCommandHandler):
    """Updates an existing user."""

    async def run(
        self, update_data: UserUpdateObject
    ) -> UserEntity:
        """Update an existing user.

        Args:
            update_data: The update data containing optional fields to update

        Returns:
            The updated user entity

        Raises:
            NotFoundError: If user not found
        """
        async with self.new_uow() as uow:
            # Get the existing user
            user = await uow.user_ro_repo.get(self.user_id)

            # Apply updates using domain method (adds EntityUpdatedEvent)
            from lykke.domain.events.user_events import UserUpdatedEvent

            user = user.apply_update(update_data, UserUpdatedEvent)

            # Add entity to UoW for saving
            uow.add(user)
            return user

