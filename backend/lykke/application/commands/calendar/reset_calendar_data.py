"""Command to purge calendar data and refresh webhook subscriptions for a user."""

from __future__ import annotations

import secrets
import uuid
from typing import Iterable
from uuid import UUID

from lykke.application.commands.base import BaseCommandHandler
from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.application.unit_of_work import (
    ReadOnlyRepositories,
    UnitOfWorkFactory,
    UnitOfWorkProtocol,
)
from lykke.core.config import settings
from lykke.domain import value_objects
from lykke.domain.entities import AuthTokenEntity
from lykke.domain.entities import CalendarEntity, CalendarEntryEntity, CalendarEntrySeriesEntity
from lykke.domain.events.calendar_events import CalendarUpdatedEvent
from lykke.domain.value_objects import CalendarUpdateObject
from lykke.domain.value_objects.sync import SyncSubscription


class ResetCalendarDataHandler(BaseCommandHandler):
    """Delete calendar entries/series and refresh subscriptions for the user."""

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
        google_gateway: GoogleCalendarGatewayProtocol,
    ) -> None:
        super().__init__(ro_repos, uow_factory, user_id)
        self._google_gateway = google_gateway

    async def reset(self) -> list[CalendarEntity]:
        """Remove all entries/series then refresh subscriptions for subscribed calendars."""
        updated_calendars: list[CalendarEntity] = []
        uow = self.new_uow()

        async with uow:
            await self._delete_calendar_entries(uow)
            await self._delete_calendar_entry_series(uow)

            calendars = await uow.calendar_ro_repo.all()
            for calendar in calendars:
                if calendar.sync_subscription is None:
                    continue

                token = await uow.auth_token_ro_repo.get(calendar.auth_token_id)
                refreshed = await self._refresh_subscription(calendar, token, uow)
                updated_calendars.append(refreshed)

        return updated_calendars

    async def _delete_calendar_entries(self, uow: UnitOfWorkProtocol) -> None:
        """Delete all calendar entries for the scoped user."""
        entries: Iterable[CalendarEntryEntity] = await uow.calendar_entry_ro_repo.search(
            value_objects.CalendarEntryQuery()
        )
        for entry in entries:
            await uow.delete(entry)

    async def _delete_calendar_entry_series(self, uow: UnitOfWorkProtocol) -> None:
        """Delete all calendar entry series for the scoped user."""
        series_items: Iterable[
            CalendarEntrySeriesEntity
        ] = await uow.calendar_entry_series_ro_repo.search(
            value_objects.CalendarEntrySeriesQuery()
        )
        for series in series_items:
            await uow.delete(series)

    async def _refresh_subscription(
        self,
        calendar: CalendarEntity,
        token: AuthTokenEntity,
        uow: UnitOfWorkProtocol,
    ) -> CalendarEntity:
        """Unsubscribe and re-subscribe the calendar to provider webhooks."""
        if calendar.platform != "google":
            raise NotImplementedError(
                f"Reset not implemented for platform {calendar.platform}"
            )

        if calendar.sync_subscription:
            await self._google_gateway.unsubscribe_from_calendar(
                calendar=calendar,
                token=token,
                channel_id=calendar.sync_subscription.subscription_id,
                resource_id=calendar.sync_subscription.resource_id,
            )

        channel_id = str(uuid.uuid4())
        client_state = secrets.token_urlsafe(32)
        base_url = settings.API_BASE_URL.rstrip("/")
        webhook_url = f"{base_url}/google/webhook/{self.user_id}/{calendar.id}"

        subscription = await self._google_gateway.subscribe_to_calendar(
            calendar=calendar,
            token=token,
            webhook_url=webhook_url,
            channel_id=channel_id,
            client_state=client_state,
        )

        update_data = CalendarUpdateObject(
            last_sync_at=None,
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

        refreshed_calendar = calendar.apply_update(update_data, CalendarUpdatedEvent)
        uow.add(refreshed_calendar)
        return refreshed_calendar

