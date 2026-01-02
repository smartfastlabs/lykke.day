"""Reusable handler functions for CRUD operations using CQRS pattern.

All operations are dispatched through the Mediator to ensure consistent
transaction handling and domain event dispatching.
"""

from typing import Any
from uuid import UUID

from planned.application.commands import (
    BulkCreateEntitiesCommand,
    CreateEntityCommand,
    DeleteEntityCommand,
    UpdateEntityCommand,
)
from planned.application.mediator import Mediator
from planned.application.queries import GetEntityQuery, ListEntitiesQuery
from planned.domain.entities import User
from planned.domain.value_objects.query import BaseQuery, PagedQueryResponse

from .config import EntityRouterConfig


async def handle_get(
    entity_id: UUID,
    repository_name: str,
    user: User,
    mediator: Mediator,
) -> Any:
    """Handle GET request for a single entity.

    Args:
        entity_id: UUID of the entity to retrieve
        repository_name: Name of the repository attribute on UoW
        user: Current user
        mediator: Mediator for dispatching queries

    Returns:
        The entity

    Raises:
        NotFoundError: If entity not found
    """
    return await mediator.query(
        GetEntityQuery(
            user_id=user.id,
            entity_id=entity_id,
            repository_name=repository_name,
        )
    )


async def handle_list(
    repository_name: str,
    user: User,
    mediator: Mediator,
    config: EntityRouterConfig,
    query: BaseQuery | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Any] | PagedQueryResponse[Any]:
    """Handle GET request for listing entities with optional pagination.

    Args:
        repository_name: Name of the repository attribute on UoW
        user: Current user
        mediator: Mediator for dispatching queries
        config: Router configuration
        query: Optional search query
        limit: Page size
        offset: Page offset

    Returns:
        List of entities or PagedQueryResponse if pagination enabled
    """
    return await mediator.query(
        ListEntitiesQuery(
            user_id=user.id,
            repository_name=repository_name,
            search_query=query,
            limit=limit,
            offset=offset,
            paginate=config.enable_pagination,
        )
    )


async def handle_create(
    entity_data: Any,
    repository_name: str,
    user: User,
    mediator: Mediator,
) -> Any:
    """Handle POST request for creating an entity.

    Args:
        entity_data: Entity data to create
        repository_name: Name of the repository attribute on UoW
        user: Current user
        mediator: Mediator for dispatching commands

    Returns:
        Created entity
    """
    return await mediator.execute(
        CreateEntityCommand(
            user_id=user.id,
            repository_name=repository_name,
            entity=entity_data,
        )
    )


async def handle_update(
    entity_id: UUID,
    entity_data: Any,
    repository_name: str,
    user: User,
    mediator: Mediator,
) -> Any:
    """Handle PUT/PATCH request for updating an entity.

    Args:
        entity_id: UUID of the entity to update
        entity_data: Updated entity data
        repository_name: Name of the repository attribute on UoW
        user: Current user
        mediator: Mediator for dispatching commands

    Returns:
        Updated entity

    Raises:
        NotFoundError: If entity not found
    """
    return await mediator.execute(
        UpdateEntityCommand(
            user_id=user.id,
            repository_name=repository_name,
            entity_id=entity_id,
            entity_data=entity_data,
        )
    )


async def handle_delete(
    entity_id: UUID,
    repository_name: str,
    user: User,
    mediator: Mediator,
) -> None:
    """Handle DELETE request for an entity.

    Args:
        entity_id: UUID of the entity to delete
        repository_name: Name of the repository attribute on UoW
        user: Current user
        mediator: Mediator for dispatching commands

    Raises:
        NotFoundError: If entity not found
    """
    await mediator.execute(
        DeleteEntityCommand(
            user_id=user.id,
            repository_name=repository_name,
            entity_id=entity_id,
        )
    )


async def handle_bulk_create(
    entities: list[Any],
    repository_name: str,
    user: User,
    mediator: Mediator,
) -> list[Any]:
    """Handle POST request for bulk creating entities.

    Args:
        entities: List of entity objects to create
        repository_name: Name of the repository attribute on UoW
        user: Current user
        mediator: Mediator for dispatching commands

    Returns:
        List of created entities
    """
    if not entities:
        return []

    return await mediator.execute(
        BulkCreateEntitiesCommand(
            user_id=user.id,
            repository_name=repository_name,
            entities=tuple(entities),
        )
    )
