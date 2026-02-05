"""Repository factories for handlers (non-transactional).

These factories provide read-only and read-write repository collections that manage
their own connections (i.e., they are not bound to a Unit of Work transaction).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from lykke.domain.entities import UserEntity
from lykke.infrastructure.repositories import (
    AuditLogRepository,
    AuthTokenRepository,
    BotPersonalityRepository,
    BrainDumpRepository,
    CalendarEntryRepository,
    CalendarEntrySeriesRepository,
    CalendarRepository,
    DayRepository,
    DayTemplateRepository,
    FactoidRepository,
    MessageRepository,
    PushNotificationRepository,
    PushSubscriptionRepository,
    RoutineDefinitionRepository,
    RoutineRepository,
    TacticRepository,
    TaskDefinitionRepository,
    TaskRepository,
    TimeBlockDefinitionRepository,
    TriggerRepository,
    UseCaseConfigRepository,
)

if TYPE_CHECKING:
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
        RoutineDefinitionRepositoryReadOnlyProtocol,
        RoutineDefinitionRepositoryReadWriteProtocol,
        RoutineRepositoryReadOnlyProtocol,
        RoutineRepositoryReadWriteProtocol,
        TacticRepositoryReadOnlyProtocol,
        TacticRepositoryReadWriteProtocol,
        TaskDefinitionRepositoryReadOnlyProtocol,
        TaskDefinitionRepositoryReadWriteProtocol,
        TaskRepositoryReadOnlyProtocol,
        TaskRepositoryReadWriteProtocol,
        TimeBlockDefinitionRepositoryReadOnlyProtocol,
        TimeBlockDefinitionRepositoryReadWriteProtocol,
        TriggerRepositoryReadOnlyProtocol,
        TriggerRepositoryReadWriteProtocol,
        UseCaseConfigRepositoryReadOnlyProtocol,
        UseCaseConfigRepositoryReadWriteProtocol,
    )
    from lykke.application.unit_of_work import ReadOnlyRepositories, ReadWriteRepositories


class SqlAlchemyReadOnlyRepositories:
    """SQLAlchemy implementation of ReadOnlyRepositories.

    Provides read-only access to repositories without write capabilities.
    Each repository manages its own database connections for read operations.
    """

    def __init__(self, user: UserEntity) -> None:
        self.user = user

        # Initialize all read-only repositories (all are user-scoped).
        self.auth_token_ro_repo = cast(
            "AuthTokenRepositoryReadOnlyProtocol",
            AuthTokenRepository(user=self.user),
        )
        self.calendar_ro_repo = cast(
            "CalendarRepositoryReadOnlyProtocol",
            CalendarRepository(user=self.user),
        )
        self.day_ro_repo = cast("DayRepositoryReadOnlyProtocol", DayRepository(user=self.user))
        self.day_template_ro_repo = cast(
            "DayTemplateRepositoryReadOnlyProtocol",
            DayTemplateRepository(user=self.user),
        )
        self.calendar_entry_ro_repo = cast(
            "CalendarEntryRepositoryReadOnlyProtocol",
            CalendarEntryRepository(user=self.user),
        )
        self.calendar_entry_series_ro_repo = cast(
            "CalendarEntrySeriesRepositoryReadOnlyProtocol",
            CalendarEntrySeriesRepository(user=self.user),
        )
        self.push_subscription_ro_repo = cast(
            "PushSubscriptionRepositoryReadOnlyProtocol",
            PushSubscriptionRepository(user=self.user),
        )
        self.routine_definition_ro_repo = cast(
            "RoutineDefinitionRepositoryReadOnlyProtocol",
            RoutineDefinitionRepository(user=self.user),
        )
        self.routine_ro_repo = cast(
            "RoutineRepositoryReadOnlyProtocol",
            RoutineRepository(user=self.user),
        )
        self.tactic_ro_repo = cast(
            "TacticRepositoryReadOnlyProtocol",
            TacticRepository(user=self.user),
        )
        self.task_definition_ro_repo = cast(
            "TaskDefinitionRepositoryReadOnlyProtocol",
            TaskDefinitionRepository(user=self.user),
        )
        self.task_ro_repo = cast(
            "TaskRepositoryReadOnlyProtocol", TaskRepository(user=self.user)
        )
        self.time_block_definition_ro_repo = cast(
            "TimeBlockDefinitionRepositoryReadOnlyProtocol",
            TimeBlockDefinitionRepository(user=self.user),
        )
        self.trigger_ro_repo = cast(
            "TriggerRepositoryReadOnlyProtocol",
            TriggerRepository(user=self.user),
        )
        self.usecase_config_ro_repo = cast(
            "UseCaseConfigRepositoryReadOnlyProtocol",
            UseCaseConfigRepository(user=self.user),
        )

        # Chatbot-related repositories
        self.bot_personality_ro_repo = cast(
            "BotPersonalityRepositoryReadOnlyProtocol",
            BotPersonalityRepository(user=self.user),
        )
        self.brain_dump_ro_repo = cast(
            "BrainDumpRepositoryReadOnlyProtocol",
            BrainDumpRepository(user=self.user),
        )
        self.message_ro_repo = cast(
            "MessageRepositoryReadOnlyProtocol",
            MessageRepository(user=self.user),
        )
        self.factoid_ro_repo = cast(
            "FactoidRepositoryReadOnlyProtocol",
            FactoidRepository(user=self.user),
        )

        # AuditLogRepository is read-only (immutable entities)
        self.audit_log_ro_repo = cast(
            "AuditLogRepositoryReadOnlyProtocol",
            AuditLogRepository(user=self.user),
        )
        self.push_notification_ro_repo = cast(
            "PushNotificationRepositoryReadOnlyProtocol",
            PushNotificationRepository(user=self.user),
        )


class SqlAlchemyReadOnlyRepositoryFactory:
    """Factory for creating SqlAlchemyReadOnlyRepositories instances."""

    def create(self, user: UserEntity) -> "ReadOnlyRepositories":
        return SqlAlchemyReadOnlyRepositories(user=user)


class SqlAlchemyReadWriteRepositories:
    """SQLAlchemy implementation of ReadWriteRepositories.

    Provides read-write access to repositories without a Unit of Work.
    Each repository manages its own database connections.
    """

    def __init__(self, user: UserEntity) -> None:
        self.user = user

        # Initialize all read-write repositories (all are user-scoped).
        self.auth_token_rw_repo = cast(
            "AuthTokenRepositoryReadWriteProtocol",
            AuthTokenRepository(user=self.user),
        )
        self.calendar_rw_repo = cast(
            "CalendarRepositoryReadWriteProtocol",
            CalendarRepository(user=self.user),
        )
        self.day_rw_repo = cast("DayRepositoryReadWriteProtocol", DayRepository(user=self.user))
        self.day_template_rw_repo = cast(
            "DayTemplateRepositoryReadWriteProtocol",
            DayTemplateRepository(user=self.user),
        )
        self.calendar_entry_rw_repo = cast(
            "CalendarEntryRepositoryReadWriteProtocol",
            CalendarEntryRepository(user=self.user),
        )
        self.calendar_entry_series_rw_repo = cast(
            "CalendarEntrySeriesRepositoryReadWriteProtocol",
            CalendarEntrySeriesRepository(user=self.user),
        )
        self.push_subscription_rw_repo = cast(
            "PushSubscriptionRepositoryReadWriteProtocol",
            PushSubscriptionRepository(user=self.user),
        )
        self.routine_definition_rw_repo = cast(
            "RoutineDefinitionRepositoryReadWriteProtocol",
            RoutineDefinitionRepository(user=self.user),
        )
        self.routine_rw_repo = cast(
            "RoutineRepositoryReadWriteProtocol",
            RoutineRepository(user=self.user),
        )
        self.tactic_rw_repo = cast(
            "TacticRepositoryReadWriteProtocol",
            TacticRepository(user=self.user),
        )
        self.task_definition_rw_repo = cast(
            "TaskDefinitionRepositoryReadWriteProtocol",
            TaskDefinitionRepository(user=self.user),
        )
        self.task_rw_repo = cast(
            "TaskRepositoryReadWriteProtocol", TaskRepository(user=self.user)
        )
        self.time_block_definition_rw_repo = cast(
            "TimeBlockDefinitionRepositoryReadWriteProtocol",
            TimeBlockDefinitionRepository(user=self.user),
        )
        self.trigger_rw_repo = cast(
            "TriggerRepositoryReadWriteProtocol",
            TriggerRepository(user=self.user),
        )
        self.usecase_config_rw_repo = cast(
            "UseCaseConfigRepositoryReadWriteProtocol",
            UseCaseConfigRepository(user=self.user),
        )

        # Chatbot-related repositories
        self.bot_personality_rw_repo = cast(
            "BotPersonalityRepositoryReadWriteProtocol",
            BotPersonalityRepository(user=self.user),
        )
        self.brain_dump_rw_repo = cast(
            "BrainDumpRepositoryReadWriteProtocol",
            BrainDumpRepository(user=self.user),
        )
        self.message_rw_repo = cast(
            "MessageRepositoryReadWriteProtocol",
            MessageRepository(user=self.user),
        )
        self.factoid_rw_repo = cast(
            "FactoidRepositoryReadWriteProtocol",
            FactoidRepository(user=self.user),
        )
        self.push_notification_rw_repo = cast(
            "PushNotificationRepositoryReadWriteProtocol",
            PushNotificationRepository(user=self.user),
        )


class SqlAlchemyReadWriteRepositoryFactory:
    """Factory for creating SqlAlchemyReadWriteRepositories instances."""

    def create(self, user: UserEntity) -> "ReadWriteRepositories":
        return SqlAlchemyReadWriteRepositories(user=user)

