"""Base handler class shared by commands, queries, and event handlers."""

from typing import TYPE_CHECKING, Any
from uuid import UUID

from lykke.application.unit_of_work import ReadOnlyRepositories

if TYPE_CHECKING:
    from lykke.application.repositories import (
        AuditLogRepositoryReadOnlyProtocol,
        AuthTokenRepositoryReadOnlyProtocol,
        BotPersonalityRepositoryReadOnlyProtocol,
        BrainDumpRepositoryReadOnlyProtocol,
        CalendarEntryRepositoryReadOnlyProtocol,
        CalendarEntrySeriesRepositoryReadOnlyProtocol,
        CalendarRepositoryReadOnlyProtocol,
        DayRepositoryReadOnlyProtocol,
        DayTemplateRepositoryReadOnlyProtocol,
        FactoidRepositoryReadOnlyProtocol,
        MessageRepositoryReadOnlyProtocol,
        PushNotificationRepositoryReadOnlyProtocol,
        PushSubscriptionRepositoryReadOnlyProtocol,
        RoutineDefinitionRepositoryReadOnlyProtocol,
        RoutineRepositoryReadOnlyProtocol,
        SmsLoginCodeRepositoryReadOnlyProtocol,
        TacticRepositoryReadOnlyProtocol,
        TaskDefinitionRepositoryReadOnlyProtocol,
        TaskRepositoryReadOnlyProtocol,
        TimeBlockDefinitionRepositoryReadOnlyProtocol,
        TriggerRepositoryReadOnlyProtocol,
        UseCaseConfigRepositoryReadOnlyProtocol,
        UserRepositoryReadOnlyProtocol,
    )


class BaseHandler:
    """Base class for handlers with lazy repository access.

    This class provides common initialization for command handlers, query handlers,
    and event handlers. Repository access is lazy via __getattr__, so handlers only
    access the repositories they actually need.

    Usage:
        class MyHandler(BaseHandler):
            async def handle(self, command: MyCommand) -> None:
                # Access repositories as needed - they're resolved lazily
                task = await self.task_ro_repo.get(command.task_id)
                day = await self.day_ro_repo.get(command.day_id)
    """

    # Repository attribute suffix used to identify repository lookups
    _REPO_SUFFIX = "_ro_repo"

    # Type hints for static analysis (repos are accessed lazily at runtime)
    audit_log_ro_repo: "AuditLogRepositoryReadOnlyProtocol"
    auth_token_ro_repo: "AuthTokenRepositoryReadOnlyProtocol"
    bot_personality_ro_repo: "BotPersonalityRepositoryReadOnlyProtocol"
    brain_dump_ro_repo: "BrainDumpRepositoryReadOnlyProtocol"
    calendar_entry_ro_repo: "CalendarEntryRepositoryReadOnlyProtocol"
    calendar_entry_series_ro_repo: "CalendarEntrySeriesRepositoryReadOnlyProtocol"
    calendar_ro_repo: "CalendarRepositoryReadOnlyProtocol"
    day_ro_repo: "DayRepositoryReadOnlyProtocol"
    day_template_ro_repo: "DayTemplateRepositoryReadOnlyProtocol"
    factoid_ro_repo: "FactoidRepositoryReadOnlyProtocol"
    message_ro_repo: "MessageRepositoryReadOnlyProtocol"
    push_notification_ro_repo: "PushNotificationRepositoryReadOnlyProtocol"
    push_subscription_ro_repo: "PushSubscriptionRepositoryReadOnlyProtocol"
    routine_ro_repo: "RoutineRepositoryReadOnlyProtocol"
    routine_definition_ro_repo: "RoutineDefinitionRepositoryReadOnlyProtocol"
    tactic_ro_repo: "TacticRepositoryReadOnlyProtocol"
    task_definition_ro_repo: "TaskDefinitionRepositoryReadOnlyProtocol"
    task_ro_repo: "TaskRepositoryReadOnlyProtocol"
    time_block_definition_ro_repo: "TimeBlockDefinitionRepositoryReadOnlyProtocol"
    trigger_ro_repo: "TriggerRepositoryReadOnlyProtocol"
    usecase_config_ro_repo: "UseCaseConfigRepositoryReadOnlyProtocol"
    user_ro_repo: "UserRepositoryReadOnlyProtocol"
    sms_login_code_ro_repo: "SmsLoginCodeRepositoryReadOnlyProtocol"

    def __init__(self, ro_repos: ReadOnlyRepositories, user_id: UUID) -> None:
        """Initialize the handler with its dependencies.

        Args:
            ro_repos: Read-only repositories container
            user_id: The user ID for this handler instance
        """
        self.user_id = user_id
        self._ro_repos = ro_repos

    def __getattr__(self, name: str) -> Any:
        """Provide lazy access to repositories from the container.

        This allows handlers to access repositories like self.task_ro_repo
        without explicitly wiring them in __init__. The repository is looked
        up from _ro_repos on first access.

        Args:
            name: Attribute name being accessed

        Returns:
            The repository if it exists on _ro_repos

        Raises:
            AttributeError: If the attribute doesn't exist on _ro_repos
        """
        # Only intercept repository lookups
        if name.endswith(self._REPO_SUFFIX):
            # Try to get from _ro_repos
            try:
                ro_repos = object.__getattribute__(self, "_ro_repos")
                return getattr(ro_repos, name)
            except AttributeError:
                pass

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )
