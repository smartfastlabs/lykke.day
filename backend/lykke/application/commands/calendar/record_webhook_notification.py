"""Command to record a webhook notification and return the calendar."""

from lykke.application.commands.base import BaseCommandHandler
from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntity


class RecordWebhookNotificationHandler(BaseCommandHandler):
    """Records a webhook notification and returns the matching calendar.

    Looks up the calendar by subscription information from the webhook headers.
    """

    async def run(
        self,
        subscription_id: str | None = None,
        resource_id: str | None = None,
    ) -> CalendarEntity | None:
        """Find the calendar matching the webhook subscription info.

        Args:
            subscription_id: The channel/subscription ID from the webhook header
            resource_id: The resource ID from the webhook header

        Returns:
            The calendar entity if found, None otherwise
        """
        query = value_objects.CalendarQuery(
            subscription_id=subscription_id,
            resource_id=resource_id,
        )
        return await self.calendar_ro_repo.get_one_or_none(query)

