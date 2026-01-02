"""Reusable handler functions for CRUD operations using CQRS pattern."""

from typing import Any
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import User
from planned.domain.value_objects.query import BaseQuery, PagedQueryResponse

from .config import EntityRouterConfig


async def handle_get(
    entity_id: UUID,
    repository_name: str,
    user: User,
    uow_factory: UnitOfWorkFactory,
) -> Any:
    """Handle GET request for a single entity.

    Args:
        entity_id: UUID of the entity to retrieve
        repository_name: Name of the repository attribute on UoW
        user: Current user
        uow_factory: Factory for creating UnitOfWork instances

    Returns:
        The entity

    Raises:
        NotFoundError: If entity not found
    """
    async with uow_factory.create(user.id) as uow:
        repo = getattr(uow, repository_name)
        return await repo.get(entity_id)


async def handle_list(
    repository_name: str,
    user: User,
    uow_factory: UnitOfWorkFactory,
    config: EntityRouterConfig,
    query: BaseQuery | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Any] | PagedQueryResponse[Any]:
    """Handle GET request for listing entities with optional pagination.

    Args:
        repository_name: Name of the repository attribute on UoW
        user: Current user
        uow_factory: Factory for creating UnitOfWork instances
        config: Router configuration
        query: Optional search query
        limit: Page size
        offset: Page offset

    Returns:
        List of entities or PagedQueryResponse if pagination enabled
    """
    async with uow_factory.create(user.id) as uow:
        repo = getattr(uow, repository_name)

        # Get items using query or all()
        if query is not None and hasattr(repo, "search_query"):
            items = await repo.search_query(query)
        elif hasattr(repo, "all"):
            items = await repo.all()
        else:
            raise ValueError(f"Repository {repository_name} does not support list")

        if not config.enable_pagination:
            return items  # type: ignore[no-any-return]

        # Apply pagination
        total = len(items)
        start = offset
        end = start + limit
        paginated_items = items[start:end]

        return PagedQueryResponse(
            items=paginated_items,
            total=total,
            limit=limit,
            offset=offset,
            has_next=end < total,
            has_previous=start > 0,
        )


async def handle_create(
    entity_data: Any,
    repository_name: str,
    user: User,
    uow_factory: UnitOfWorkFactory,
) -> Any:
    """Handle POST request for creating an entity.

    Args:
        entity_data: Entity data to create
        repository_name: Name of the repository attribute on UoW
        user: Current user
        uow_factory: Factory for creating UnitOfWork instances

    Returns:
        Created entity
    """
    async with uow_factory.create(user.id) as uow:
        repo = getattr(uow, repository_name)
        entity = await repo.put(entity_data)
        await uow.commit()
        return entity


async def handle_update(
    entity_id: UUID,
    entity_data: Any,
    repository_name: str,
    user: User,
    uow_factory: UnitOfWorkFactory,
) -> Any:
    """Handle PUT/PATCH request for updating an entity.

    Args:
        entity_id: UUID of the entity to update
        entity_data: Updated entity data
        repository_name: Name of the repository attribute on UoW
        user: Current user
        uow_factory: Factory for creating UnitOfWork instances

    Returns:
        Updated entity

    Raises:
        NotFoundError: If entity not found
    """
    async with uow_factory.create(user.id) as uow:
        repo = getattr(uow, repository_name)

        # Get existing entity
        existing = await repo.get(entity_id)

        # Merge updates
        if hasattr(existing, "model_copy") and hasattr(entity_data, "model_dump"):
            updated = existing.model_copy(
                update=entity_data.model_dump(exclude_unset=True)
            )
        else:
            updated = entity_data

        # Ensure ID matches
        if hasattr(updated, "id"):
            object.__setattr__(updated, "id", entity_id)

        entity = await repo.put(updated)
        await uow.commit()
        return entity


async def handle_delete(
    entity_id: UUID,
    repository_name: str,
    user: User,
    uow_factory: UnitOfWorkFactory,
) -> None:
    """Handle DELETE request for an entity.

    Args:
        entity_id: UUID of the entity to delete
        repository_name: Name of the repository attribute on UoW
        user: Current user
        uow_factory: Factory for creating UnitOfWork instances

    Raises:
        NotFoundError: If entity not found
    """
    async with uow_factory.create(user.id) as uow:
        repo = getattr(uow, repository_name)
        entity = await repo.get(entity_id)
        await repo.delete(entity)
        await uow.commit()


async def handle_bulk_create(
    entities: list[Any],
    repository_name: str,
    user: User,
    uow_factory: UnitOfWorkFactory,
) -> list[Any]:
    """Handle POST request for bulk creating entities.

    Args:
        entities: List of entity objects to create
        repository_name: Name of the repository attribute on UoW
        user: Current user
        uow_factory: Factory for creating UnitOfWork instances

    Returns:
        List of created entities
    """
    if not entities:
        return []

    async with uow_factory.create(user.id) as uow:
        repo = getattr(uow, repository_name)
        created = await repo.insert_many(*entities)
        await uow.commit()
        return created  # type: ignore[no-any-return]
