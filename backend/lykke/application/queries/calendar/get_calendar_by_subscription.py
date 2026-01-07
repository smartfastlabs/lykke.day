"""Query to get a calendar by subscription ID."""

from lykke.application.queries.base import BaseQueryHandler
from lykke.domain import value_objects
from lykke.domain.entities import CalendarEntity


class GetCalendarBySubscriptionHandler(BaseQueryHandler):
    """Retrieves a calendar by subscription ID.

    Looks up a calendar using its sync subscription channel ID or resource ID.
    """

    async def run(
        self,
        subscription_id: str | None = None,
        resource_id: str | None = None,
    ) -> CalendarEntity | None:
        """Get a calendar by subscription ID or resource ID.

        Args:
            subscription_id: The channel/subscription ID from the webhook
            resource_id: The resource ID from the webhook

        Returns:
            The calendar entity if found, None otherwise
        """
        query = value_objects.CalendarQuery(
            subscription_id=subscription_id,
            resource_id=resource_id,
        )
        return await self.calendar_ro_repo.get_one_or_none(query)
