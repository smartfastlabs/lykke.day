"""Generic command to update an existing entity."""

from dataclasses import asdict, fields, is_dataclass, replace
from typing import Any, TypeVar, cast
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory

EntityT = TypeVar("EntityT")


class UpdateEntityHandler:
    """Updates an existing entity."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def update_entity(
        self, user_id: UUID, repository_name: str, entity_id: UUID, entity_data: EntityT
    ) -> EntityT:
        """Update an existing entity.

        Args:
            user_id: The user making the request
            repository_name: Name of the repository on UoW (e.g., "days", "tasks")
            entity_id: The ID of the entity to update
            entity_data: The updated entity data

        Returns:
            The updated entity

        Raises:
            NotFoundError: If entity not found
        """
        async with self._uow_factory.create(user_id) as uow:
            repo = getattr(uow, repository_name)

            # Get existing entity
            existing: EntityT = await repo.get(entity_id)

            # Merge updates
            if is_dataclass(existing) and is_dataclass(entity_data):
                # Both are dataclasses - use replace to merge updates
                # Get all fields from entity_data that are not None
                entity_data_dict: dict[str, Any] = asdict(entity_data)  # type: ignore[arg-type]
                
                # Filter out init=False fields (like _domain_events) - they can't be specified in replace()
                init_false_fields = {f.name for f in fields(existing) if not f.init}
                update_dict = {
                    k: v for k, v in entity_data_dict.items() 
                    if v is not None and k not in init_false_fields
                }
                updated_any: Any = replace(existing, **update_dict)  # type: ignore[type-var]
                updated = cast(EntityT, updated_any)
            else:
                updated = entity_data

            # Ensure ID matches
            if hasattr(updated, "id"):
                object.__setattr__(updated, "id", entity_id)

            entity: EntityT = await repo.put(updated)
            await uow.commit()
            return entity
