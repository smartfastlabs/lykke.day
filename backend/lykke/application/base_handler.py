"""Base handler class shared by commands, queries, and event handlers."""

from uuid import UUID

from lykke.application.unit_of_work import ReadOnlyRepositories


class BaseHandler:
    """Base class for handlers with explicit dependency wiring.

    This class provides common initialization for command handlers, query handlers,
    and event handlers, reducing duplication in __init__ methods.
    """

    def __init__(self, ro_repos: ReadOnlyRepositories, user_id: UUID) -> None:
        """Initialize the handler with its dependencies.

        Args:
            ro_repos: Read-only repositories container
            user_id: The user ID for this handler instance
        """
        self.user_id = user_id
        self._ro_repos = ro_repos
        # Explicitly expose read-only repositories for convenience
        self.audit_log_ro_repo = ro_repos.audit_log_ro_repo
        self.auth_token_ro_repo = ro_repos.auth_token_ro_repo
        self.bot_personality_ro_repo = ro_repos.bot_personality_ro_repo
        self.brain_dump_ro_repo = ro_repos.brain_dump_ro_repo
        self.calendar_entry_ro_repo = ro_repos.calendar_entry_ro_repo
        self.calendar_entry_series_ro_repo = ro_repos.calendar_entry_series_ro_repo
        self.calendar_ro_repo = ro_repos.calendar_ro_repo
        self.conversation_ro_repo = ro_repos.conversation_ro_repo
        self.day_ro_repo = ro_repos.day_ro_repo
        self.day_template_ro_repo = ro_repos.day_template_ro_repo
        self.factoid_ro_repo = ro_repos.factoid_ro_repo
        self.message_ro_repo = ro_repos.message_ro_repo
        self.push_notification_ro_repo = ro_repos.push_notification_ro_repo
        self.push_subscription_ro_repo = ro_repos.push_subscription_ro_repo
        self.routine_definition_ro_repo = ro_repos.routine_definition_ro_repo
        self.task_definition_ro_repo = ro_repos.task_definition_ro_repo
        self.task_ro_repo = ro_repos.task_ro_repo
        self.time_block_definition_ro_repo = ro_repos.time_block_definition_ro_repo
        self.usecase_config_ro_repo = ro_repos.usecase_config_ro_repo
        self.user_ro_repo = ro_repos.user_ro_repo
