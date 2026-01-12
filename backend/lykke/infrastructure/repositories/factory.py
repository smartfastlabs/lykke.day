"""Repository factory for creating repository instances."""

from typing import Any
from uuid import UUID

from lykke.infrastructure.repositories import (
    AuthTokenRepository,
    CalendarEntryRepository,
    CalendarEntrySeriesRepository,
    CalendarRepository,
    DayRepository,
    DayTemplateRepository,
    PushSubscriptionRepository,
    RoutineRepository,
    TaskDefinitionRepository,
    TaskRepository,
    TimeBlockDefinitionRepository,
    UserRepository,
)


class RepositoryFactory:
    """Factory for creating repository instances with consistent patterns."""

    @staticmethod
    def create_all_repositories(user_id: UUID) -> dict[str, Any]:
        """Create all repository instances for a given user_id.

        Returns a dictionary mapping repository names to instances.
        Non-user-scoped repositories (user, auth_token) are created without user_id.

        Args:
            user_id: The user ID to scope repositories to.

        Returns:
            Dictionary with keys:
                - user: UserRepository (no user scoping)
                - auth_token: AuthTokenRepository (no user scoping)
                - calendar: CalendarRepository
                - calendar_entry: CalendarEntryRepository
                - calendar_entry_series: CalendarEntrySeriesRepository
                - day: DayRepository
                - day_template: DayTemplateRepository
                - push_subscription: PushSubscriptionRepository
                - routine: RoutineRepository
                - task: TaskRepository
                - task_definition: TaskDefinitionRepository
                - time_block_definition: TimeBlockDefinitionRepository
        """
        return {
            # Non-user-scoped repositories
            "user": UserRepository(),
            "auth_token": AuthTokenRepository(),
            # User-scoped repositories
            "calendar": CalendarRepository(user_id=user_id),
            "calendar_entry": CalendarEntryRepository(user_id=user_id),
            "calendar_entry_series": CalendarEntrySeriesRepository(user_id=user_id),
            "day": DayRepository(user_id=user_id),
            "day_template": DayTemplateRepository(user_id=user_id),
            "push_subscription": PushSubscriptionRepository(user_id=user_id),
            "routine": RoutineRepository(user_id=user_id),
            "task": TaskRepository(user_id=user_id),
            "task_definition": TaskDefinitionRepository(user_id=user_id),
            "time_block_definition": TimeBlockDefinitionRepository(user_id=user_id),
        }
