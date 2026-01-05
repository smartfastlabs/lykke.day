from dataclasses import asdict, dataclass, field, replace
from typing import TYPE_CHECKING, Any, Generic, Self, TypeVar
from uuid import UUID, uuid4

from planned.domain.events.base import DomainEvent
from planned.domain.value_objects.update import BaseUpdateObject

if TYPE_CHECKING:
    from planned.domain.events.base import EntityUpdatedEvent

UpdateObjectType = TypeVar("UpdateObjectType", bound=BaseUpdateObject)
UpdateEventType = TypeVar("UpdateEventType", bound="EntityUpdatedEvent[Any, Any]")


@dataclass(kw_only=True)
class BaseObject:
    """Base class for all domain objects."""

    def clone(self, **kwargs: dict[str, Any]) -> Self:
        # Exclude init=False fields from replace() call
        # These fields cannot be specified in replace() but we don't want to include them anyway
        from dataclasses import fields

        init_false_fields = {f.name for f in fields(self) if not f.init}
        filtered_kwargs = {
            k: v for k, v in kwargs.items() if k not in init_false_fields
        }
        return replace(self, **filtered_kwargs)


@dataclass(kw_only=True)
class BaseEntityObject(BaseObject, Generic[UpdateObjectType, UpdateEventType]):
    """Base class for all domain entities (aggregate roots).

    All entities are aggregate roots and can raise domain events
    that are collected and dispatched after transaction commit.

    Type parameters:
        UpdateObjectType: The update object type for this entity (e.g., DayUpdateObject)
        UpdateEventType: The update event type for this entity (e.g., DayUpdatedEvent)

    Subclasses should:
    1. Enforce business invariants
    2. Raise domain events when important things happen
    3. Only expose methods that maintain consistency
    4. Specify UpdateObjectType and UpdateEventType as type parameters
    """

    id: UUID = field(default_factory=uuid4)
    _domain_events: list[DomainEvent] = field(init=False, default_factory=list)

    def _add_event(self, event: DomainEvent) -> None:
        """Add a domain event to be dispatched after commit.

        Args:
            event: The domain event to add.
        """
        self._domain_events.append(event)

    def collect_events(self) -> list[DomainEvent]:
        """Collect and clear all domain events from this aggregate.

        Returns:
            A list of domain events that were raised.
        """
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events

    def has_events(self) -> bool:
        """Check if this aggregate has any pending domain events.

        Returns:
            True if there are pending events, False otherwise.
        """
        return len(self._domain_events) > 0

    def apply_update(
        self,
        update_object: UpdateObjectType,
        update_event_class: type[UpdateEventType],
    ) -> Self:
        """Apply updates from an UpdateObject to this entity and record a domain event.

        This method:
        1. Converts the update object to a dict, filtering out None values
        2. Applies the updates to the entity using clone()
        3. Records a domain event with the update object and new entity value

        Args:
            update_object: The update object containing optional fields to update
            update_event_class: The class of the update event to create

        Returns:
            A new instance of the entity with updates applied
        """
        # Convert update object to dict and filter out None values
        update_dict: dict[str, Any] = asdict(update_object)
        update_dict = {k: v for k, v in update_dict.items() if v is not None}

        # Apply updates using clone (creates a new instance)
        # clone() returns Self, which for BaseEntityObject is the entity type
        # At runtime, this is definitely a BaseEntityObject since self is one
        updated_entity = self.clone(**update_dict)

        # Record domain event with update object and new entity value
        # The event class should accept update_object and entity as parameters
        from planned.domain.events.base import EntityUpdatedEvent

        event = update_event_class(
            update_object=update_object,
            entity=updated_entity,
        )
        # Type checker limitation: clone() returns Self from BaseObject, but we know it's BaseEntityObject
        updated_entity._add_event(event)

        return updated_entity


@dataclass(kw_only=True)
class BaseConfigObject(BaseEntityObject):
    pass
