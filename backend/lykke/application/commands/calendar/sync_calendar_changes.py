"""Command to sync calendar entries since the last sync."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from loguru import logger
from lykke.application.commands.base import BaseCommandHandler
from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.application.unit_of_work import ReadOnlyRepositories, UnitOfWorkFactory
from lykke.core.exceptions import TokenExpiredError
from lykke.domain.entities import CalendarEntity, CalendarEntryEntity

# Max lookahead for calendar events (1 year)
MAX_EVENT_LOOKAHEAD = timedelta(days=365)


class SyncCalendarChangesHandler(BaseCommandHandler):
    """Syncs calendar entries since the last sync point."""

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
        google_gateway: GoogleCalendarGatewayProtocol,
    ) -> None:
        """Initialize SyncCalendarChangesHandler.

        Args:
            ro_repos: Read-only repositories
            uow_factory: UnitOfWork factory
            user_id: User ID
            google_gateway: Google Calendar gateway
        """
        super().__init__(ro_repos, uow_factory, user_id)
        self._google_gateway = google_gateway

    async def sync(self, calendar: CalendarEntity) -> None:
        """Sync calendar entries from the last sync point.

        Fetches changes since last sync, creates/updates/deletes
        CalendarEntries accordingly, and updates the sync progress.

        Args:
            calendar: The calendar to sync

        Raises:
            NotImplementedError: If calendar platform is not supported
            TokenExpiredError: If the auth token has expired
        """
        uow = self.new_uow()
        async with uow:
            token = await uow.auth_token_ro_repo.get(calendar.auth_token_id)

            if calendar.platform != "google":
                raise NotImplementedError(
                    f"Sync not implemented for platform {calendar.platform}"
                )

            try:
                # Calculate lookback - use last_sync_at or default
                lookback = calendar.last_sync_at or (
                    datetime.now(UTC) - timedelta(days=7)
                )

                # Fetch events from Google
                calendar_entries = await self._google_gateway.load_calendar_events(
                    calendar=calendar,
                    lookback=lookback,
                    token=token,
                )

                # Filter out events more than a year in the future
                max_date = datetime.now(UTC) + MAX_EVENT_LOOKAHEAD
                filtered_entries: list[CalendarEntryEntity] = []
                for entry in calendar_entries:
                    if entry.starts_at <= max_date:
                        filtered_entries.append(entry)
                    else:
                        logger.debug(
                            f"Skipping event '{entry.name}' - starts at {entry.starts_at} "
                            f"which is more than a year out"
                        )

                # Process entries - create or update
                for entry in filtered_entries:
                    if entry.status == "cancelled":
                        logger.info(f"Deleting cancelled event: {entry.name}")
                        await uow.delete(entry)
                    else:
                        await uow.create(entry)

                # Update calendar's last_sync_at
                calendar.last_sync_at = datetime.now(UTC)
                uow.add(calendar)

                logger.info(
                    f"Synced {len(filtered_entries)} entries for calendar '{calendar.name}'"
                )

            except TokenExpiredError:
                logger.warning(f"Token expired for calendar {calendar.name}")
                raise
            except Exception as e:
                logger.exception(f"Error syncing calendar {calendar.name}: {e}")
                raise
