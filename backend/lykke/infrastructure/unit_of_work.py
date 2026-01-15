"""Infrastructure implementation of Unit of Work pattern using SQLAlchemy."""

from __future__ import annotations

from contextvars import Token
from dataclasses import asdict
from datetime import date as dt_date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from lykke.application.events import send_domain_events
from lykke.application.gateways import PubSubGatewayProtocol
from lykke.application.repositories import (
    AuditLogRepositoryReadOnlyProtocol,
    AuthTokenRepositoryReadOnlyProtocol,
    AuthTokenRepositoryReadWriteProtocol,
    BotPersonalityRepositoryReadOnlyProtocol,
    BotPersonalityRepositoryReadWriteProtocol,
    CalendarEntryRepositoryReadOnlyProtocol,
    CalendarEntryRepositoryReadWriteProtocol,
    CalendarEntrySeriesRepositoryReadOnlyProtocol,
    CalendarEntrySeriesRepositoryReadWriteProtocol,
    CalendarRepositoryReadOnlyProtocol,
    CalendarRepositoryReadWriteProtocol,
    ConversationRepositoryReadOnlyProtocol,
    ConversationRepositoryReadWriteProtocol,
    DayRepositoryReadOnlyProtocol,
    DayRepositoryReadWriteProtocol,
    DayTemplateRepositoryReadOnlyProtocol,
    DayTemplateRepositoryReadWriteProtocol,
    FactoidRepositoryReadOnlyProtocol,
    FactoidRepositoryReadWriteProtocol,
    MessageRepositoryReadOnlyProtocol,
    MessageRepositoryReadWriteProtocol,
    PushSubscriptionRepositoryReadOnlyProtocol,
    PushSubscriptionRepositoryReadWriteProtocol,
    RoutineRepositoryReadOnlyProtocol,
    RoutineRepositoryReadWriteProtocol,
    TaskDefinitionRepositoryReadOnlyProtocol,
    TaskDefinitionRepositoryReadWriteProtocol,
    TaskRepositoryReadOnlyProtocol,
    TaskRepositoryReadWriteProtocol,
    TimeBlockDefinitionRepositoryReadOnlyProtocol,
    TimeBlockDefinitionRepositoryReadWriteProtocol,
    UserRepositoryReadOnlyProtocol,
    UserRepositoryReadWriteProtocol,
)
from lykke.application.unit_of_work import (
    ReadOnlyRepositories,
    ReadOnlyRepositoryFactory,
    UnitOfWorkProtocol,
)
from lykke.core.exceptions import BadRequestError, NotFoundError
from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.domain import data_objects, value_objects
from lykke.domain.entities import (
    AuditLogEntity,
    BotPersonalityEntity,
    CalendarEntity,
    CalendarEntryEntity,
    CalendarEntrySeriesEntity,
    ConversationEntity,
    DayEntity,
    DayTemplateEntity,
    FactoidEntity,
    MessageEntity,
    RoutineEntity,
    TaskEntity,
    UserEntity,
)
from lykke.domain.entities.auditable import AuditableEntity
from lykke.domain.entities.base import BaseEntityObject
from lykke.domain.events.base import (
    DomainEvent,
    EntityCreatedEvent,
    EntityDeletedEvent,
    EntityUpdatedEvent,
)
from lykke.infrastructure.database import get_engine
from lykke.infrastructure.database.transaction import (
    get_transaction_connection,
    reset_transaction_connection,
    set_transaction_connection,
)
from lykke.infrastructure.repositories import (
    AuditLogRepository,
    AuthTokenRepository,
    BotPersonalityRepository,
    CalendarEntryRepository,
    CalendarEntrySeriesRepository,
    CalendarRepository,
    ConversationRepository,
    DayRepository,
    DayTemplateRepository,
    FactoidRepository,
    MessageRepository,
    PushSubscriptionRepository,
    RoutineRepository,
    TaskDefinitionRepository,
    TaskRepository,
    TimeBlockDefinitionRepository,
    UserRepository,
)

if TYPE_CHECKING:
    from typing import Self


