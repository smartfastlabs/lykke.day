"""Infrastructure implementation of Unit of Work pattern using SQLAlchemy."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date as dt_date, datetime
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar, cast
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from lykke.application.events import send_domain_events
from lykke.application.unit_of_work import (
    ReadOnlyRepositoryFactory,
)
from lykke.core.exceptions import BadRequestError, NotFoundError
from lykke.core.utils.serialization import dataclass_to_json_dict
from lykke.domain.entities import (
    AuditLogEntity,
    AuthTokenEntity,
    BotPersonalityEntity,
    BrainDumpEntity,
    CalendarEntity,
    CalendarEntryEntity,
    CalendarEntrySeriesEntity,
    ConversationEntity,
    DayEntity,
    DayTemplateEntity,
    FactoidEntity,
    MessageEntity,
    PushNotificationEntity,
    PushSubscriptionEntity,
    RoutineEntity,
    TaskDefinitionEntity,
    TaskEntity,
    TimeBlockDefinitionEntity,
    UseCaseConfigEntity,
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
    BrainDumpRepository,
    CalendarEntryRepository,
    CalendarEntrySeriesRepository,
    CalendarRepository,
    ConversationRepository,
    DayRepository,
    DayTemplateRepository,
    FactoidRepository,
    MessageRepository,
    PushNotificationRepository,
    PushSubscriptionRepository,
    RoutineRepository,
    TaskDefinitionRepository,
    TaskRepository,
    TimeBlockDefinitionRepository,
    UseCaseConfigRepository,
    UserRepository,
)

if TYPE_CHECKING:
    from contextvars import Token
    from typing import Self
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncConnection

    from lykke.application.gateways import PubSubGatewayProtocol
    from lykke.application.repositories import (
        AuditLogRepositoryReadOnlyProtocol,
        AuthTokenRepositoryReadOnlyProtocol,
        AuthTokenRepositoryReadWriteProtocol,
        BotPersonalityRepositoryReadOnlyProtocol,
        BotPersonalityRepositoryReadWriteProtocol,
        BrainDumpRepositoryReadOnlyProtocol,
        BrainDumpRepositoryReadWriteProtocol,
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
        PushNotificationRepositoryReadOnlyProtocol,
        PushNotificationRepositoryReadWriteProtocol,
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
        UseCaseConfigRepositoryReadOnlyProtocol,
        UseCaseConfigRepositoryReadWriteProtocol,
        UserRepositoryReadOnlyProtocol,
        UserRepositoryReadWriteProtocol,
    )
    from lykke.application.unit_of_work import (
        ReadOnlyRepositories,
        UnitOfWorkProtocol,
    )
    from lykke.domain import value_objects

# Type variable for entities
_T = TypeVar("_T", bound=BaseEntityObject)

# Sentinel for lazily cached values
_UNSET = object()


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
    brain_dump_ro_repo: BrainDumpRepositoryReadOnlyProtocol
    calendar_entry_ro_repo: CalendarEntryRepositoryReadOnlyProtocol
    calendar_ro_repo: CalendarRepositoryReadOnlyProtocol
    calendar_entry_series_ro_repo: CalendarEntrySeriesRepositoryReadOnlyProtocol
    conversation_ro_repo: ConversationRepositoryReadOnlyProtocol
    day_ro_repo: DayRepositoryReadOnlyProtocol
    day_template_ro_repo: DayTemplateRepositoryReadOnlyProtocol
    factoid_ro_repo: FactoidRepositoryReadOnlyProtocol
    message_ro_repo: MessageRepositoryReadOnlyProtocol
    push_notification_ro_repo: PushNotificationRepositoryReadOnlyProtocol
    push_subscription_ro_repo: PushSubscriptionRepositoryReadOnlyProtocol
    routine_ro_repo: RoutineRepositoryReadOnlyProtocol
    task_definition_ro_repo: TaskDefinitionRepositoryReadOnlyProtocol
    task_ro_repo: TaskRepositoryReadOnlyProtocol
    time_block_definition_ro_repo: TimeBlockDefinitionRepositoryReadOnlyProtocol
    user_ro_repo: UserRepositoryReadOnlyProtocol

    # Entity type to repository attribute name mapping
    # Maps: entity_type -> (ro_repo_attr, rw_repo_attr)
    _ENTITY_REPO_MAP: ClassVar[dict[type, tuple[str, str]]] = {
        AuditLogEntity: (
            "audit_log_ro_repo",
            "audit_log_ro_repo",
        ),  # Read-only, uses same repo
        BotPersonalityEntity: ("bot_personality_ro_repo", "_bot_personality_rw_repo"),
        BrainDumpEntity: ("brain_dump_ro_repo", "_brain_dump_rw_repo"),
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
        PushNotificationEntity: (
            "push_notification_ro_repo",
            "_push_notification_rw_repo",
        ),
        TaskEntity: ("task_ro_repo", "_task_rw_repo"),
        RoutineEntity: ("routine_ro_repo", "_routine_rw_repo"),
        TaskDefinitionEntity: (
            "task_definition_ro_repo",
            "_task_definition_rw_repo",
        ),
        TimeBlockDefinitionEntity: (
            "time_block_definition_ro_repo",
            "_time_block_definition_rw_repo",
        ),
        UserEntity: ("user_ro_repo", "_user_rw_repo"),
        PushSubscriptionEntity: (
            "push_subscription_ro_repo",
            "_push_subscription_rw_repo",
        ),
        AuthTokenEntity: ("auth_token_ro_repo", "_auth_token_rw_repo"),
        UseCaseConfigEntity: ("usecase_config_ro_repo", "_usecase_config_rw_repo"),
    }

    def __init__(self, user_id: UUID, pubsub_gateway: PubSubGatewayProtocol) -> None:
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
        # PubSub gateway for broadcasting domain events
        self._pubsub_gateway = pubsub_gateway
        # Cache user timezone to avoid repeated lookups
        self._user_timezone_cache: str | None | object = _UNSET
        # Internal read-write repositories (not exposed to commands)
        self._auth_token_rw_repo: AuthTokenRepositoryReadWriteProtocol | None = None
        self._bot_personality_rw_repo: (
            BotPersonalityRepositoryReadWriteProtocol | None
        ) = None
        self._brain_dump_rw_repo: BrainDumpRepositoryReadWriteProtocol | None = None
        self._calendar_entry_rw_repo: (
            CalendarEntryRepositoryReadWriteProtocol | None
        ) = None
        self._calendar_entry_series_rw_repo: (
            CalendarEntrySeriesRepositoryReadWriteProtocol | None
        ) = None
        self._calendar_rw_repo: CalendarRepositoryReadWriteProtocol | None = None
        self._conversation_rw_repo: ConversationRepositoryReadWriteProtocol | None = (
            None
        )
        self._day_rw_repo: DayRepositoryReadWriteProtocol | None = None
        self._day_template_rw_repo: DayTemplateRepositoryReadWriteProtocol | None = None
        self._factoid_rw_repo: FactoidRepositoryReadWriteProtocol | None = None
        self._message_rw_repo: MessageRepositoryReadWriteProtocol | None = None
        self._push_notification_rw_repo: (
            PushNotificationRepositoryReadWriteProtocol | None
        ) = None
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

        usecase_config_repo = cast(
            "UseCaseConfigRepositoryReadWriteProtocol",
            UseCaseConfigRepository(user_id=self.user_id),
        )
        self.usecase_config_ro_repo = cast(
            "UseCaseConfigRepositoryReadOnlyProtocol", usecase_config_repo
        )
        self._usecase_config_rw_repo = usecase_config_repo

        # Chatbot-related repositories
        bot_personality_repo = cast(
            "BotPersonalityRepositoryReadWriteProtocol",
            BotPersonalityRepository(user_id=self.user_id),
        )
        self.bot_personality_ro_repo = cast(
            "BotPersonalityRepositoryReadOnlyProtocol", bot_personality_repo
        )
        self._bot_personality_rw_repo = bot_personality_repo

        brain_dump_repo = cast(
            "BrainDumpRepositoryReadWriteProtocol",
            BrainDumpRepository(user_id=self.user_id),
        )
        self.brain_dump_ro_repo = cast(
            "BrainDumpRepositoryReadOnlyProtocol", brain_dump_repo
        )
        self._brain_dump_rw_repo = brain_dump_repo

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
        self._audit_log_rw_repo = audit_log_repo

        push_notification_repo = cast(
            "PushNotificationRepositoryReadWriteProtocol",
            PushNotificationRepository(user_id=self.user_id),
        )
        self.push_notification_ro_repo = cast(
            "PushNotificationRepositoryReadOnlyProtocol", push_notification_repo
        )
        self._push_notification_rw_repo = push_notification_repo

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

    def add(self, entity: _T) -> _T:
        """Add an entity to be tracked for persistence.

        Only entities added via this method will be saved when commit() is called.
        The commit() method will inspect domain events on each added entity to
        determine whether to create, update, or delete it.

        Args:
            entity: The entity to track for persistence.

        Returns:
            The entity that was added.
        """
        self._added_entities.append(entity)
        return entity

    async def create(self, entity: _T) -> _T:
        """Create a new entity.

        This method:
        1. Verifies the entity does not already exist
        2. Calls entity.create() to mark it as newly created
        3. Adds the entity to be tracked for persistence

        Args:
            entity: The entity to create

        Returns:
            The entity that was created.

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
        return self.add(entity)

    async def delete(self, entity: BaseEntityObject) -> None:
        """Delete an existing entity.

        This method:
        1. Verifies the entity exists
        2. Calls entity.delete() to mark it for deletion
        3. Adds the entity to be tracked for persistence

        Args:
            entity: The entity to delete

        Returns:
            None

        Raises:
            NotFoundError: If the entity does not exist
        """
        repo = self._get_read_only_repository_for_entity(entity)
        # Verify entity exists - this will raise NotFoundError if it doesn't
        await repo.get(entity.id)

        # Mark for deletion and add to tracking
        entity.delete()
        self.add(entity)
        return None

    async def commit(self) -> None:
        """Commit the current transaction.

        This will:
        1. Process all added entities (create, update, delete based on domain events)
        2. Collect domain events from all aggregates
        3. Dispatch domain events to handlers (BEFORE commit - handlers can make transactional changes)
        4. Commit the database transaction
        5. Broadcast domain events via PubSub (AFTER commit - external systems see only committed data)
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

        # Dispatch domain events to handlers BEFORE commit
        # This allows handlers to make transactional changes atomically
        await self._dispatch_domain_events(events)

        # Commit the database transaction
        await self._connection.commit()

        # Broadcast ALL domain events via PubSub after successful commit
        # This ensures external systems (WebSocket clients) only see committed data
        await self._broadcast_domain_events_to_redis(events)

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        if self._connection is None:
            raise RuntimeError("Cannot rollback: not in a transaction context")

        if self._is_nested:
            # Nested transactions don't rollback - outer transaction handles it
            return

        await self._connection.rollback()

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

    async def bulk_delete_audit_logs(self, query: value_objects.AuditLogQuery) -> None:
        """Bulk delete audit logs matching the query.

        Note: This is a special operation that bypasses the normal immutability
        of audit logs. Use with caution.
        """
        if self._audit_log_rw_repo is None:
            raise RuntimeError("Audit log repository not initialized")

        await self._audit_log_rw_repo.bulk_delete(query)

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
        the AuditableDomainEvent protocol.

        Note: Events are not collected here - they remain on entities
        to be collected after processing.
        """
        # Process entities and collect audit logs to create
        audit_logs_to_create: list[AuditLogEntity] = []

        user_timezone = await self._get_user_timezone()

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
            any(isinstance(e, EntityUpdatedEvent) for e in events)

            # Create audit logs from audited events (skip for AuditLogEntity itself to avoid loops)
            if not isinstance(entity, AuditLogEntity):
                # Get occurred_at from the first event (all events should have similar timestamps)
                occurred_at = datetime.now(UTC)
                if events:
                    # Try to get timestamp from event if available
                    event_timestamp = getattr(events[0], "occurred_at", None)
                    if event_timestamp is not None:
                        occurred_at = event_timestamp

                if isinstance(entity, CalendarEntryEntity):
                    entity.user_timezone = user_timezone

                # Extract user-facing date from entity
                entity_date = _extract_entity_date(
                    entity, occurred_at, user_timezone=user_timezone
                )

                for event in events:
                    # Check if event implements AuditableDomainEvent protocol
                    if hasattr(event, "to_audit_log") and callable(event.to_audit_log):
                        audit_log = event.to_audit_log(self.user_id)
                        # Override date with entity date to ensure consistency
                        audit_log.date = entity_date
                        audit_log.meta = _attach_entity_snapshot(
                            audit_log.meta, entity_snapshot
                        )
                        audit_logs_to_create.append(audit_log)
                    # For AuditableEntity, also create audit logs for EntityCreated/Updated/Deleted events
                    elif isinstance(entity, AuditableEntity):
                        if isinstance(
                            event,
                            (
                                EntityCreatedEvent,
                                EntityUpdatedEvent,
                                EntityDeletedEvent,
                            ),
                        ):
                            # Infer entity_type from entity class name (e.g., "TaskEntity" -> "task")
                            entity_type = (
                                type(entity).__name__.replace("Entity", "").lower()
                            )
                            # For EntityUpdatedEvent, include update_object in meta
                            meta: dict[str, Any] = {}
                            if isinstance(event, EntityUpdatedEvent):
                                # Convert update_object to JSON-safe dict using utility function
                                # This handles nested dataclasses, UUIDs, lists, etc. recursively
                                update_dict = dataclass_to_json_dict(
                                    event.update_object
                                )
                                if isinstance(update_dict, dict):
                                    meta = update_dict
                                else:
                                    meta = {}

                            audit_log = AuditLogEntity(
                                user_id=self.user_id,
                                activity_type=type(event).__name__,
                                entity_id=entity.id,
                                entity_type=entity_type,
                                date=entity_date,
                                meta=_attach_entity_snapshot(meta, entity_snapshot),
                            )
                            audit_logs_to_create.append(audit_log)

            # Put events back so they can be collected later for dispatching
            for event in events:
                entity._add_event(event)

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
                # Persist immediately
                await audit_log_repo.put(audit_log)

    async def _get_user_timezone(self) -> str | None:
        """Fetch and cache the user's timezone setting."""
        if self._user_timezone_cache is not _UNSET:
            return cast("str | None", self._user_timezone_cache)
        try:
            user = await self.user_ro_repo.get(self.user_id)
            timezone = user.settings.timezone if user.settings else None
        except Exception:
            timezone = None
        self._user_timezone_cache = timezone
        return timezone

    def _collect_domain_events_from_entities(self) -> list[DomainEvent]:
        """Collect domain events from all added entities.

        This collects and clears events from entities after processing.
        The added entities list is cleared after collecting events.

        Returns:
            A list of all domain events collected from entities.
        """
        events: list[DomainEvent] = []
        user_timezone: str | None = None
        if self._user_timezone_cache is not _UNSET:
            user_timezone = cast("str | None", self._user_timezone_cache)

        for entity in self._added_entities:
            entity_events = entity.collect_events()
            if entity_events:
                entity_type = type(entity).__name__.replace("Entity", "").lower()
                for event in entity_events:
                    if isinstance(
                        event,
                        (EntityCreatedEvent, EntityUpdatedEvent, EntityDeletedEvent),
                    ):
                        occurred_at = getattr(event, "occurred_at", datetime.now(UTC))
                        entity_date = _extract_entity_date(
                            entity, occurred_at, user_timezone=user_timezone
                        )
                        event_entity_id = (
                            event.entity_id
                            if event.entity_id is not None
                            else entity.id
                        )
                        event_entity_type = (
                            event.entity_type
                            if event.entity_type is not None
                            else entity_type
                        )
                        event_entity_date = (
                            event.entity_date
                            if event.entity_date is not None
                            else entity_date
                        )
                        event = replace(
                            event,
                            entity_id=event_entity_id,
                            entity_type=event_entity_type,
                            entity_date=event_entity_date,
                        )
                    events.append(event)

        # Clear the added entities list after processing
        self._added_entities.clear()

        return events

    async def _dispatch_domain_events(self, events: list[DomainEvent]) -> None:
        """Dispatch domain events to handlers BEFORE commit.

        Uses blinker signals to dispatch events to registered handlers.
        Handlers execute within the same transaction and can make atomic changes.

        This enables event-driven workflows like:
        - Coordinating multi-entity changes atomically
        - Updating related aggregates in response to domain events
        - Enforcing cross-aggregate invariants
        - Triggering side effects (notifications, logging, etc.)

        IMPORTANT: Handlers run BEFORE commit, so:
        - Handler failures will rollback the entire transaction
        - Handlers should be fast (they block the commit)
        - Handlers can access UnitOfWork to make transactional changes
        - Handlers must not interact with external systems (use post-commit broadcasting for that)

        Args:
            events: List of domain events to dispatch.
        """
        await send_domain_events(events)

    async def _broadcast_domain_events_to_redis(
        self, events: list[DomainEvent]
    ) -> None:
        """Broadcast ALL domain events via Redis PubSub after successful commit.

        Publishes all domain events to user-specific Redis channels for real-time
        updates. WebSocket handlers subscribe to these channels and filter which
        events to forward to clients.

        This broadcasting happens AFTER commit to ensure external systems only
        receive events for successfully committed transactions.

        Args:
            events: List of domain events to broadcast.
        """
        if not events:
            return

        from loguru import logger

        from lykke.core.utils.domain_event_serialization import serialize_domain_event

        for event in events:
            try:
                # Serialize domain event to JSON-compatible dict
                message = serialize_domain_event(event)

                # Publish to user-specific domain-events channel
                # Note: We publish to the user_id from the UnitOfWork context
                await self._pubsub_gateway.publish_to_user_channel(
                    user_id=self.user_id,
                    channel_type="domain-events",
                    message=message,
                )
            except Exception as e:
                # Log error but don't fail the commit
                # PubSub failures shouldn't affect the transaction
                logger.error(
                    f"Failed to broadcast DomainEvent {event.__class__.__name__} via PubSub: {e}"
                )


