"""Command to sync calendar entries from external calendar providers."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from loguru import logger
from planned.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from planned.application.unit_of_work import UnitOfWorkFactory, UnitOfWorkProtocol
from planned.core.constants import CALENDAR_DEFAULT_LOOKBACK, CALENDAR_SYNC_LOOKBACK
from planned.core.exceptions import TokenExpiredError
from planned.domain.entities import AuthToken, Calendar, CalendarEntry

from .base import Command, CommandHandler


@dataclass(frozen=True)
class SyncCalendarCommand(Command):
    """Command to sync a single calendar from its external provider.

    Fetches calendar entries from the external provider and saves them.
    """

    user_id: UUID
    calendar_id: UUID


@dataclass(frozen=True)
class SyncAllCalendarsCommand(Command):
    """Command to sync all calendars for a user.

    Iterates through all user calendars and syncs each one.
    """

    user_id: UUID


class SyncCalendarHandler(
    CommandHandler[SyncCalendarCommand, tuple[list[CalendarEntry], list[CalendarEntry]]]
):
    """Handles SyncCalendarCommand."""

    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        google_gateway: GoogleCalendarGatewayProtocol,
    ) -> None:
        self._uow_factory = uow_factory
        self._google_gateway = google_gateway

    async def handle(
        self, cmd: SyncCalendarCommand
    ) -> tuple[list[CalendarEntry], list[CalendarEntry]]:
        """Sync calendar entries from external provider.

        Args:
            cmd: The sync command

        Returns:
            Tuple of (calendar_entries, deleted_calendar_entries)
        """
        uow = self._uow_factory.create(cmd.user_id)
        async with uow:
            calendar = await uow.calendars.get(cmd.calendar_id)
            token = await uow.auth_tokens.get(calendar.auth_token_id)

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
        calendar: Calendar,
        token: AuthToken,
        uow: UnitOfWorkProtocol,
    ) -> tuple[list[CalendarEntry], list[CalendarEntry]]:
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


class SyncAllCalendarsHandler(CommandHandler[SyncAllCalendarsCommand, None]):
    """Handles SyncAllCalendarsCommand."""

    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        google_gateway: GoogleCalendarGatewayProtocol,
    ) -> None:
        self._uow_factory = uow_factory
        self._google_gateway = google_gateway

    async def handle(self, cmd: SyncAllCalendarsCommand) -> None:
        """Sync all calendars for the user.

        Args:
            cmd: The sync all command
        """
        uow = self._uow_factory.create(cmd.user_id)
        async with uow:
            calendars = await uow.calendars.all()
            sync_handler = SyncCalendarHandler(self._uow_factory, self._google_gateway)

            for calendar in calendars:
                try:
                    token = await uow.auth_tokens.get(calendar.auth_token_id)
                    (
                        calendar_entries,
                        deleted_calendar_entries,
                    ) = await sync_handler._sync_calendar_internal(calendar, token, uow)

                    # Save calendar entries
                    for calendar_entry in calendar_entries:
                        await uow.calendar_entries.put(calendar_entry)
                    for calendar_entry in deleted_calendar_entries:
                        logger.info(f"DELETING CALENDAR ENTRY: {calendar_entry.name}")
                        await uow.calendar_entries.delete(calendar_entry)

                    # Update calendar last_sync_at
                    await uow.calendars.put(calendar)
                    await uow.commit()
                except TokenExpiredError:
                    logger.info(f"Token expired for calendar {calendar.name}")
                except Exception as e:
                    logger.exception(f"Error syncing calendar {calendar.name}: {e}")
                    await uow.rollback()
