"""Query to verify Google Calendar webhook requests."""

import hmac
from dataclasses import dataclass
from uuid import UUID

from loguru import logger

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.core.exceptions import NotFoundError


@dataclass(frozen=True)
class VerifyGoogleWebhookQuery(Query):
    """Query to validate a Google webhook request."""

    calendar_id: UUID
    channel_token: str | None
    resource_state: str | None = None


@dataclass(frozen=True)
class VerifyGoogleWebhookResult:
    """Result of Google webhook validation."""

    should_sync: bool


class VerifyGoogleWebhookHandler(
    BaseQueryHandler[VerifyGoogleWebhookQuery, VerifyGoogleWebhookResult]
):
    """Validate Google webhook headers against stored subscription data."""

    async def handle(
        self, query: VerifyGoogleWebhookQuery
    ) -> VerifyGoogleWebhookResult:
        """Validate a webhook request for a specific calendar."""
        if not query.channel_token:
            logger.warning(f"Missing token for calendar {query.calendar_id}")
            return VerifyGoogleWebhookResult(should_sync=False)

        try:
            calendar = await self.calendar_ro_repo.get(query.calendar_id)
        except NotFoundError:
            logger.warning(
                f"Calendar {query.calendar_id} not found for user {self.user_id}"
            )
            return VerifyGoogleWebhookResult(should_sync=False)

        if not calendar.sync_subscription:
            logger.warning(f"Calendar {query.calendar_id} has no sync subscription")
            return VerifyGoogleWebhookResult(should_sync=False)

        client_state = calendar.sync_subscription.client_state
        if client_state is None:
            logger.warning(f"Missing client_state for calendar {query.calendar_id}")
            return VerifyGoogleWebhookResult(should_sync=False)

        if not hmac.compare_digest(client_state, query.channel_token):
            logger.warning(f"Invalid token for calendar {query.calendar_id}")
            return VerifyGoogleWebhookResult(should_sync=False)

        if query.resource_state == "sync":
            logger.info("Received sync verification from Google, triggering sync")

        return VerifyGoogleWebhookResult(should_sync=True)
