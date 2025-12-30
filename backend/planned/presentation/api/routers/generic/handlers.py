"""Reusable handler functions for CRUD operations."""

from typing import Protocol, TypeVar
from uuid import UUID

from planned.domain.entities import User
from planned.domain.entities.base import BaseEntityObject
from planned.domain.value_objects.query import (
    BaseQuery,
    PagedQueryRequest,
    PagedQueryResponse,
)

from .config import EntityRouterConfig

EntityType = TypeVar("EntityType", bound=BaseEntityObject)
QueryType = TypeVar("QueryType", bound=BaseQuery)


class RepositoryProtocol(Protocol[EntityType]):
    """Protocol for repository methods used by handlers."""

    async def get(self, key: UUID) -> EntityType:
        """Get an object by key."""
        ...

    async def put(self, obj: EntityType) -> EntityType:
        """Save or update an object."""
        ...

    async def all(self) -> list[EntityType]:
        """Get all objects."""
        ...

    async def delete(self, key: UUID | EntityType) -> None:
        """Delete an object by key or by object."""
        ...


class SearchableRepositoryProtocol(Protocol[EntityType]):
    """Protocol for repositories that support search_query."""

    async def get(self, key: UUID) -> EntityType:
        """Get an object by key."""
        ...

    async def put(self, obj: EntityType) -> EntityType:
        """Save or update an object."""
        ...

    async def search_query(self, query: BaseQuery) -> list[EntityType]:
        """Search for objects based on a query object."""
        ...

    async def delete(self, obj: EntityType) -> None:
        """Delete an object."""
        ...


async def handle_get(
    entity_id: UUID,
    repo: RepositoryProtocol[EntityType],
    _user: User,
) -> EntityType:
    """Handle GET request for a single entity.

    Args:
        entity_id: UUID of the entity to retrieve
        repo: Repository instance
        user: Current user

    Returns:
        The entity

    Raises:
        NotFoundError: If entity not found
    """
    entity = await repo.get(entity_id)
    return entity


async def handle_list(
    paged_query: PagedQueryRequest[QueryType],
    config: EntityRouterConfig,
    repo: RepositoryProtocol[EntityType] | SearchableRepositoryProtocol[EntityType],
    _user: User,
) -> list[EntityType] | PagedQueryResponse[EntityType]:
    """Handle GET request for listing entities with optional pagination.

    Args:
        paged_query: Pagination query parameters
        config: Router configuration
        repo: Repository instance
        user: Current user

    Returns:
        List of entities or PagedQueryResponse if pagination enabled
    """
    query_type = config.query_type
    enable_pagination = config.enable_pagination

    # Check if we have a query object (from paged_query.query)
    query = getattr(paged_query, "query", None)

    if query is not None and query_type is not None and hasattr(repo, "search_query"):
        # Use the query object that was passed in (already has limit/offset from BaseQuery)
        items = await repo.search_query(query)

        if enable_pagination:
            # Get total count by querying again without limit/offset
            # Create a copy of query without limit/offset
            query_dict = (
                query.model_dump() if hasattr(query, "model_dump") else query.dict()
            )
            count_query_dict = {
                k: v for k, v in query_dict.items() if k not in ("limit", "offset")
            }
            count_query = query_type(**count_query_dict)
            all_items = await repo.search_query(count_query)
            total = len(all_items)

            # Use limit/offset from query object (they're already there from BaseQuery)
            query_limit = query.limit or paged_query.limit
            query_offset = query.offset or paged_query.offset

            return PagedQueryResponse(
                items=items,
                total=total,
                limit=query_limit,
                offset=query_offset,
                has_next=(query_offset + query_limit) < total,
                has_previous=query_offset > 0,
            )
        return items
    # Fall through to all() if search_query not available

    # Use all() method (for SimpleReadRepositoryProtocol or CrudRepositoryProtocol)
    if hasattr(repo, "all"):
        all_items = await repo.all()

        if enable_pagination:
            total = len(all_items)
            # Apply pagination manually
            start = paged_query.offset
            end = start + paged_query.limit
            items = all_items[start:end]

            return PagedQueryResponse(
                items=items,
                total=total,
                limit=paged_query.limit,
                offset=paged_query.offset,
                has_next=end < total,
                has_previous=start > 0,
            )
        return all_items

    raise ValueError(f"Repository {type(repo)} does not support list operation")


async def handle_create(
    entity_data: EntityType,
    repo: RepositoryProtocol[EntityType],
    _user: User,
) -> EntityType:
    """Handle POST request for creating an entity.

    Args:
        entity_data: Entity data to create (UUID will be generated if not provided)
        repo: Repository instance
        user: Current user

    Returns:
        Created entity
    """
    entity = await repo.put(entity_data)
    return entity


async def handle_update(
    entity_id: UUID,
    entity_data: EntityType,
    repo: RepositoryProtocol[EntityType],
    _user: User,
) -> EntityType:
    """Handle PUT/PATCH request for updating an entity.

    Args:
        entity_id: UUID of the entity to update
        entity_data: Updated entity data (may be partial)
        repo: Repository instance
        user: Current user

    Returns:
        Updated entity

    Raises:
        NotFoundError: If entity not found
    """
    # Get existing entity first
    existing = await repo.get(entity_id)

    # Merge updates into existing entity
    # If entity_data has a model_copy or update method, use it
    if hasattr(existing, "model_copy"):
        updated = existing.model_copy(update=entity_data.model_dump(exclude_unset=True))
    elif hasattr(existing, "dict"):
        existing_dict = existing.dict()
        update_dict = (
            entity_data.dict(exclude_unset=True)
            if hasattr(entity_data, "dict")
            else entity_data
        )
        existing_dict.update(update_dict)
        updated = type(existing)(**existing_dict)
    else:
        # Fallback: assume entity_data is already the full entity
        updated = entity_data

    # Ensure UUID matches the path parameter
    if hasattr(updated, "uuid"):
        updated.uuid = entity_id

    entity = await repo.put(updated)
    return entity


async def handle_delete(
    entity_id: UUID,
    repo: RepositoryProtocol[EntityType],
    _user: User,
) -> None:
    """Handle DELETE request for an entity.

    Args:
        entity_id: UUID of the entity to delete
        repo: Repository instance
        user: Current user

    Raises:
        NotFoundError: If entity not found
    """
    # Get entity first to verify it exists
    entity = await repo.get(entity_id)
    await repo.delete(entity)
