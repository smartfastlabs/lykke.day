"""Command to sync calendar entries from external calendar providers."""

from datetime import UTC, datetime
from uuid import UUID

from loguru import logger
from planned.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from planned.application.unit_of_work import UnitOfWorkFactory, UnitOfWorkProtocol
from planned.core.constants import CALENDAR_DEFAULT_LOOKBACK, CALENDAR_SYNC_LOOKBACK
from planned.core.exceptions import TokenExpiredError
from planned.domain.entities import CalendarEntity, CalendarEntryEntity
from planned.infrastructure import data_objects


class SyncCalendarHandler:
    """Syncs calendar entries from external provider."""

    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        google_gateway: GoogleCalendarGatewayProtocol,
        user_id: UUID,
    ) -> None:
        self._uow_factory = uow_factory
        self._google_gateway = google_gateway
        self.user_id = user_id

    async def sync_calendar(
        self, calendar_id: UUID
    ) -> tuple[list[CalendarEntryEntity], list[CalendarEntryEntity]]:
        """Sync calendar entries from external provider.

        Args:
            calendar_id: The calendar ID to sync

        Returns:
            Tuple of (calendar_entries, deleted_calendar_entries)
        """
        uow = self._uow_factory.create(self.user_id)
        async with uow:
            calendar = await uow.calendar_ro_repo.get(calendar_id)
            token = await uow.auth_token_ro_repo.get(calendar.auth_token_id)

            # Calculate lookback time
            lookback: datetime = datetime.now(UTC) - CALENDAR_DEFAULT_LOOKBACK
            if calendar.last_sync_at:
                lookback = calendar.last_sync_at - CALENDAR_SYNC_LOOKBACK

            calendar_entries, deleted_calendar_entries = [], []

            if calendar.platform == "google":
                calendar.last_sync_at = datetime.now(UTC)
                for calendar_entry in await self._google_gateway.load_calendar_events(
                    calendar,
                    lookback=lookback,
                    token=token,
                ):
                    if calendar_entry.status == "cancelled":
                        deleted_calendar_entries.append(calendar_entry)
                    else:
                        calendar_entries.append(calendar_entry)
            else:
                raise NotImplementedError(
                    f"Sync not implemented for platform {calendar.platform}"
                )

        return calendar_entries, deleted_calendar_entries

    async def _sync_calendar_internal(
        self,
        calendar: CalendarEntity,
        token: data_objects.AuthToken,
        uow: UnitOfWorkProtocol,
    ) -> tuple[list[CalendarEntryEntity], list[CalendarEntryEntity]]:
        """Internal method to sync a calendar (used by SyncAllCalendarsHandler).

        Args:
            calendar: The calendar to sync
            token: The auth token for the calendar
            uow: The unit of work to use

        Returns:
            Tuple of (calendar_entries, deleted_calendar_entries)
        """
        # Calculate lookback time
        lookback: datetime = datetime.now(UTC) - CALENDAR_DEFAULT_LOOKBACK
        if calendar.last_sync_at:
            lookback = calendar.last_sync_at - CALENDAR_SYNC_LOOKBACK

        calendar_entries, deleted_calendar_entries = [], []

        if calendar.platform == "google":
            calendar.last_sync_at = datetime.now(UTC)
            for calendar_entry in await self._google_gateway.load_calendar_events(
                calendar,
                lookback=lookback,
                token=token,
            ):
                if calendar_entry.status == "cancelled":
                    deleted_calendar_entries.append(calendar_entry)
                else:
                    calendar_entries.append(calendar_entry)
        else:
            raise NotImplementedError(
                f"Sync not implemented for platform {calendar.platform}"
            )

        return calendar_entries, deleted_calendar_entries


class SyncAllCalendarsHandler:
    """Syncs all calendars for a user."""

    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        google_gateway: GoogleCalendarGatewayProtocol,
        user_id: UUID,
    ) -> None:
        self._uow_factory = uow_factory
        self._google_gateway = google_gateway
        self.user_id = user_id

    async def sync_all_calendars(self) -> None:
        """Sync all calendars for the user."""
        uow = self._uow_factory.create(self.user_id)
        async with uow:
            calendars = await uow.calendar_ro_repo.all()
            sync_handler = SyncCalendarHandler(
                self._uow_factory, self._google_gateway, self.user_id
            )

            for calendar in calendars:
                try:
                    token = await uow.auth_token_ro_repo.get(calendar.auth_token_id)
                    (
                        calendar_entries,
                        deleted_calendar_entries,
                    ) = await sync_handler._sync_calendar_internal(calendar, token, uow)

                    # Save calendar entries
                    for calendar_entry in calendar_entries:
                        await uow.create(calendar_entry)
                    for calendar_entry in deleted_calendar_entries:
                        logger.info(f"DELETING CALENDAR ENTRY: {calendar_entry.name}")
                        await uow.delete(calendar_entry)

                    # Update calendar last_sync_at (just set attribute, no event needed)
                    uow.add(calendar)
                except TokenExpiredError:
                    logger.info(f"Token expired for calendar {calendar.name}")
                except Exception as e:
                    logger.exception(f"Error syncing calendar {calendar.name}: {e}")
                    await uow.rollback()
