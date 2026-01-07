"""Command to sync calendar entries from external calendar providers."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from googleapiclient.errors import HttpError
from loguru import logger
from lykke.application.commands.base import BaseCommandHandler
from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.application.unit_of_work import (
    ReadOnlyRepositories,
    UnitOfWorkFactory,
    UnitOfWorkProtocol,
)
from lykke.core.constants import CALENDAR_DEFAULT_LOOKBACK, CALENDAR_SYNC_LOOKBACK
from lykke.core.exceptions import TokenExpiredError
from lykke.domain import data_objects, value_objects
from lykke.domain.entities import CalendarEntity, CalendarEntryEntity
from lykke.domain.events.calendar_events import CalendarUpdatedEvent
from lykke.domain.value_objects import CalendarUpdateObject

# Max lookahead for calendar events (1 year)
MAX_EVENT_LOOKAHEAD = timedelta(days=365)


class SyncCalendarHandler(BaseCommandHandler):
    """Syncs calendar entries from external provider."""

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
        google_gateway: GoogleCalendarGatewayProtocol,
    ) -> None:
        """Initialize SyncCalendarHandler.

        Args:
            ro_repos: Read-only repositories (from BaseCommandHandler)
            uow_factory: UnitOfWork factory (from BaseCommandHandler)
            user_id: User ID (from BaseCommandHandler)
            google_gateway: Google Calendar gateway
        """
        super().__init__(ro_repos, uow_factory, user_id)
        self._google_gateway = google_gateway

    async def sync_calendar(self, calendar_id: UUID) -> CalendarEntity:
        """Sync a calendar by ID using a fresh unit of work."""
        uow = self.new_uow()
        async with uow:
            calendar = await uow.calendar_ro_repo.get(calendar_id)
            token = await uow.auth_token_ro_repo.get(calendar.auth_token_id)
            return await self.sync_calendar_with_uow(calendar, token, uow)

    async def sync_calendar_entity(self, calendar: CalendarEntity) -> CalendarEntity:
        """Sync a provided calendar entity using a fresh unit of work."""
        uow = self.new_uow()
        async with uow:
            token = await uow.auth_token_ro_repo.get(calendar.auth_token_id)
            return await self.sync_calendar_with_uow(calendar, token, uow)

    async def sync_calendar_with_uow(
        self,
        calendar: CalendarEntity,
        token: data_objects.AuthToken,
        uow: UnitOfWorkProtocol,
    ) -> CalendarEntity:
        """Perform the sync using an existing unit of work."""
        lookback: datetime = datetime.now(UTC) - CALENDAR_DEFAULT_LOOKBACK
        if calendar.last_sync_at:
            lookback = calendar.last_sync_at - CALENDAR_SYNC_LOOKBACK

        sync_token = (
            calendar.sync_subscription.sync_token
            if calendar.sync_subscription
            else None
        )
        (
            fetched_entries,
            fetched_deleted_entries,
            next_sync_token,
        ) = await self._load_calendar_events(calendar, lookback, sync_token, token)

        max_date = datetime.now(UTC) + MAX_EVENT_LOOKAHEAD
        filtered_entries = [
            entry for entry in fetched_entries if entry.starts_at <= max_date
        ]

        for entry in filtered_entries:
            if entry.status == "cancelled":
                await self._delete_if_exists(entry, uow)
            else:
                entry.create()
                uow.add(entry)

        for entry in fetched_deleted_entries:
            await self._delete_if_exists(entry, uow)

        updated_calendar = self._apply_calendar_update(calendar, next_sync_token)
        uow.add(updated_calendar)
        return updated_calendar

    async def _delete_if_exists(
        self, entry: CalendarEntryEntity, uow: UnitOfWorkProtocol
    ) -> None:
        """Delete the entry if present, otherwise log and skip."""
        existing = await uow.calendar_entry_ro_repo.search_one_or_none(
            value_objects.CalendarEntryQuery(platform_id=entry.platform_id)
        )
        if existing:
            await uow.delete(existing)
        else:
            logger.info(
                "Skip delete for event without match",
                event_id=entry.platform_id,
            )

    async def _load_calendar_events(
        self,
        calendar: CalendarEntity,
        lookback: datetime,
        sync_token: str | None,
        token: data_objects.AuthToken,
    ) -> tuple[list[CalendarEntryEntity], list[CalendarEntryEntity], str | None]:
        """Load events from the provider, handling sync token expiration."""
        if calendar.platform != "google":
            raise NotImplementedError(
                f"Sync not implemented for platform {calendar.platform}"
            )

        try:
            return await self._google_gateway.load_calendar_events(
                calendar=calendar,
                lookback=lookback,
                token=token,
                sync_token=sync_token,
            )
        except HttpError as exc:
            if exc.resp.status == 410:
                logger.info("Sync token expired, performing full sync")
                return await self._google_gateway.load_calendar_events(
                    calendar=calendar,
                    lookback=lookback,
                    token=token,
                    sync_token=None,
                )
            raise

    def _apply_calendar_update(
        self, calendar: CalendarEntity, next_sync_token: str | None
    ) -> CalendarEntity:
        """Apply sync metadata updates and emit domain events."""
        updated_subscription = (
            calendar.sync_subscription.model_copy(
                update={"sync_token": next_sync_token}
            )
            if calendar.sync_subscription
            else None
        )
        update_data = CalendarUpdateObject(
            last_sync_at=datetime.now(UTC),
            sync_subscription=updated_subscription,
            sync_subscription_id=calendar.sync_subscription_id,
        )
        return calendar.apply_update(update_data, CalendarUpdatedEvent)


class SyncAllCalendarsHandler(BaseCommandHandler):
    """Syncs all calendars for a user."""

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
        google_gateway: GoogleCalendarGatewayProtocol,
    ) -> None:
        """Initialize SyncAllCalendarsHandler.

        Args:
            ro_repos: Read-only repositories (from BaseCommandHandler)
            uow_factory: UnitOfWork factory (from BaseCommandHandler)
            user_id: User ID (from BaseCommandHandler)
            google_gateway: Google Calendar gateway
        """
        super().__init__(ro_repos, uow_factory, user_id)
        self._google_gateway = google_gateway

    async def sync_all_calendars(self) -> None:
        """Sync all calendars for the user."""
        uow = self.new_uow()
        async with uow:
            calendars = await uow.calendar_ro_repo.all()
            sync_handler = SyncCalendarHandler(
                ro_repos=self._ro_repos,
                uow_factory=self._uow_factory,
                user_id=self.user_id,
                google_gateway=self._google_gateway,
            )

            for calendar in calendars:
                try:
                    token = await uow.auth_token_ro_repo.get(calendar.auth_token_id)
                    await sync_handler.sync_calendar_with_uow(calendar, token, uow)
                except TokenExpiredError:
                    logger.info(f"Token expired for calendar {calendar.name}")
                except Exception as e:  # pylint: disable=broad-except
                    logger.exception(f"Error syncing calendar {calendar.name}: {e}")
                    await uow.rollback()
