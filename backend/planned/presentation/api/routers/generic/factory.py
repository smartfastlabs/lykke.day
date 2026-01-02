"""Factory function for creating CRUD routers using CQRS pattern."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from planned.application.mediator import Mediator
from planned.domain.entities import User
from planned.presentation.api.routers.dependencies.services import get_mediator
from planned.presentation.api.routers.dependencies.user import get_current_user

from .config import EntityRouterConfig
from .handlers import (
    handle_bulk_create,
    handle_create,
    handle_delete,
    handle_get,
    handle_list,
    handle_update,
)


def create_crud_router(config: EntityRouterConfig) -> APIRouter:
    """Create a CRUD router for an entity based on configuration.

    All operations are dispatched through the Mediator for proper
    CQRS handling, transaction management, and domain event dispatching.

    Args:
        config: Configuration specifying entity type, repository, and operations

    Returns:
        FastAPI router with CRUD endpoints
    """
    router = APIRouter()

    entity_type = config.entity_type
    repository_name = config.repository_name
    operations = config.operations

    if entity_type is None:
        raise ValueError(
            f"Could not extract entity type from repository class {config.repo_class}"
        )

    # GET /{uuid} - Get single entity
    if operations.enable_get:

        @router.get("/{uuid}")
        async def get_entity(
            uuid: UUID,
            user: Annotated[User, Depends(get_current_user)],
            mediator: Annotated[Mediator, Depends(get_mediator)],
        ) -> entity_type:  # type: ignore
            return await handle_get(  # type: ignore[no-any-return]
                uuid, repository_name, user, mediator
            )

    # GET / - List entities
    if operations.enable_list:
        query_type = config.query_type

        if query_type is not None:
            # Use query_type for filtering

            @router.get("/")
            async def list_entities_with_query(
                query: Annotated[query_type, Query()],  # type: ignore[valid-type]
                user: Annotated[User, Depends(get_current_user)],
                mediator: Annotated[Mediator, Depends(get_mediator)],
            ) -> Any:
                query_limit = getattr(query, "limit", None) or 50
                query_offset = getattr(query, "offset", None) or 0
                return await handle_list(
                    repository_name,
                    user,
                    mediator,
                    config,
                    query=query,
                    limit=query_limit,
                    offset=query_offset,
                )

        else:
            # No query_type, use simple pagination params

            @router.get("/")
            async def list_entities(
                user: Annotated[User, Depends(get_current_user)],
                mediator: Annotated[Mediator, Depends(get_mediator)],
                limit: Annotated[int, Query(ge=1, le=1000)] = 50,
                offset: Annotated[int, Query(ge=0)] = 0,
            ) -> Any:
                return await handle_list(
                    repository_name,
                    user,
                    mediator,
                    config,
                    limit=limit,
                    offset=offset,
                )

    # POST / - Create entity
    if operations.enable_create:

        @router.post("/")
        async def create_entity(
            entity_data: entity_type,  # type: ignore
            user: Annotated[User, Depends(get_current_user)],
            mediator: Annotated[Mediator, Depends(get_mediator)],
        ) -> entity_type:  # type: ignore
            return await handle_create(  # type: ignore[no-any-return]
                entity_data, repository_name, user, mediator
            )

    # POST /bulk - Bulk create entities
    if operations.enable_bulk_create:

        @router.post("/bulk")
        async def bulk_create_entities(
            entities_data: list[dict],
            user: Annotated[User, Depends(get_current_user)],
            mediator: Annotated[Mediator, Depends(get_mediator)],
        ) -> list[entity_type]:  # type: ignore
            # Convert dictionaries to entity objects, setting user_id
            entities = []
            for data in entities_data:
                if "user_id" not in data:
                    data["user_id"] = user.id
                entity = entity_type.model_validate(data)  # type: ignore
                entities.append(entity)
            return await handle_bulk_create(entities, repository_name, user, mediator)

    # PUT /{uuid} - Update entity
    if operations.enable_update:

        @router.put("/{uuid}")
        async def update_entity(
            uuid: UUID,
            entity_data: entity_type,  # type: ignore
            user: Annotated[User, Depends(get_current_user)],
            mediator: Annotated[Mediator, Depends(get_mediator)],
        ) -> entity_type:  # type: ignore
            return await handle_update(  # type: ignore[no-any-return]
                uuid, entity_data, repository_name, user, mediator
            )

    # DELETE /{uuid} - Delete entity
    if operations.enable_delete:

        @router.delete("/{uuid}")
        async def delete_entity(
            uuid: UUID,
            user: Annotated[User, Depends(get_current_user)],
            mediator: Annotated[Mediator, Depends(get_mediator)],
        ) -> None:
            await handle_delete(uuid, repository_name, user, mediator)

    return router
