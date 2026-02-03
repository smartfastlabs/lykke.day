"""Command to fully resync a calendar: purge entries, refresh subscription, and sync."""

from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.repositories import (
    AuthTokenRepositoryReadOnlyProtocol,
    CalendarEntryRepositoryReadOnlyProtocol,
)
from lykke.core.config import settings
from lykke.domain import value_objects
from lykke.domain.entities import AuthTokenEntity, CalendarEntity
from lykke.domain.events.calendar_events import CalendarUpdatedEvent
from lykke.domain.value_objects import CalendarUpdateObject
from lykke.domain.value_objects.sync import SyncSubscription

if TYPE_CHECKING:
    from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
    from lykke.application.unit_of_work import (
        UnitOfWorkProtocol,
    )

    from .sync_calendar import SyncCalendarHandler


@dataclass(frozen=True)
class ResyncCalendarCommand(Command):
    """Command to fully resync a calendar."""

    calendar: CalendarEntity


class ResyncCalendarHandler(BaseCommandHandler[ResyncCalendarCommand, CalendarEntity]):
    """Deletes existing entries, refreshes subscription, and triggers a full sync."""

    google_gateway: GoogleCalendarGatewayProtocol
    sync_calendar_handler: SyncCalendarHandler
    auth_token_ro_repo: AuthTokenRepositoryReadOnlyProtocol
    calendar_entry_ro_repo: CalendarEntryRepositoryReadOnlyProtocol

    async def handle(self, command: ResyncCalendarCommand) -> CalendarEntity:
        """Perform a full resync of the given calendar."""
        calendar = command.calendar
        uow = self.new_uow()
        async with uow:
            token = await self.auth_token_ro_repo.get(calendar.auth_token_id)

            await self._delete_calendar_entries(calendar.id, uow)
            calendar = await self._unsubscribe(calendar, token, uow)
            calendar = await self._subscribe(calendar, token, uow)

        # Run a fresh sync after subscription refresh using a new UoW context
        return await self.sync_calendar_handler.sync_calendar(calendar.id)

    async def _delete_calendar_entries(
        self, calendar_id: UUID, uow: UnitOfWorkProtocol
    ) -> None:
        """Remove all calendar entries for the calendar."""
        entries = await self.calendar_entry_ro_repo.search(
            value_objects.CalendarEntryQuery(calendar_id=calendar_id)
        )
        for entry in entries:
            await uow.delete(entry)

    async def _unsubscribe(
        self,
        calendar: CalendarEntity,
        token: AuthTokenEntity,
        uow: UnitOfWorkProtocol,
    ) -> CalendarEntity:
        """Unsubscribe from the provider if currently subscribed."""
        if calendar.platform != "google":
            raise NotImplementedError(
                f"Resync not implemented for platform {calendar.platform}"
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
                # Clear last sync timestamp to force fresh lookback
                last_sync_at=None,
            )
            calendar = calendar.apply_update(update_data, CalendarUpdatedEvent)
            calendar = uow.add(calendar)

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
                f"Resync not implemented for platform {calendar.platform}"
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
        return uow.add(calendar)
