"""Utility functions for router endpoints."""

from collections.abc import Callable
from typing import Any, TypeVar

from lykke.domain import value_objects
from lykke.presentation.api.schemas import PagedResponseSchema, QuerySchema

# Type variables
QueryT = TypeVar("QueryT", bound=value_objects.BaseQuery)
EntityT = TypeVar("EntityT")
SchemaT = TypeVar("SchemaT")


def build_search_query(
    query_schema: QuerySchema[QueryT],
    query_class: type[QueryT],
    **extra_filters: Any,
) -> QueryT:
    """Build a domain query object from QuerySchema.

    Extracts common pagination and ordering fields, plus any entity-specific
    filters from the query schema.

    Args:
        query_schema: The QuerySchema from the request
        query_class: The domain query class to instantiate
        **extra_filters: Additional filter values to include

    Returns:
        An instance of the query class with all filters applied
    """
    # Get filters from schema or create empty query
    filters = query_schema.filters or query_class()

    # Build the query with pagination, ordering, and common filters
    query_kwargs: dict = {
        "limit": query_schema.limit,
        "offset": query_schema.offset,
        "created_before": getattr(filters, "created_before", None),
        "created_after": getattr(filters, "created_after", None),
        "order_by": getattr(filters, "order_by", None),
        "order_by_desc": getattr(filters, "order_by_desc", None),
    }

    # Add any entity-specific fields from filters
    # Get all fields from the query class that aren't in BaseQuery
    base_query_fields = {
        "limit",
        "offset",
        "order_by",
        "order_by_desc",
        "created_before",
        "created_after",
    }

    if filters:
        # Copy entity-specific fields from filters
        for field_name in query_class.__dataclass_fields__:
            if field_name not in base_query_fields:
                value = getattr(filters, field_name, None)
                if value is not None:
                    query_kwargs[field_name] = value

    # Add any extra filters passed in
    query_kwargs.update(extra_filters)

    return query_class(**query_kwargs)


def create_paged_response(
    result: value_objects.PagedQueryResponse[EntityT],
    mapper_func: Callable[[EntityT], SchemaT],
) -> PagedResponseSchema[SchemaT]:
    """Create a PagedResponseSchema from a PagedQueryResponse.

    Maps the entities in the result to schemas using the provided mapper function.

    Args:
        result: The PagedQueryResponse from the handler
        mapper_func: Function to map entities to schemas

    Returns:
        A PagedResponseSchema with mapped items
    """
    schema_items = [mapper_func(item) for item in result.items]
    return PagedResponseSchema(
        items=schema_items,
        total=result.total,
        limit=result.limit,
        offset=result.offset,
        has_next=result.has_next,
        has_previous=result.has_previous,
    )
