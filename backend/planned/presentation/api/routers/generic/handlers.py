"""Reusable handler functions for CRUD operations using CQRS pattern.

All operations are dispatched through the Mediator to ensure consistent
transaction handling and domain event dispatching.

This module provides both:
1. Standalone functions for use in route handlers
2. A generic `EntityCrudOperations` class that provides typed methods
"""

from typing import Generic, TypeVar
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

EntityT = TypeVar("EntityT")


class EntityCrudOperations(Generic[EntityT]):
    """Typed CRUD operations for a specific entity type.

    This class provides properly typed methods for all CRUD operations,
    with the entity type flowing through all return values.

    Example:
        ops: EntityCrudOperations[DayTemplate] = EntityCrudOperations(
            mediator=mediator,
            repository_name="day_templates",
            user=current_user,
        )

        template: DayTemplate = await ops.get(template_id)
        templates: list[DayTemplate] = await ops.list_all()
        created: DayTemplate = await ops.create(new_template)
    """

    def __init__(
        self,
        mediator: Mediator,
        repository_name: str,
        user: User,
    ) -> None:
        self._mediator = mediator
        self._repository_name = repository_name
        self._user = user

    async def get(self, entity_id: UUID) -> EntityT:
        """Get a single entity by ID.

        Args:
            entity_id: UUID of the entity to retrieve

        Returns:
            The entity

        Raises:
            NotFoundError: If entity not found
        """
        return await self._mediator.query(
            GetEntityQuery[EntityT](
                user_id=self._user.id,
                entity_id=entity_id,
                repository_name=self._repository_name,
            )
        )

    async def list_all(
        self,
        query: BaseQuery | None = None,
        limit: int = 50,
        offset: int = 0,
        paginate: bool = True,
    ) -> list[EntityT] | PagedQueryResponse[EntityT]:
        """List entities with optional filtering and pagination.

        Args:
            query: Optional search/filter query
            limit: Maximum number of items to return
            offset: Number of items to skip
            paginate: Whether to return paginated response

        Returns:
            List of entities or PagedQueryResponse
        """
        return await self._mediator.query(
            ListEntitiesQuery[EntityT](
                user_id=self._user.id,
                repository_name=self._repository_name,
                search_query=query,
                limit=limit,
                offset=offset,
                paginate=paginate,
            )
        )

    async def create(self, entity: EntityT) -> EntityT:
        """Create a new entity.

        Args:
            entity: The entity to create

        Returns:
            The created entity
        """
        return await self._mediator.execute(
            CreateEntityCommand[EntityT](
                user_id=self._user.id,
                repository_name=self._repository_name,
                entity=entity,
            )
        )

    async def update(self, entity_id: UUID, entity_data: EntityT) -> EntityT:
        """Update an existing entity.

        Args:
            entity_id: UUID of the entity to update
            entity_data: Updated entity data

        Returns:
            The updated entity

        Raises:
            NotFoundError: If entity not found
        """
        return await self._mediator.execute(
            UpdateEntityCommand[EntityT](
                user_id=self._user.id,
                repository_name=self._repository_name,
                entity_id=entity_id,
                entity_data=entity_data,
            )
        )

    async def delete(self, entity_id: UUID) -> None:
        """Delete an entity.

        Args:
            entity_id: UUID of the entity to delete

        Raises:
            NotFoundError: If entity not found
        """
        await self._mediator.execute(
            DeleteEntityCommand(
                user_id=self._user.id,
                repository_name=self._repository_name,
                entity_id=entity_id,
            )
        )

    async def bulk_create(self, entities: list[EntityT]) -> list[EntityT]:
        """Create multiple entities.

        Args:
            entities: List of entities to create

        Returns:
            List of created entities
        """
        if not entities:
            return []

        return await self._mediator.execute(
            BulkCreateEntitiesCommand[EntityT](
                user_id=self._user.id,
                repository_name=self._repository_name,
                entities=tuple(entities),
            )
        )


# =============================================================================
# Standalone handler functions (for backward compatibility with factory.py)
# =============================================================================


async def handle_get(
    entity_id: UUID,
    repository_name: str,
    user: User,
    mediator: Mediator,
) -> EntityT:
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
) -> list[EntityT] | PagedQueryResponse[EntityT]:
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
    entity_data: EntityT,
    repository_name: str,
    user: User,
    mediator: Mediator,
) -> EntityT:
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
    entity_data: EntityT,
    repository_name: str,
    user: User,
    mediator: Mediator,
) -> EntityT:
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
    entities: list[EntityT],
    repository_name: str,
    user: User,
    mediator: Mediator,
) -> list[EntityT]:
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
