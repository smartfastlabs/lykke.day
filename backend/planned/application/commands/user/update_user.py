"""Command to update an existing user."""

from dataclasses import asdict
from typing import Any
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
            # Convert update_data to dict and filter out None values
            update_data_dict: dict[str, Any] = asdict(update_data)
            update_dict = {k: v for k, v in update_data_dict.items() if v is not None}

            # Apply updates directly to the database
            user = await uow.user_rw_repo.apply_updates(self.user_id, **update_dict)
            await uow.commit()
            return user

