"""Event handler that sends push notifications when calendar entries change."""

from typing import Any
from uuid import UUID

from loguru import logger

from lykke.application.commands.push_subscription import SendPushNotificationCommand, SendPushNotificationHandler
from lykke.application.gateways.web_push_protocol import WebPushGatewayProtocol
from lykke.application.notifications import build_notification_payload_for_calendar_entry_change
from lykke.domain.entities import CalendarEntryEntity
from lykke.domain.events.base import DomainEvent
from lykke.domain.events.calendar_entry_events import (
    CalendarEntryCreatedEvent,
    CalendarEntryDeletedEvent,
    CalendarEntryUpdatedEvent,
)
from lykke.infrastructure.gateways import WebPushGateway

from .base import DomainEventHandler


class CalendarEntryPushNotificationHandler(DomainEventHandler):
    """Sends push notifications when calendar entries are created, updated, or deleted.

    For each event, loads all of the calendar entry owner's push subscriptions
    and sends a push notification to each one.
    """

    handles = [CalendarEntryCreatedEvent, CalendarEntryUpdatedEvent, CalendarEntryDeletedEvent]

    async def handle(self, event: DomainEvent) -> None:
        """Handle calendar entry events by sending push notifications.

        Args:
            event: The calendar entry event (created/updated/deleted)
        """
        # Extract user_id and calendar_entry_id from event
        user_id: UUID
        calendar_entry_id: UUID
        change_type: str
        entry_data: CalendarEntryEntity | dict[str, Any] | None

        if isinstance(event, CalendarEntryCreatedEvent):
            user_id = event.user_id
            calendar_entry_id = event.calendar_entry_id
            change_type = "created"
            entry_data = None  # Will need to load the entry
        elif isinstance(event, CalendarEntryUpdatedEvent):
            user_id = event.user_id
            calendar_entry_id = event.calendar_entry_id
            change_type = "edited"
            entry_data = None  # Will need to load the entry
        elif isinstance(event, CalendarEntryDeletedEvent):
            user_id = event.user_id
            calendar_entry_id = event.calendar_entry_id
            change_type = "deleted"
            entry_data = event.entry_snapshot  # Already have snapshot
        else:
            logger.warning(f"Unknown calendar entry event type: {type(event)}")
            return

        # Load all push subscriptions for the user
        subscriptions = await self.push_subscription_ro_repo.all()

        if not subscriptions:
            logger.debug(f"No push subscriptions found for user {user_id}")
            return

        # For created/updated events, load the entry to get full data
        if entry_data is None and change_type in ("created", "edited"):
            try:
                entry = await self.calendar_entry_ro_repo.get(calendar_entry_id)
                entry_data = entry
            except Exception as e:
                logger.error(f"Failed to load calendar entry {calendar_entry_id}: {e}")
                return

        # At this point, entry_data should not be None
        if entry_data is None:
            logger.error(f"Entry data is None for {change_type} event on entry {calendar_entry_id}")
            return

        # Build notification payload
        try:
            payload = build_notification_payload_for_calendar_entry_change(
                change_type=change_type,
                entry_data=entry_data,
            )
        except Exception as e:
            logger.error(f"Failed to build notification payload for entry {calendar_entry_id}: {e}")
            return

        # Send push notification to all subscriptions in one batch
        if self._uow_factory is None:
            logger.error("UnitOfWorkFactory not available for sending push notifications")
            return

        web_push_gateway: WebPushGatewayProtocol = WebPushGateway()
        send_handler = SendPushNotificationHandler(
            ro_repos=self._ro_repos,
            uow_factory=self._uow_factory,
            user_id=user_id,
            web_push_gateway=web_push_gateway,
        )

        command = SendPushNotificationCommand(
            subscriptions=subscriptions,
            content=payload,
        )
        await send_handler.handle(command)

        logger.info(
            f"Sent {change_type} notifications for calendar entry {calendar_entry_id} "
            f"to {len(subscriptions)} subscription(s)"
        )
