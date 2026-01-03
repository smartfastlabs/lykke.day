"""CalendarService for managing calendar synchronization.

This service acts as a facade that delegates to command handlers.
It maintains backward compatibility while the codebase transitions to CQRS.
"""

from planned.application.commands.sync_calendar import (
    SyncAllCalendarsHandler,
    SyncCalendarHandler,
)
from planned.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from planned.application.services.base import BaseService
from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import CalendarEntity, CalendarEntryEntity, UserEntity


class CalendarService(BaseService):
    """Service for managing calendar synchronization.

    This service acts as a facade that delegates to command handlers.
    """

    uow_factory: UnitOfWorkFactory
    google_gateway: GoogleCalendarGatewayProtocol
    running: bool = False
    _sync_calendar_handler: SyncCalendarHandler
    _sync_all_calendars_handler: SyncAllCalendarsHandler

    def __init__(
        self,
        user: UserEntity,
        uow_factory: UnitOfWorkFactory,
        google_gateway: GoogleCalendarGatewayProtocol,
    ) -> None:
        """Initialize CalendarService.

        Args:
            user: The user for this service
            uow_factory: Factory for creating UnitOfWork instances
            google_gateway: Gateway for Google Calendar integration
        """
        super().__init__(user)
        self.uow_factory = uow_factory
        self.google_gateway = google_gateway
        self._sync_calendar_handler = SyncCalendarHandler(uow_factory, google_gateway)
        self._sync_all_calendars_handler = SyncAllCalendarsHandler(
            uow_factory, google_gateway
        )

    async def sync(
        self, calendar: CalendarEntity
    ) -> tuple[list[CalendarEntryEntity], list[CalendarEntryEntity]]:
        """Sync a single calendar from its external provider.

        Args:
            calendar: The calendar to sync

        Returns:
            Tuple of (calendar_entries, deleted_calendar_entries)
        """
        return await self._sync_calendar_handler.sync_calendar(
            user_id=self.user.id, calendar_id=calendar.id
        )

    async def sync_all(self) -> None:
        """Sync all calendars for the user."""
        await self._sync_all_calendars_handler.sync_all_calendars(user_id=self.user.id)

