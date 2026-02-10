"""Command to subscribe a calendar to push notifications for changes."""

import secrets
import uuid
from dataclasses import dataclass
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.application.repositories import AuthTokenRepositoryReadOnlyProtocol
from lykke.core.config import settings
from lykke.domain.entities import CalendarEntity
from lykke.domain.events.calendar_events import CalendarUpdatedEvent
from lykke.domain.value_objects import CalendarUpdateObject
from lykke.domain.value_objects.sync import SyncSubscription


@dataclass(frozen=True)
class SubscribeCalendarCommand(Command):
    """Command to subscribe a calendar to push notifications."""

    calendar: CalendarEntity


class SubscribeCalendarHandler(
    BaseCommandHandler[SubscribeCalendarCommand, CalendarEntity]
):
    """Subscribes a calendar to push notifications for changes."""

    google_gateway: GoogleCalendarGatewayProtocol
    auth_token_ro_repo: AuthTokenRepositoryReadOnlyProtocol

    async def handle(self, command: SubscribeCalendarCommand) -> CalendarEntity:
        """Subscribe a calendar to push notifications.

        Creates a watch channel on the specified calendar that will send
        push notifications when events change. Stores the subscription
        information on the CalendarEntity.

        Args:
            command: The command containing the calendar entity to subscribe.

        Returns:
            The updated CalendarEntity with sync_subscription set.

        Raises:
            NotImplementedError: If the calendar platform is not supported.
        """
        calendar = command.calendar
        if calendar.platform == "lykke":
            return calendar
        if calendar.auth_token_id is None:
            raise ValueError("Calendar has no auth token; cannot subscribe")
        uow = self.new_uow()
        async with uow:
            token = await self.auth_token_ro_repo.get(calendar.auth_token_id)

            if calendar.platform == "google":
                # Generate unique channel ID for this subscription
                channel_id = str(uuid.uuid4())

                # Generate secret token for webhook verification
                client_state = secrets.token_urlsafe(32)

                # Build webhook URL with user_id and calendar_id
                base_url = settings.API_BASE_URL.rstrip("/")
                webhook_url = f"{base_url}/google/webhook/{self.user.id}/{calendar.id}"

                # Subscribe to calendar changes via Google API
                subscription = await self.google_gateway.subscribe_to_calendar(
                    calendar=calendar,
                    token=token,
                    webhook_url=webhook_url,
                    channel_id=channel_id,
                    client_state=client_state,
                )

                update_data = CalendarUpdateObject(
                    sync_subscription=SyncSubscription(
                        subscription_id=subscription.channel_id,
                        resource_id=subscription.resource_id,
                        expiration=subscription.expiration,
                        provider="google",
                        client_state=client_state,
                        webhook_url=webhook_url,
                    ),
                    sync_subscription_id=subscription.channel_id,
                )

                calendar = calendar.apply_update(update_data, CalendarUpdatedEvent)
                uow.add(calendar)
            else:
                raise NotImplementedError(
                    f"Subscription not implemented for platform {calendar.platform}"
                )

        return calendar
