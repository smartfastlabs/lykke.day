"""Query to get the complete context for LLM prompts."""

import asyncio
from dataclasses import dataclass
from datetime import UTC, date as datetime_date, datetime, timedelta

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.queries.get_day_context import GetDayContextHandler
from lykke.application.repositories import (
    FactoidRepositoryReadOnlyProtocol,
    MessageRepositoryReadOnlyProtocol,
    PushNotificationRepositoryReadOnlyProtocol,
)
from lykke.domain import value_objects
from lykke.domain.entities import FactoidEntity, MessageEntity, PushNotificationEntity

_RECENT_MESSAGES_LIMIT = 20
_RECENT_PUSH_NOTIFICATIONS_LIMIT = 20
_RECENT_PUSH_NOTIFICATIONS_WINDOW = timedelta(hours=4)


@dataclass(frozen=True)
class GetLLMPromptContextQuery(Query):
    """Query to get LLM prompt context."""

    date: datetime_date


class GetLLMPromptContextHandler(
    BaseQueryHandler[GetLLMPromptContextQuery, value_objects.LLMPromptContext]
):
    """Gets the complete context needed for LLM prompts."""

    factoid_ro_repo: FactoidRepositoryReadOnlyProtocol
    message_ro_repo: MessageRepositoryReadOnlyProtocol
    push_notification_ro_repo: PushNotificationRepositoryReadOnlyProtocol
    get_day_context_handler: GetDayContextHandler

    async def handle(
        self, query: GetLLMPromptContextQuery
    ) -> value_objects.LLMPromptContext:
        """Handle get LLM prompt context query."""
        return await self.get_prompt_context(query.date)

    async def get_prompt_context(
        self, date: datetime_date
    ) -> value_objects.LLMPromptContext:
        """Load complete LLM prompt context for the given date."""
        day_context = await self.get_day_context_handler.get_day_context(date)

        factoids, messages, push_notifications = await asyncio.gather(
            self._get_factoids(),
            self._get_recent_messages(),
            self._get_recent_push_notifications(),
        )

        return value_objects.LLMPromptContext(
            day=day_context.day,
            tasks=day_context.tasks,
            calendar_entries=day_context.calendar_entries,
            brain_dumps=day_context.brain_dumps,
            factoids=factoids,
            messages=messages,
            push_notifications=push_notifications,
        )

    async def _get_recent_messages(self) -> list[MessageEntity]:
        """Load recent messages for the user."""
        messages = await self.message_ro_repo.search(
            value_objects.MessageQuery(
                order_by="created_at",
                order_by_desc=True,
                limit=_RECENT_MESSAGES_LIMIT,
            )
        )
        return list(reversed(messages))

    async def _get_factoids(self) -> list[FactoidEntity]:
        """Load all factoids for the user."""
        return await self.factoid_ro_repo.all()

    async def _get_recent_push_notifications(
        self,
    ) -> list[PushNotificationEntity]:
        """Load recent push notifications for the user."""
        cutoff = datetime.now(UTC) - _RECENT_PUSH_NOTIFICATIONS_WINDOW
        return await self.push_notification_ro_repo.search(
            value_objects.PushNotificationQuery(
                order_by="sent_at",
                order_by_desc=True,
                sent_after=cutoff,
                limit=_RECENT_PUSH_NOTIFICATIONS_LIMIT,
            )
        )
