"""Configuration classes for generic CRUD router factory."""

from dataclasses import dataclass, field

from planned.domain import value_objects


@dataclass
class CRUDOperations:
    """Configuration for which CRUD operations to enable."""

    enable_get: bool = True
    enable_list: bool = True
    enable_create: bool = True
    enable_update: bool = True
    enable_delete: bool = True
    enable_bulk_create: bool = False


@dataclass
class EntityRouterConfig:
    """Configuration for creating a CRUD router for an entity."""

    entity_name: str
    repo_class: type
    repository_name: (
        str  # Name of the repository attribute on UoW (e.g., "days", "tasks")
    )
    operations: CRUDOperations
    tags: list[str] | None = None
    enable_pagination: bool = True
    entity_type: type | None = field(init=False, default=None)
    query_type: type[value_objects.BaseQuery] | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        """Extract entity type and query type from repository class."""
        # Get entity type from repository class Object attribute
        if hasattr(self.repo_class, "Object"):
            self.entity_type = self.repo_class.Object
        else:
            self.entity_type = None

        # Get query type from repository class QueryClass attribute
        if hasattr(self.repo_class, "QueryClass"):
            self.query_type = self.repo_class.QueryClass
        else:
            self.query_type = None

        # Set default tags if not provided
        if self.tags is None:
            self.tags = [self.entity_name]
