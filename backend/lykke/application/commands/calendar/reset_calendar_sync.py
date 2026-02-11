"""Command to reset calendar sync: unsubscribe, delete future events, resubscribe, and sync."""

from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from loguru import logger

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.commands.calendar.sync_calendar import SyncCalendarHandler
from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.application.repositories import (
    AuthTokenRepositoryReadOnlyProtocol,
    CalendarEntryRepositoryReadOnlyProtocol,
    CalendarRepositoryReadOnlyProtocol,
)
from lykke.core.config import settings
from lykke.domain import value_objects
from lykke.domain.entities import AuthTokenEntity, CalendarEntity
from lykke.domain.events.calendar_events import CalendarUpdatedEvent
from lykke.domain.value_objects import CalendarUpdateObject
from lykke.domain.value_objects.sync import SyncSubscription

if TYPE_CHECKING:
    from lykke.application.unit_of_work import UnitOfWorkProtocol


@dataclass(frozen=True)
class ResetCalendarSyncCommand(Command):
    """Command to reset calendar sync (takes no args, uses handler's user)."""


class ResetCalendarSyncHandler(
    BaseCommandHandler[ResetCalendarSyncCommand, list[CalendarEntity]]
):
    """Resets calendar sync by unsubscribing, deleting future events, resubscribing, and syncing."""

    google_gateway: GoogleCalendarGatewayProtocol
    sync_calendar_handler: SyncCalendarHandler
    calendar_ro_repo: CalendarRepositoryReadOnlyProtocol
    auth_token_ro_repo: AuthTokenRepositoryReadOnlyProtocol
    calendar_entry_ro_repo: CalendarEntryRepositoryReadOnlyProtocol

    async def handle(self, command: ResetCalendarSyncCommand) -> list[CalendarEntity]:
        """Reset sync for all calendars with subscriptions enabled.

        This operation:
        1. Gets all calendars with sync_subscription enabled
        2. Unsubscribes them from push notifications
        3. Deletes all future calendar entries for those calendars
        4. Resubscribes them to push notifications
        5. Performs initial sync for each calendar

        Returns:
            List of updated CalendarEntity objects
        """
        logger.info(f"Resetting calendar sync for user {self.user.id}")

        async with self.new_uow() as uow:
            # Step 1: Get all calendars with sync_subscription enabled (exclude Lykke)
            all_calendars = await self.calendar_ro_repo.all()
            subscribed_calendars = [
                cal
                for cal in all_calendars
                if cal.sync_subscription is not None
                and cal.auth_token_id is not None
                and cal.platform != "lykke"
            ]

            logger.info(
                f"Found {len(subscribed_calendars)} calendars with subscriptions enabled"
            )

            if not subscribed_calendars:
                logger.info("No calendars with subscriptions found, nothing to reset")
                return []

            # Store calendar IDs for later use (before unsubscribing)
            calendar_ids = [cal.id for cal in subscribed_calendars]

            # Step 2: Unsubscribe all calendars
            for calendar in subscribed_calendars:
                assert calendar.auth_token_id is not None
                try:
                    token = await self.auth_token_ro_repo.get(calendar.auth_token_id)
                    await self._unsubscribe(calendar, token, uow)
                except Exception as e:
                    logger.error(f"Error unsubscribing calendar {calendar.id}: {e}")
                    # Continue with other calendars even if one fails

            # Step 3: Delete all future calendar entries for these calendars
            await self._delete_future_calendar_entries(calendar_ids, uow)

            # Step 4: Resubscribe all calendars (re-fetch to get updated state)
            updated_calendars = []
            for calendar_id in calendar_ids:
                try:
                    calendar = await self.calendar_ro_repo.get(calendar_id)
                    if calendar.auth_token_id is None:
                        continue
                    token = await self.auth_token_ro_repo.get(calendar.auth_token_id)
                    calendar = await self._subscribe(calendar, token, uow)
                    updated_calendars.append(calendar)
                except Exception as e:
                    logger.error(f"Error resubscribing calendar {calendar_id}: {e}")
                    # Continue with other calendars even if one fails

        # Step 5: Perform initial sync for each calendar (using new UoW contexts)
        synced_calendars = []
        for calendar in updated_calendars:
            try:
                synced = await self.sync_calendar_handler.sync_calendar(calendar.id)
                synced_calendars.append(synced)
                logger.info(f"Successfully synced calendar {calendar.id}")
            except Exception as e:
                logger.error(f"Error syncing calendar {calendar.id}: {e}")
                # Still return the calendar even if sync fails
                synced_calendars.append(calendar)

        logger.info(f"Successfully reset sync for {len(synced_calendars)} calendars")
        return synced_calendars

    async def _delete_future_calendar_entries(
        self, calendar_ids: list[UUID], uow: UnitOfWorkProtocol
    ) -> None:
        """Delete all future calendar entries for the given calendars."""
        now = datetime.now(UTC)
        logger.info(
            f"Deleting future calendar entries for {len(calendar_ids)} calendars"
        )

        # Get all entries for these calendars
        all_entries = []
        for calendar_id in calendar_ids:
            entries = await self.calendar_entry_ro_repo.search(
                value_objects.CalendarEntryQuery(calendar_id=calendar_id)
            )
            all_entries.extend(entries)

        # Filter to only future entries
        future_entries = [
            entry for entry in all_entries if entry.starts_at and entry.starts_at >= now
        ]

        logger.info(f"Found {len(future_entries)} future calendar entries to delete")

        # Delete future entries
        for entry in future_entries:
            await uow.delete(entry)

        logger.info(f"Deleted {len(future_entries)} future calendar entries")

    async def _unsubscribe(
        self,
        calendar: CalendarEntity,
        token: AuthTokenEntity,
        uow: UnitOfWorkProtocol,
    ) -> CalendarEntity:
        """Unsubscribe from the provider if currently subscribed."""
        if calendar.platform != "google":
            raise NotImplementedError(
                f"Unsubscribe not implemented for platform {calendar.platform}"
            )

        if calendar.sync_subscription:
            await self.google_gateway.unsubscribe_from_calendar(
                calendar=calendar,
                token=token,
                channel_id=calendar.sync_subscription.subscription_id,
                resource_id=calendar.sync_subscription.resource_id,
            )
            update_data = CalendarUpdateObject(
                sync_subscription=None,
                sync_subscription_id=None,
            )
            calendar = calendar.apply_update(update_data, CalendarUpdatedEvent)
            calendar = uow.add(calendar)
            logger.info(f"Unsubscribed calendar {calendar.id}")

        return calendar

    async def _subscribe(
        self,
        calendar: CalendarEntity,
        token: AuthTokenEntity,
        uow: UnitOfWorkProtocol,
    ) -> CalendarEntity:
        """Subscribe to provider updates and persist metadata."""
        if calendar.platform != "google":
            raise NotImplementedError(
                f"Subscribe not implemented for platform {calendar.platform}"
            )

        channel_id = str(uuid.uuid4())
        client_state = secrets.token_urlsafe(32)

        base_url = settings.API_BASE_URL.rstrip("/")
        webhook_url = f"{base_url}/google/webhook/{self.user.id}/{calendar.id}"

        subscription = await self.google_gateway.subscribe_to_calendar(
            calendar=calendar,
            token=token,
            webhook_url=webhook_url,
            channel_id=channel_id,
            client_state=client_state,
        )

        update_data = CalendarUpdateObject(
            last_sync_at=None,  # Force full lookback on next sync
            sync_subscription=SyncSubscription(
                subscription_id=subscription.channel_id,
                resource_id=subscription.resource_id,
                expiration=subscription.expiration,
                provider="google",
                client_state=client_state,
                sync_token=None,
                webhook_url=webhook_url,
            ),
            sync_subscription_id=subscription.channel_id,
        )

        calendar = calendar.apply_update(update_data, CalendarUpdatedEvent)
        calendar = uow.add(calendar)
        logger.info(f"Resubscribed calendar {calendar.id}")
        return calendar
