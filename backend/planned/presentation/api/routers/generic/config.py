"""Configuration classes for generic CRUD router factory."""

import inspect
from dataclasses import dataclass
from typing import Callable, get_args, get_origin

from planned.application.repositories import (
    CalendarRepositoryProtocol,
    DayRepositoryProtocol,
    DayTemplateRepositoryProtocol,
    EventRepositoryProtocol,
    MessageRepositoryProtocol,
    PushSubscriptionRepositoryProtocol,
    RoutineRepositoryProtocol,
    TaskDefinitionRepositoryProtocol,
    TaskRepositoryProtocol,
)
from planned.application.repositories.base import (
    BasicCrudRepositoryProtocol,
    CrudRepositoryProtocol,
    DateScopedCrudRepositoryProtocol,
    SimpleDateScopedRepositoryProtocol,
    SimpleReadRepositoryProtocol,
)
from planned.infrastructure.repositories import (
    CalendarRepository,
    DayRepository,
    DayTemplateRepository,
    EventRepository,
    MessageRepository,
    PushSubscriptionRepository,
    RoutineRepository,
    TaskDefinitionRepository,
    TaskRepository,
)

# Registry mapping protocol types to concrete repository classes
PROTOCOL_TO_REPO_CLASS: dict[type, type] = {
    DayTemplateRepositoryProtocol: DayTemplateRepository,
    CalendarRepositoryProtocol: CalendarRepository,
    RoutineRepositoryProtocol: RoutineRepository,
    EventRepositoryProtocol: EventRepository,
    TaskRepositoryProtocol: TaskRepository,
    MessageRepositoryProtocol: MessageRepository,
    PushSubscriptionRepositoryProtocol: PushSubscriptionRepository,
    TaskDefinitionRepositoryProtocol: TaskDefinitionRepository,
    DayRepositoryProtocol: DayRepository,
}


@dataclass
class CRUDOperations:
    """Configuration for which CRUD operations to enable."""

    enable_get: bool = True
    enable_list: bool = True
    enable_create: bool = True
    enable_update: bool = True
    enable_delete: bool = True


def extract_entity_type_from_protocol(protocol_type: type) -> type | None:
    """Extract entity type from repository protocol generic type argument.

    Args:
        protocol_type: The protocol type (e.g., CrudRepositoryProtocol[Entity])

    Returns:
        The entity type if found, None otherwise
    """
    # Try to get args directly first (for generic types like Protocol[Entity])
    args = get_args(protocol_type)
    if args:
        return args[0]  # type: ignore[no-any-return]

    # Check origin for generic types
    origin = get_origin(protocol_type)
    if origin is not None:
        args = get_args(protocol_type)
        if args:
            return args[0]  # type: ignore[no-any-return]

    # Try checking if it's a subclass of base protocols (for non-generic protocol types)
    base_protocols = [
        CrudRepositoryProtocol,
        SimpleReadRepositoryProtocol,
        BasicCrudRepositoryProtocol,
        DateScopedCrudRepositoryProtocol,
        SimpleDateScopedRepositoryProtocol,
    ]

    for base_protocol in base_protocols:
        try:
            # Check if protocol_type itself is a subclass
            if issubclass(protocol_type, base_protocol):
                args = get_args(protocol_type)
                if args:
                    return args[0]  # type: ignore[no-any-return]
        except (TypeError, AttributeError):
            pass

    return None


def extract_query_type_from_repo_class(repo_class: type) -> type | None:
    """Extract QueryClass from concrete repository class.

    Args:
        repo_class: The concrete repository class

    Returns:
        The QueryClass type if found, None otherwise
    """
    if hasattr(repo_class, "QueryClass"):
        return repo_class.QueryClass  # type: ignore[no-any-return]
    return None


@dataclass
class EntityRouterConfig:
    """Configuration for creating a CRUD router for an entity."""

    entity_name: str
    repository_dependency: Callable
    operations: CRUDOperations
    tags: list[str] | None = None
    enable_pagination: bool = True

    def __post_init__(self) -> None:
        """Extract entity type and query type from repository dependency."""
        # Get return type annotation from dependency function
        sig = inspect.signature(self.repository_dependency)
        return_type = sig.return_annotation

        # Extract entity type from protocol generic
        # First try direct extraction
        self.entity_type = extract_entity_type_from_protocol(return_type)

        # Get concrete repository class from registry
        # Check if return_type is directly in the registry
        repo_class = PROTOCOL_TO_REPO_CLASS.get(return_type)

        # If not found, try to match by checking origin (for generic types)
        if repo_class is None:
            origin = get_origin(return_type)
            if origin is not None:
                repo_class = PROTOCOL_TO_REPO_CLASS.get(origin)

        # If still not found, iterate through registry to find match
        if repo_class is None:
            for protocol_type, concrete_class in PROTOCOL_TO_REPO_CLASS.items():
                # Check if return_type matches protocol_type
                if return_type == protocol_type:
                    repo_class = concrete_class
                    break
                # Check if origin matches
                origin = get_origin(return_type)
                if origin == protocol_type:
                    repo_class = concrete_class
                    break

        # Extract query type from concrete repository class
        if repo_class:
            self.query_type = extract_query_type_from_repo_class(repo_class)
        else:
            self.query_type = None

        # Set default tags if not provided
        if self.tags is None:
            self.tags = [self.entity_name]

