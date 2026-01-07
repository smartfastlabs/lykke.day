"""Command to subscribe a calendar to push notifications for changes."""

import uuid
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler
from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.application.unit_of_work import ReadOnlyRepositories, UnitOfWorkFactory
from lykke.core.config import settings
from lykke.domain.entities import CalendarEntity
from lykke.domain.value_objects.sync import SyncSubscription


class SubscribeCalendarHandler(BaseCommandHandler):
    """Subscribes a calendar to push notifications for changes."""

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
        google_gateway: GoogleCalendarGatewayProtocol,
    ) -> None:
        """Initialize SubscribeCalendarHandler.

        Args:
            ro_repos: Read-only repositories (from BaseCommandHandler)
            uow_factory: UnitOfWork factory (from BaseCommandHandler)
            user_id: User ID (from BaseCommandHandler)
            google_gateway: Google Calendar gateway
        """
        super().__init__(ro_repos, uow_factory, user_id)
        self._google_gateway = google_gateway

    async def subscribe(self, calendar: CalendarEntity) -> CalendarEntity:
        """Subscribe a calendar to push notifications.

        Creates a watch channel on the specified calendar that will send
        push notifications when events change. Stores the subscription
        information on the CalendarEntity.

        Args:
            calendar: The calendar entity to subscribe.

        Returns:
            The updated CalendarEntity with sync_subscription set.

        Raises:
            NotImplementedError: If the calendar platform is not supported.
        """
        uow = self.new_uow()
        async with uow:
            token = await uow.auth_token_ro_repo.get(calendar.auth_token_id)

            if calendar.platform == "google":
                # Generate unique channel ID for this subscription
                channel_id = str(uuid.uuid4())

                # Build webhook URL with user_id - Google will call this when events change
                webhook_url = f"{settings.API_PREFIX}/google/webhook/{self.user_id}"

                # Subscribe to calendar changes via Google API
                subscription = await self._google_gateway.subscribe_to_calendar(
                    calendar=calendar,
                    token=token,
                    webhook_url=webhook_url,
                    channel_id=channel_id,
                )

                # Store subscription info on the calendar entity
                calendar.sync_subscription = SyncSubscription(
                    subscription_id=subscription.channel_id,
                    resource_id=subscription.resource_id,
                    expiration=subscription.expiration,
                    provider="google",
                )

                # Persist the updated calendar
                uow.add(calendar)
            else:
                raise NotImplementedError(
                    f"Subscription not implemented for platform {calendar.platform}"
                )

        return calendar
