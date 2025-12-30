"""Factory function for creating CRUD routers."""

from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from planned.domain.entities import User
from planned.domain.entities.base import BaseEntityObject
from planned.domain.value_objects.query import BaseQuery, PagedQueryRequest
from planned.presentation.api.routers.dependencies.user import get_current_user

from .config import EntityRouterConfig
from .handlers import (
    handle_create,
    handle_delete,
    handle_get,
    handle_list,
    handle_update,
)


def create_crud_router(config: EntityRouterConfig) -> APIRouter:
    """Create a CRUD router for an entity based on configuration.

    Args:
        config: Configuration specifying entity type, repository, and operations

    Returns:
        FastAPI router with CRUD endpoints
    """
    router = APIRouter()

    entity_type = config.entity_type
    repo_dependency = config.repository_dependency
    operations = config.operations

    if entity_type is None:
        raise ValueError(
            f"Could not extract entity type from repository dependency {repo_dependency}"
        )

    # GET /{uuid} - Get single entity
    if operations.enable_get:

        @router.get("/{uuid}")
        async def get_entity(
            uuid: UUID,
            repo: Annotated[Any, Depends(repo_dependency)],
            user: Annotated[User, Depends(get_current_user)],
        ) -> entity_type:  # type: ignore
            return await handle_get(uuid, repo, user)

    # GET / - List entities
    if operations.enable_list:
        query_type = config.query_type

        if query_type is not None and config.enable_pagination:
            # Use query_type directly with FastAPI query parameter parsing
            # BaseQuery already has limit/offset fields

            @router.get("/")
            async def list_entities_with_query_paged(
                query: Annotated[query_type, Query()],  # type: ignore[valid-type]
                repo: Annotated[Any, Depends(repo_dependency)],
                user: Annotated[User, Depends(get_current_user)],
            ) -> Any:
                # Create PagedQueryRequest wrapper for handler
                # query is a BaseQuery instance, so it has limit and offset
                query_limit = getattr(query, "limit", None) or 50
                query_offset = getattr(query, "offset", None) or 0
                paged_query: PagedQueryRequest[Any] = PagedQueryRequest(
                    limit=query_limit,
                    offset=query_offset,
                )
                paged_query.query = query
                return await handle_list(paged_query, config, repo, user)

        elif query_type is not None and not config.enable_pagination:
            # Use query_type but return plain list

            @router.get("/")
            async def list_entities_with_query(
                query: Annotated[query_type, Query()],  # type: ignore[valid-type]
                repo: Annotated[Any, Depends(repo_dependency)],
                user: Annotated[User, Depends(get_current_user)],
            ) -> Any:
                # query is a BaseQuery instance, so it has limit and offset
                query_limit = getattr(query, "limit", None) or 50
                query_offset = getattr(query, "offset", None) or 0
                paged_query: PagedQueryRequest[Any] = PagedQueryRequest(
                    limit=query_limit,
                    offset=query_offset,
                )
                paged_query.query = query
                result = await handle_list(paged_query, config, repo, user)
                if isinstance(result, list):
                    return result
                # result is PagedQueryResponse
                return result.items

        else:
            # No query_type, use simple pagination params
            if config.enable_pagination:

                @router.get("/")
                async def list_entities_paged(
                    repo: Annotated[Any, Depends(repo_dependency)],
                    user: Annotated[User, Depends(get_current_user)],
                    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
                    offset: Annotated[int, Query(ge=0)] = 0,
                ) -> Any:
                    paged_query: PagedQueryRequest[Any] = PagedQueryRequest(
                        limit=limit, offset=offset
                    )
                    return await handle_list(paged_query, config, repo, user)

            else:

                @router.get("/")
                async def list_entities_simple(
                    repo: Annotated[Any, Depends(repo_dependency)],
                    user: Annotated[User, Depends(get_current_user)],
                ) -> Any:
                    paged_query: PagedQueryRequest[Any] = PagedQueryRequest(
                        limit=50, offset=0
                    )
                    result = await handle_list(paged_query, config, repo, user)
                    if isinstance(result, list):
                        return result
                    # result is PagedQueryResponse
                    return result.items

    # PUT /{uuid} - Create or update entity
    if operations.enable_create or operations.enable_update:

        @router.put("/{uuid}")
        async def create_or_update_entity(
            uuid: UUID,
            entity_data: entity_type,  # type: ignore
            repo: Annotated[Any, Depends(repo_dependency)],
            user: Annotated[User, Depends(get_current_user)],
        ) -> entity_type:  # type: ignore
            # Ensure UUID matches
            if hasattr(entity_data, "uuid"):
                # entity_data is a BaseEntityObject, which has uuid
                entity_data.uuid = uuid
            return await handle_create(entity_data, repo, user)

    # DELETE /{uuid} - Delete entity
    if operations.enable_delete:

        @router.delete("/{uuid}")
        async def delete_entity(
            uuid: UUID,
            repo: Annotated[Any, Depends(repo_dependency)],
            user: Annotated[User, Depends(get_current_user)],
        ) -> None:
            await handle_delete(uuid, repo, user)

    return router
