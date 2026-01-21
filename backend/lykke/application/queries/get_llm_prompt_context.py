"""Query to get the complete context for LLM prompts."""

import asyncio
from dataclasses import dataclass
from datetime import date as datetime_date
from uuid import UUID

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.queries.get_day_context import GetDayContextHandler
from lykke.application.repositories import (
    ConversationRepositoryReadOnlyProtocol,
    MessageRepositoryReadOnlyProtocol,
    PushNotificationRepositoryReadOnlyProtocol,
)
from lykke.application.unit_of_work import ReadOnlyRepositories
from lykke.domain import value_objects
from lykke.domain.entities import MessageEntity, PushNotificationEntity

_RECENT_MESSAGES_LIMIT = 20
_RECENT_PUSH_NOTIFICATIONS_LIMIT = 20


@dataclass(frozen=True)
class GetLLMPromptContextQuery(Query):
    """Query to get LLM prompt context."""

    date: datetime_date


class GetLLMPromptContextHandler(
    BaseQueryHandler[GetLLMPromptContextQuery, value_objects.LLMPromptContext]
):
    """Gets the complete context needed for LLM prompts."""

    conversation_ro_repo: ConversationRepositoryReadOnlyProtocol
    message_ro_repo: MessageRepositoryReadOnlyProtocol
    push_notification_ro_repo: PushNotificationRepositoryReadOnlyProtocol

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        user_id: UUID,
        get_day_context_handler: GetDayContextHandler,
    ) -> None:
        """Initialize the handler.

        Args:
            ro_repos: Read-only repositories
            user_id: The user ID for scoping
            get_day_context_handler: Handler for base day context
        """
        super().__init__(ro_repos, user_id)
        self._get_day_context_handler = get_day_context_handler

    async def handle(
        self, query: GetLLMPromptContextQuery
    ) -> value_objects.LLMPromptContext:
        """Handle get LLM prompt context query."""
        return await self.get_prompt_context(query.date)

    async def get_prompt_context(
        self, date: datetime_date
    ) -> value_objects.LLMPromptContext:
        """Load complete LLM prompt context for the given date."""
        day_context = await self._get_day_context_handler.get_day_context(date)

        messages, push_notifications = await asyncio.gather(
            self._get_recent_messages(),
            self._get_recent_push_notifications(),
        )

        return value_objects.LLMPromptContext(
            day=day_context.day,
            tasks=day_context.tasks,
            calendar_entries=day_context.calendar_entries,
            messages=messages,
            push_notifications=push_notifications,
        )

    async def _get_recent_messages(self) -> list[MessageEntity]:
        """Load recent messages from the most active conversation."""
        conversations = await self.conversation_ro_repo.search(
            value_objects.ConversationQuery(
                status=value_objects.ConversationStatus.ACTIVE.value,
                order_by="last_message_at",
                order_by_desc=True,
                limit=1,
            )
        )

        if not conversations:
            return []

        messages = await self.message_ro_repo.search(
            value_objects.MessageQuery(
                conversation_id=conversations[0].id,
                order_by="created_at",
                order_by_desc=True,
                limit=_RECENT_MESSAGES_LIMIT,
            )
        )

        return list(reversed(messages))

    async def _get_recent_push_notifications(
        self,
    ) -> list[PushNotificationEntity]:
        """Load recent push notifications for the user."""
        return await self.push_notification_ro_repo.search(
            value_objects.PushNotificationQuery(
                order_by="sent_at",
                order_by_desc=True,
                limit=_RECENT_PUSH_NOTIFICATIONS_LIMIT,
            )
        )