def _extract_entity_date(
    entity: BaseEntityObject,
    occurred_at: datetime,
    *,
    user_timezone: str | None,
) -> dt_date:
    """Extract the user-facing date from an entity.

    For entities with date fields (like TaskEntity with scheduled_date),
    use that date directly. For entities with datetime fields (like
    CalendarEntryEntity with starts_at), convert to user timezone.
    Otherwise, convert occurred_at to user timezone.

    Args:
        entity: The entity to extract date from
        occurred_at: The datetime when the event occurred (UTC)

    Returns:
        The date in the user's timezone
    """
    # For TaskEntity, use scheduled_date directly (already user-facing date)
    if isinstance(entity, TaskEntity):
        return entity.scheduled_date

    # For CalendarEntryEntity, convert starts_at to user timezone
    if isinstance(entity, CalendarEntryEntity):
        timezone_name = user_timezone or entity.timezone
        try:
            tz = ZoneInfo(timezone_name) if timezone_name else UTC
        except (ZoneInfoNotFoundError, ValueError):
            tz = UTC
        return entity.starts_at.astimezone(tz).date()

    # For other entities, convert occurred_at to user timezone
    try:
        tz = ZoneInfo(user_timezone) if user_timezone else UTC
    except (ZoneInfoNotFoundError, ValueError):
        # Fallback to UTC if timezone is invalid
        return occurred_at.date()
    return occurred_at.astimezone(tz).date()


