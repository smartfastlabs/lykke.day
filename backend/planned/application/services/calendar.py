from datetime import UTC, datetime

from loguru import logger

from planned.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from planned.application.unit_of_work import UnitOfWorkFactory
from planned.core.constants import CALENDAR_DEFAULT_LOOKBACK, CALENDAR_SYNC_LOOKBACK
from planned.core.exceptions import exceptions
from planned.domain.entities import Calendar, Event, User

from .base import BaseService


class CalendarService(BaseService):
    """Service for managing calendar synchronization."""

    uow_factory: UnitOfWorkFactory
    google_gateway: GoogleCalendarGatewayProtocol
    running: bool = False

    def __init__(
        self,
        user: User,
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

    async def sync_google(
        self,
        calendar: Calendar,
        lookback: datetime,
    ) -> tuple[list[Event], list[Event]]:
        """Sync events from Google Calendar.

        Args:
            calendar: The calendar to sync
            lookback: The datetime to look back from

        Returns:
            Tuple of (events, deleted_events)
        """
        events, deleted_events = [], []

        uow = self.uow_factory.create(self.user.id)
        async with uow:
            token = await uow.auth_tokens.get(calendar.auth_token_id)
            for event in await self.google_gateway.load_calendar_events(
                calendar,
                lookback=lookback,
                token=token,
            ):
                if event.status == "cancelled":
                    deleted_events.append(event)
                else:
                    events.append(event)

        return events, deleted_events

    async def sync(self, calendar: Calendar) -> tuple[list[Event], list[Event]]:
        lookback: datetime = datetime.now(UTC) - CALENDAR_DEFAULT_LOOKBACK
        if calendar.last_sync_at:
            lookback = calendar.last_sync_at - CALENDAR_SYNC_LOOKBACK

        if calendar.platform == "google":
            calendar.last_sync_at = datetime.now(UTC)
            return await self.sync_google(
                calendar,
                lookback=lookback,
            )

        raise NotImplementedError(
            f"Sync not implemented for platform {calendar.platform}"
        )

    async def sync_all(self) -> None:
        """Sync all calendars for the user."""
        uow = self.uow_factory.create(self.user.id)
        async with uow:
            for calendar in await uow.calendars.all():
                try:
                    events, deleted_events = await self.sync(calendar)
                    for event in events:
                        await uow.events.put(event)
                    for event in deleted_events:
                        logger.info(f"DELETING EVENT: {event.name}")
                        await uow.events.delete(event)
                    await uow.commit()
                except exceptions.TokenExpiredError:
                    logger.info(f"Token expired for calendar {calendar.name}")
                except Exception as e:
                    logger.exception(f"Error syncing calendar {calendar.name}: {e}")
                    await uow.rollback()
