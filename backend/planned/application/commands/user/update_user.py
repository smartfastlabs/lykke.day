"""Command to update an existing user."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import UserEntity
from planned.domain.value_objects import UserUpdateObject


class UpdateUserHandler:
    """Updates an existing user."""

    def __init__(self, uow_factory: UnitOfWorkFactory, user_id: UUID) -> None:
        self._uow_factory = uow_factory
        self.user_id = user_id

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
        async with self._uow_factory.create(self.user_id) as uow:
            # Get the existing user
            user = await uow.user_ro_repo.get(self.user_id)

            # Apply updates using domain method (adds EntityUpdatedEvent)
            from planned.domain.events.user_events import UserUpdatedEvent

            user = user.apply_update(update_data, UserUpdatedEvent)

            # Add entity to UoW for saving
            uow.add(user)
            return user

