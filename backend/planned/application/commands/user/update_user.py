"""Command to update an existing user."""

from dataclasses import asdict, fields, replace
from typing import Any, cast
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import UserEntity


class UpdateUserHandler:
    """Updates an existing user."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def update_user(
        self, user_id: UUID, user_data: UserEntity
    ) -> UserEntity:
        """Update an existing user.

        Args:
            user_id: The user making the request (and the ID of the user to update)
            user_data: The updated user data

        Returns:
            The updated user entity

        Raises:
            NotFoundError: If user not found
        """
        async with self._uow_factory.create(user_id) as uow:
            # Get existing user
            existing = await uow.users.get(user_id)

            # Merge updates - both entities are dataclasses
            # Get all fields from user_data that are not None
            user_data_dict: dict[str, Any] = asdict(user_data)

            # Filter out init=False fields (like _domain_events) - they can't be specified in replace()
            init_false_fields = {f.name for f in fields(existing) if not f.init}
            update_dict = {
                k: v
                for k, v in user_data_dict.items()
                if v is not None and k not in init_false_fields
            }
            updated_any: Any = replace(existing, **update_dict)
            updated = cast(UserEntity, updated_any)

            # Ensure ID matches
            if hasattr(updated, "id"):
                object.__setattr__(updated, "id", user_id)

            user = await uow.users.put(updated)
            await uow.commit()
            return user