class SqlAlchemyUnitOfWork:
    """SQLAlchemy implementation of UnitOfWorkProtocol.

    Manages a single database transaction and provides access to read-only
    repositories for querying and an add() method for tracking entities to save.
    All repositories share the same connection.

    Read-write repositories are kept internally for commit() processing only.
    Commands should not access them directly.
    """

    # Read-only repository type annotations (public API for commands)
    audit_log_ro_repo: AuditLogRepositoryReadOnlyProtocol
    auth_token_ro_repo: AuthTokenRepositoryReadOnlyProtocol
    bot_personality_ro_repo: BotPersonalityRepositoryReadOnlyProtocol
    calendar_entry_ro_repo: CalendarEntryRepositoryReadOnlyProtocol
    calendar_ro_repo: CalendarRepositoryReadOnlyProtocol
    calendar_entry_series_ro_repo: CalendarEntrySeriesRepositoryReadOnlyProtocol
    conversation_ro_repo: ConversationRepositoryReadOnlyProtocol
    day_ro_repo: DayRepositoryReadOnlyProtocol
    day_template_ro_repo: DayTemplateRepositoryReadOnlyProtocol
    factoid_ro_repo: FactoidRepositoryReadOnlyProtocol
    message_ro_repo: MessageRepositoryReadOnlyProtocol
    push_subscription_ro_repo: PushSubscriptionRepositoryReadOnlyProtocol
    routine_ro_repo: RoutineRepositoryReadOnlyProtocol
    task_definition_ro_repo: TaskDefinitionRepositoryReadOnlyProtocol
    task_ro_repo: TaskRepositoryReadOnlyProtocol
    time_block_definition_ro_repo: TimeBlockDefinitionRepositoryReadOnlyProtocol
    user_ro_repo: UserRepositoryReadOnlyProtocol

    # Entity type to repository attribute name mapping
    # Maps: entity_type -> (ro_repo_attr, rw_repo_attr)
    _ENTITY_REPO_MAP: dict[type, tuple[str, str]] = {
        AuditLogEntity: ("audit_log_ro_repo", "audit_log_ro_repo"),  # Read-only, uses same repo
        BotPersonalityEntity: ("bot_personality_ro_repo", "_bot_personality_rw_repo"),
        DayEntity: ("day_ro_repo", "_day_rw_repo"),
        DayTemplateEntity: ("day_template_ro_repo", "_day_template_rw_repo"),
        CalendarEntryEntity: ("calendar_entry_ro_repo", "_calendar_entry_rw_repo"),
        CalendarEntrySeriesEntity: (
            "calendar_entry_series_ro_repo",
            "_calendar_entry_series_rw_repo",
        ),
        CalendarEntity: ("calendar_ro_repo", "_calendar_rw_repo"),
        ConversationEntity: ("conversation_ro_repo", "_conversation_rw_repo"),
        FactoidEntity: ("factoid_ro_repo", "_factoid_rw_repo"),
        MessageEntity: ("message_ro_repo", "_message_rw_repo"),
        TaskEntity: ("task_ro_repo", "_task_rw_repo"),
        RoutineEntity: ("routine_ro_repo", "_routine_rw_repo"),
        data_objects.TaskDefinition: (
            "task_definition_ro_repo",
            "_task_definition_rw_repo",
        ),
        data_objects.TimeBlockDefinition: (
            "time_block_definition_ro_repo",
            "_time_block_definition_rw_repo",
        ),
        UserEntity: ("user_ro_repo", "_user_rw_repo"),
        data_objects.PushSubscription: (
            "push_subscription_ro_repo",
            "_push_subscription_rw_repo",
        ),
        data_objects.AuthToken: ("auth_token_ro_repo", "_auth_token_rw_repo"),
    }

    def __init__(
        self, user_id: UUID, pubsub_gateway: PubSubGatewayProtocol
    ) -> None:
        """Initialize the unit of work for a specific user.

        Args:
            user_id: The UUID of the user to scope repositories to.
            pubsub_gateway: PubSub gateway for broadcasting events
        """
        self.user_id = user_id
        self._connection: AsyncConnection | None = None
        self._token: Token[AsyncConnection | None] | None = None
        self._is_nested = False
        # Track entities that need to be saved
        self._added_entities: list[BaseEntityObject] = []
        # Track AuditLog entities for PubSub broadcasting
        self._audit_logs_to_broadcast: list[AuditLogEntity] = []
        # PubSub gateway for broadcasting events
        self._pubsub_gateway = pubsub_gateway
        # Internal read-write repositories (not exposed to commands)
        self._auth_token_rw_repo: AuthTokenRepositoryReadWriteProtocol | None = None
        self._bot_personality_rw_repo: (
            BotPersonalityRepositoryReadWriteProtocol | None
        ) = None
        self._calendar_entry_rw_repo: (
            CalendarEntryRepositoryReadWriteProtocol | None
        ) = None
        self._calendar_entry_series_rw_repo: (
            CalendarEntrySeriesRepositoryReadWriteProtocol | None
        ) = None
        self._calendar_rw_repo: CalendarRepositoryReadWriteProtocol | None = None
        self._conversation_rw_repo: ConversationRepositoryReadWriteProtocol | None = None
        self._day_rw_repo: DayRepositoryReadWriteProtocol | None = None
        self._day_template_rw_repo: DayTemplateRepositoryReadWriteProtocol | None = None
        self._factoid_rw_repo: FactoidRepositoryReadWriteProtocol | None = None
        self._message_rw_repo: MessageRepositoryReadWriteProtocol | None = None
        self._push_subscription_rw_repo: (
            PushSubscriptionRepositoryReadWriteProtocol | None
        ) = None
        self._routine_rw_repo: RoutineRepositoryReadWriteProtocol | None = None
        self._task_definition_rw_repo: (
            TaskDefinitionRepositoryReadWriteProtocol | None
        ) = None
        self._task_rw_repo: TaskRepositoryReadWriteProtocol | None = None
        self._time_block_definition_rw_repo: (
            TimeBlockDefinitionRepositoryReadWriteProtocol | None
        ) = None
        self._user_rw_repo: UserRepositoryReadWriteProtocol | None = None

    async def __aenter__(self) -> Self:
        """Enter the unit of work context.

        Creates a database connection and transaction, then initializes all repositories
        to use that connection.

        Returns:
            The unit of work instance.
        """
        # Check if there's already an active transaction (nested UoW)
        existing_conn = get_transaction_connection()
        if existing_conn is not None:
            self._is_nested = True
            self._connection = existing_conn
        else:
            # Create a new transaction
            engine = get_engine()
            self._connection = await engine.connect()
            await self._connection.begin()

            # Set the connection in the context variable so repositories can use it
            self._token = set_transaction_connection(self._connection)

        # Initialize all repositories with user scoping (where applicable)
        # UserRepository and AuthTokenRepository are not user-scoped
        # Use cast to satisfy type checker - concrete repos implement both protocols
        # We assign the same instance to both ro and rw since they implement both
        user_repo = cast("UserRepositoryReadWriteProtocol", UserRepository())
        self.user_ro_repo = cast("UserRepositoryReadOnlyProtocol", user_repo)
        self._user_rw_repo = user_repo

        auth_token_repo = cast(
            "AuthTokenRepositoryReadWriteProtocol", AuthTokenRepository()
        )
        self.auth_token_ro_repo = cast(
            "AuthTokenRepositoryReadOnlyProtocol", auth_token_repo
        )
        self._auth_token_rw_repo = auth_token_repo

        # All other repositories are user-scoped
        calendar_repo = cast(
            "CalendarRepositoryReadWriteProtocol",
            CalendarRepository(user_id=self.user_id),
        )
        self.calendar_ro_repo = cast(
            "CalendarRepositoryReadOnlyProtocol", calendar_repo
        )
        self._calendar_rw_repo = calendar_repo

        day_repo = cast(
            "DayRepositoryReadWriteProtocol", DayRepository(user_id=self.user_id)
        )
        self.day_ro_repo = cast("DayRepositoryReadOnlyProtocol", day_repo)
        self._day_rw_repo = day_repo

        day_template_repo = cast(
            "DayTemplateRepositoryReadWriteProtocol",
            DayTemplateRepository(user_id=self.user_id),
        )
        self.day_template_ro_repo = cast(
            "DayTemplateRepositoryReadOnlyProtocol", day_template_repo
        )
        self._day_template_rw_repo = day_template_repo

        calendar_entry_repo = cast(
            "CalendarEntryRepositoryReadWriteProtocol",
            CalendarEntryRepository(user_id=self.user_id),
        )
        self.calendar_entry_ro_repo = cast(
            "CalendarEntryRepositoryReadOnlyProtocol", calendar_entry_repo
        )
        self._calendar_entry_rw_repo = calendar_entry_repo

        calendar_entry_series_repo = cast(
            "CalendarEntrySeriesRepositoryReadWriteProtocol",
            CalendarEntrySeriesRepository(user_id=self.user_id),
        )
        self.calendar_entry_series_ro_repo = cast(
            "CalendarEntrySeriesRepositoryReadOnlyProtocol",
            calendar_entry_series_repo,
        )
        self._calendar_entry_series_rw_repo = calendar_entry_series_repo

        push_subscription_repo = cast(
            "PushSubscriptionRepositoryReadWriteProtocol",
            PushSubscriptionRepository(user_id=self.user_id),
        )
        self.push_subscription_ro_repo = cast(
            "PushSubscriptionRepositoryReadOnlyProtocol", push_subscription_repo
        )
        self._push_subscription_rw_repo = push_subscription_repo

        routine_repo = cast(
            "RoutineRepositoryReadWriteProtocol",
            RoutineRepository(user_id=self.user_id),
        )
        self.routine_ro_repo = cast("RoutineRepositoryReadOnlyProtocol", routine_repo)
        self._routine_rw_repo = routine_repo

        task_definition_repo = cast(
            "TaskDefinitionRepositoryReadWriteProtocol",
            TaskDefinitionRepository(user_id=self.user_id),
        )
        self.task_definition_ro_repo = cast(
            "TaskDefinitionRepositoryReadOnlyProtocol", task_definition_repo
        )
        self._task_definition_rw_repo = task_definition_repo

        task_repo = cast(
            "TaskRepositoryReadWriteProtocol",
            TaskRepository(user_id=self.user_id),
        )
        self.task_ro_repo = cast("TaskRepositoryReadOnlyProtocol", task_repo)
        self._task_rw_repo = task_repo

        time_block_definition_repo = cast(
            "TimeBlockDefinitionRepositoryReadWriteProtocol",
            TimeBlockDefinitionRepository(user_id=self.user_id),
        )
        self.time_block_definition_ro_repo = cast(
            "TimeBlockDefinitionRepositoryReadOnlyProtocol", time_block_definition_repo
        )
        self._time_block_definition_rw_repo = time_block_definition_repo

        # Chatbot-related repositories
        bot_personality_repo = cast(
            "BotPersonalityRepositoryReadWriteProtocol",
            BotPersonalityRepository(user_id=self.user_id),
        )
        self.bot_personality_ro_repo = cast(
            "BotPersonalityRepositoryReadOnlyProtocol", bot_personality_repo
        )
        self._bot_personality_rw_repo = bot_personality_repo

        conversation_repo = cast(
            "ConversationRepositoryReadWriteProtocol",
            ConversationRepository(user_id=self.user_id),
        )
        self.conversation_ro_repo = cast(
            "ConversationRepositoryReadOnlyProtocol", conversation_repo
        )
        self._conversation_rw_repo = conversation_repo

        message_repo = cast(
            "MessageRepositoryReadWriteProtocol",
            MessageRepository(user_id=self.user_id),
        )
        self.message_ro_repo = cast("MessageRepositoryReadOnlyProtocol", message_repo)
        self._message_rw_repo = message_repo

        factoid_repo = cast(
            "FactoidRepositoryReadWriteProtocol",
            FactoidRepository(user_id=self.user_id),
        )
        self.factoid_ro_repo = cast("FactoidRepositoryReadOnlyProtocol", factoid_repo)
        self._factoid_rw_repo = factoid_repo

        # AuditLogRepository is read-only (immutable entities)
        # Even though it's read-only in protocol, the implementation has put() for creates
        audit_log_repo = AuditLogRepository(user_id=self.user_id)
        self.audit_log_ro_repo = cast(
            "AuditLogRepositoryReadOnlyProtocol", audit_log_repo
        )

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit the unit of work context.

        For nested transactions, do nothing (let outer transaction handle it).
        For top-level transactions, commit on success or rollback on exception.
        """
        if self._connection is None:
            return

        # If this is a nested transaction, don't commit/rollback
        if self._is_nested:
            return

        try:
            if exc_type is None:
                # Success - commit the transaction
                await self.commit()
            else:
                # Exception occurred - rollback the transaction
                await self.rollback()
        finally:
            # Reset the context variable
            if self._token is not None:
                reset_transaction_connection(self._token)
                self._token = None

            # Close the connection
            if self._connection is not None:
                await self._connection.close()
                self._connection = None

    def add(self, entity: BaseEntityObject) -> None:
        """Add an entity to be tracked for persistence.

        Only entities added via this method will be saved when commit() is called.
        The commit() method will inspect domain events on each added entity to
        determine whether to create, update, or delete it.

        Args:
            entity: The entity to track for persistence.
        """
        self._added_entities.append(entity)

    async def create(self, entity: BaseEntityObject) -> None:
        """Create a new entity.

        This method:
        1. Verifies the entity does not already exist
        2. Calls entity.create() to mark it as newly created
        3. Adds the entity to be tracked for persistence

        Args:
            entity: The entity to create

        Raises:
            BadRequestError: If the entity already exists
        """
        repo = self._get_read_only_repository_for_entity(entity)
        try:
            # Try to get the entity - if it exists, raise an error
            await repo.get(entity.id)
            raise BadRequestError(f"Entity with id {entity.id} already exists")
        except NotFoundError:
            # Entity doesn't exist, which is what we want for create
            pass

        # Mark as newly created and add to tracking
        entity.create()
        self.add(entity)

    async def delete(self, entity: BaseEntityObject) -> None:
        """Delete an existing entity.

        This method:
        1. Verifies the entity exists
        2. Calls entity.delete() to mark it for deletion
        3. Adds the entity to be tracked for persistence

        Args:
            entity: The entity to delete

        Raises:
            NotFoundError: If the entity does not exist
        """
        repo = self._get_read_only_repository_for_entity(entity)
        # Verify entity exists - this will raise NotFoundError if it doesn't
        await repo.get(entity.id)

        # Mark for deletion and add to tracking
        entity.delete()
        self.add(entity)

    async def commit(self) -> None:
        """Commit the current transaction.

        This will:
        1. Process all added entities (create, update, delete based on domain events)
        2. Collect domain events from all aggregates
        3. Commit the database transaction
        4. Dispatch domain events (after successful commit)
        5. Broadcast AuditLog events via PubSub (after successful commit)
        """
        if self._connection is None:
            raise RuntimeError("Cannot commit: not in a transaction context")

        if self._is_nested:
            # Nested transactions don't commit - outer transaction handles it
            return

        # Process all added entities based on their domain events
        await self._process_added_entities()

        # Collect domain events from all processed entities
        events = self._collect_domain_events_from_entities()

        # Commit the database transaction first
        await self._connection.commit()

        # Dispatch domain events after successful commit
        # This ensures events are only dispatched if the transaction succeeded
        await self._dispatch_domain_events(events)

        # Broadcast AuditLog events via PubSub after successful commit
        await self._broadcast_audit_logs()

    async def bulk_delete_calendar_entries(
        self, query: value_objects.CalendarEntryQuery
    ) -> None:
        """Bulk delete calendar entries matching the query."""
        if self._calendar_entry_rw_repo is None:
            raise RuntimeError("Calendar entry repository not initialized")

        await self._calendar_entry_rw_repo.bulk_delete(query)

    async def bulk_delete_tasks(self, query: value_objects.TaskQuery) -> None:
        """Bulk delete tasks matching the query."""
        if self._task_rw_repo is None:
            raise RuntimeError("Task repository not initialized")

        await self._task_rw_repo.bulk_delete(query)

    def _get_repository_for_entity(self, entity: BaseEntityObject) -> Any:
        """Get the appropriate read-write repository for an entity type.

        Args:
            entity: The entity to get a repository for.

        Returns:
            The read-write repository for the entity type.

        Raises:
            ValueError: If no repository is found for the entity type.
        """
        entity_type = type(entity)

        if entity_type not in self._ENTITY_REPO_MAP:
            raise ValueError(f"No repository found for entity type {entity_type}")

        _, rw_attr = self._ENTITY_REPO_MAP[entity_type]
        return getattr(self, rw_attr)

    def _get_read_only_repository_for_entity(self, entity: BaseEntityObject) -> Any:
        """Get the appropriate read-only repository for an entity type.

        Args:
            entity: The entity to get a repository for.

        Returns:
            The read-only repository for the entity type.

        Raises:
            ValueError: If no repository is found for the entity type.
        """
        entity_type = type(entity)

        if entity_type not in self._ENTITY_REPO_MAP:
            raise ValueError(f"No repository found for entity type {entity_type}")

        ro_attr, _ = self._ENTITY_REPO_MAP[entity_type]
        return getattr(self, ro_attr)

    async def _process_added_entities(self) -> None:
        """Process all added entities based on their domain events.

        For each entity:
        - If it has EntityDeletedEvent: delete it
        - If it has EntityCreatedEvent: insert it
        - If it has EntityUpdatedEvent or other events: update it

        Also automatically creates AuditLog entities for events that implement
        the AuditedEvent protocol.

        Note: Events are not collected here - they remain on entities
        to be collected after processing.
        """
        # Process entities and collect audit logs to create
        audit_logs_to_create: list[AuditLogEntity] = []

        for entity in self._added_entities:
            repo = self._get_repository_for_entity(entity)
            entity_snapshot = _build_entity_snapshot(entity)

            # Check events without collecting them (use has_events to peek)
            # We need to check what events exist to determine the operation
            # Since we can't peek at events without collecting, we'll collect
            # and then put them back temporarily
            events = entity.collect_events()
            if not events:
                raise BadRequestError(
                    f"Entity {type(entity).__name__} ({entity.id}) added to UoW without domain events"
                )

            # Check for EntityCreatedEvent, EntityDeletedEvent, EntityUpdatedEvent
            has_created_event = any(isinstance(e, EntityCreatedEvent) for e in events)
            has_deleted_event = any(isinstance(e, EntityDeletedEvent) for e in events)
            has_updated_event = any(isinstance(e, EntityUpdatedEvent) for e in events)

            # Create audit logs from audited events (skip for AuditLogEntity itself to avoid loops)
            if not isinstance(entity, AuditLogEntity):
                for event in events:
                    # Check if event implements AuditedEvent protocol
                    if hasattr(event, "to_audit_log") and callable(event.to_audit_log):
                        audit_log = event.to_audit_log(self.user_id)
                        audit_log.meta = _attach_entity_snapshot(
                            audit_log.meta, entity_snapshot
                        )
                        audit_logs_to_create.append(audit_log)
                    # For AuditableEntity, also create audit logs for EntityCreated/Updated/Deleted events
                    elif isinstance(entity, AuditableEntity):
                        if isinstance(event, (EntityCreatedEvent, EntityUpdatedEvent, EntityDeletedEvent)):
                            # Infer entity_type from entity class name (e.g., "TaskEntity" -> "task")
                            entity_type = type(entity).__name__.replace("Entity", "").lower()
                            # For EntityUpdatedEvent, include update_object in meta
                            meta: dict[str, Any] = {}
                            if isinstance(event, EntityUpdatedEvent):
                                # Convert update_object to dict for meta
                                update_dict = asdict(cast(Any, event.update_object))
                                # Convert non-JSON-serializable values
                                json_safe_meta: dict[str, Any] = {}
                                for key, value in update_dict.items():
                                    if isinstance(value, (datetime, dt_date)):
                                        json_safe_meta[key] = value.isoformat()
                                    elif isinstance(value, UUID):
                                        json_safe_meta[key] = str(value)
                                    elif isinstance(value, Enum):
                                        json_safe_meta[key] = value.value
                                    else:
                                        json_safe_meta[key] = value
                                meta = json_safe_meta
                            
                            audit_log = AuditLogEntity(
                                user_id=self.user_id,
                                activity_type=type(event).__name__,
                                entity_id=entity.id,
                                entity_type=entity_type,
                                meta=_attach_entity_snapshot(meta, entity_snapshot),
                            )
                            audit_logs_to_create.append(audit_log)

            # Put events back so they can be collected later for dispatching
            for event in events:
                entity._add_event(event)

            # Track AuditLog entities being created for PubSub broadcasting
            if isinstance(entity, AuditLogEntity) and has_created_event:
                self._audit_logs_to_broadcast.append(entity)

            if has_deleted_event:
                # Delete the entity
                await repo.delete(entity)
            elif has_created_event:
                # Insert the entity (new entity)
                await repo.put(entity)
            else:
                # Update the entity (existing entity with changes)
                await repo.put(entity)

        # Process auto-created audit logs immediately
        # We need to process them in a separate pass to avoid modifying _added_entities during iteration
        if audit_logs_to_create:
            audit_log_repo = self._get_repository_for_entity(audit_logs_to_create[0])
            for audit_log in audit_logs_to_create:
                audit_log.create()
                # Track for PubSub broadcasting
                self._audit_logs_to_broadcast.append(audit_log)
                # Persist immediately
                await audit_log_repo.put(audit_log)

    def _collect_domain_events_from_entities(self) -> list[DomainEvent]:
        """Collect domain events from all added entities.

        This collects and clears events from entities after processing.
        The added entities list is cleared after collecting events.

        Returns:
            A list of all domain events collected from entities.
        """
        events: list[DomainEvent] = []

        for entity in self._added_entities:
            events.extend(entity.collect_events())

        # Clear the added entities list after processing
        self._added_entities.clear()

        return events

    async def _dispatch_domain_events(self, events: list[DomainEvent]) -> None:
        """Dispatch domain events after successful commit.

        Uses blinker signals to dispatch events to registered handlers.
        This enables event-driven workflows like:
        - Keeping service caches up to date
        - Sending notifications when tasks are completed
        - Triggering calendar syncs when events change
        - Audit logging

        Args:
            events: List of domain events to dispatch.
        """
        await send_domain_events(events)

    async def _broadcast_audit_logs(self) -> None:
        """Broadcast AuditLog entities via PubSub after successful commit.

        Publishes audit log events to user-specific channels for real-time
        monitoring and notifications (e.g., via WebSocket handlers).
        """
        if not self._audit_logs_to_broadcast:
            return

        from lykke.core.utils.audit_log_serialization import serialize_audit_log

        for audit_log in self._audit_logs_to_broadcast:
            try:
                # Convert audit log to JSON-serializable dict using shared utility
                message = serialize_audit_log(audit_log)

                # Publish to user-specific auditlog channel
                await self._pubsub_gateway.publish_to_user_channel(
                    user_id=audit_log.user_id,
                    channel_type="auditlog",
                    message=message,
                )
            except Exception as e:
                # Log error but don't fail the commit
                # PubSub failures shouldn't affect the transaction
                from loguru import logger

                logger.error(
                    f"Failed to broadcast AuditLog {audit_log.id} via PubSub: {e}"
                )

        # Clear the list after broadcasting
        self._audit_logs_to_broadcast.clear()


def _build_entity_snapshot(entity: BaseEntityObject) -> dict[str, Any]:
    """Create a JSON-safe snapshot of an entity for audit logs."""
    serialized = dataclass_to_json_dict(entity)
    if not isinstance(serialized, dict):
        return {}

    snapshot = {key: value for key, value in serialized.items() if not key.startswith("_")}

    entity_date = getattr(entity, "date", None)
    if isinstance(entity_date, dt_date):
        snapshot["date"] = entity_date.isoformat()

    return snapshot


def _attach_entity_snapshot(
    meta: dict[str, Any] | None, entity_snapshot: dict[str, Any]
) -> dict[str, Any]:
    """Attach entity snapshot data to audit log meta."""
    if not entity_snapshot:
        return meta or {}

    merged = dict(meta) if meta else {}
    merged["entity_data"] = entity_snapshot
    return merged

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        if self._connection is None:
            raise RuntimeError("Cannot rollback: not in a transaction context")

        if self._is_nested:
            # Nested transactions don't rollback - outer transaction handles it
            return

        await self._connection.rollback()


class SqlAlchemyUnitOfWorkFactory:
    """Factory for creating SqlAlchemyUnitOfWork instances."""

    def __init__(self, pubsub_gateway: PubSubGatewayProtocol) -> None:
        """Initialize the factory.

        Args:
            pubsub_gateway: PubSub gateway for broadcasting events
        """
        self._pubsub_gateway = pubsub_gateway

    def create(self, user_id: UUID) -> UnitOfWorkProtocol:
        """Create a new UnitOfWork instance for the given user.

        Args:
            user_id: The UUID of the user to scope the unit of work to.

        Returns:
            A new UnitOfWork instance (not yet entered).
        """
        return SqlAlchemyUnitOfWork(
            user_id=user_id, pubsub_gateway=self._pubsub_gateway
        )


class SqlAlchemyReadOnlyRepositories:
    """SQLAlchemy implementation of ReadOnlyRepositories.

    Provides read-only access to repositories without write capabilities.
    Each repository manages its own database connections for read operations.
    """

    def __init__(self, user_id: UUID) -> None:
        """Initialize read-only repositories for a specific user.

        Args:
            user_id: The UUID of the user to scope repositories to.
        """
        self.user_id = user_id

        # Initialize all read-only repositories with user scoping (where applicable)
        # UserRepository and AuthTokenRepository are not user-scoped
        user_repo = cast("UserRepositoryReadOnlyProtocol", UserRepository())
        self.user_ro_repo = user_repo

        auth_token_repo = cast(
            "AuthTokenRepositoryReadOnlyProtocol", AuthTokenRepository()
        )
        self.auth_token_ro_repo = auth_token_repo

        # All other repositories are user-scoped
        calendar_repo = cast(
            "CalendarRepositoryReadOnlyProtocol",
            CalendarRepository(user_id=self.user_id),
        )
        self.calendar_ro_repo = calendar_repo

        day_repo = cast(
            "DayRepositoryReadOnlyProtocol", DayRepository(user_id=self.user_id)
        )
        self.day_ro_repo = day_repo

        day_template_repo = cast(
            "DayTemplateRepositoryReadOnlyProtocol",
            DayTemplateRepository(user_id=self.user_id),
        )
        self.day_template_ro_repo = day_template_repo

        calendar_entry_repo = cast(
            "CalendarEntryRepositoryReadOnlyProtocol",
            CalendarEntryRepository(user_id=self.user_id),
        )
        self.calendar_entry_ro_repo = calendar_entry_repo

        calendar_entry_series_repo = cast(
            "CalendarEntrySeriesRepositoryReadOnlyProtocol",
            CalendarEntrySeriesRepository(user_id=self.user_id),
        )
        self.calendar_entry_series_ro_repo = calendar_entry_series_repo

        push_subscription_repo = cast(
            "PushSubscriptionRepositoryReadOnlyProtocol",
            PushSubscriptionRepository(user_id=self.user_id),
        )
        self.push_subscription_ro_repo = push_subscription_repo

        routine_repo = cast(
            "RoutineRepositoryReadOnlyProtocol",
            RoutineRepository(user_id=self.user_id),
        )
        self.routine_ro_repo = routine_repo

        task_definition_repo = cast(
            "TaskDefinitionRepositoryReadOnlyProtocol",
            TaskDefinitionRepository(user_id=self.user_id),
        )
        self.task_definition_ro_repo = task_definition_repo

        task_repo = cast(
            "TaskRepositoryReadOnlyProtocol", TaskRepository(user_id=self.user_id)
        )
        self.task_ro_repo = task_repo

        time_block_definition_repo = cast(
            "TimeBlockDefinitionRepositoryReadOnlyProtocol",
            TimeBlockDefinitionRepository(user_id=self.user_id),
        )
        self.time_block_definition_ro_repo = time_block_definition_repo

        # Chatbot-related repositories
        bot_personality_repo = cast(
            "BotPersonalityRepositoryReadOnlyProtocol",
            BotPersonalityRepository(user_id=self.user_id),
        )
        self.bot_personality_ro_repo = bot_personality_repo

        conversation_repo = cast(
            "ConversationRepositoryReadOnlyProtocol",
            ConversationRepository(user_id=self.user_id),
        )
        self.conversation_ro_repo = conversation_repo

        message_repo = cast(
            "MessageRepositoryReadOnlyProtocol",
            MessageRepository(user_id=self.user_id),
        )
        self.message_ro_repo = message_repo

        factoid_repo = cast(
            "FactoidRepositoryReadOnlyProtocol",
            FactoidRepository(user_id=self.user_id),
        )
        self.factoid_ro_repo = factoid_repo

        # AuditLogRepository is read-only (immutable entities)
        audit_log_repo = cast(
            "AuditLogRepositoryReadOnlyProtocol",
            AuditLogRepository(user_id=self.user_id),
        )
        self.audit_log_ro_repo = audit_log_repo


class SqlAlchemyReadOnlyRepositoryFactory:
    """Factory for creating SqlAlchemyReadOnlyRepositories instances."""

    def create(self, user_id: UUID) -> ReadOnlyRepositories:
        """Create read-only repositories for the given user.

        Args:
            user_id: The UUID of the user to scope the repositories to.

        Returns:
            Read-only repositories scoped to the user.
        """
        return SqlAlchemyReadOnlyRepositories(user_id=user_id)