def _build_entity_snapshot(entity: BaseEntityObject) -> dict[str, Any]:
    """Create a JSON-safe snapshot of an entity for audit logs."""
    serialized = dataclass_to_json_dict(entity)
    if not isinstance(serialized, dict):
        return {}

    snapshot = {
        key: value for key, value in serialized.items() if not key.startswith("_")
    }

    entity_date = getattr(entity, "date", None)
    if isinstance(entity_date, dt_date):
        snapshot["date"] = entity_date.isoformat()

    return snapshot


def _attach_entity_snapshot(
    meta: dict[str, Any] | None, entity_snapshot: dict[str, Any]
) -> dict[str, Any]:
    """Attach entity snapshot data to audit log meta.

    Only attaches if entity_data is not already present in meta.
    This allows custom to_audit_log() implementations to provide their own entity_data.
    """
    if not entity_snapshot:
        return meta or {}

    merged = dict(meta) if meta else {}
    # Only attach if entity_data is not already set
    if "entity_data" not in merged:
        merged["entity_data"] = entity_snapshot
    return merged


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

        usecase_config_repo = cast(
            "UseCaseConfigRepositoryReadOnlyProtocol",
            UseCaseConfigRepository(user_id=self.user_id),
        )
        self.usecase_config_ro_repo = usecase_config_repo

        # Chatbot-related repositories
        bot_personality_repo = cast(
            "BotPersonalityRepositoryReadOnlyProtocol",
            BotPersonalityRepository(user_id=self.user_id),
        )
        self.bot_personality_ro_repo = bot_personality_repo

        brain_dump_repo = cast(
            "BrainDumpRepositoryReadOnlyProtocol",
            BrainDumpRepository(user_id=self.user_id),
        )
        self.brain_dump_ro_repo = brain_dump_repo

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

        push_notification_repo = cast(
            "PushNotificationRepositoryReadOnlyProtocol",
            PushNotificationRepository(user_id=self.user_id),
        )
        self.push_notification_ro_repo = push_notification_repo


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
