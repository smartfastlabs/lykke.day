from datetime import UTC, datetime, timedelta

from loguru import logger

from planned.application.repositories import (
    AuthTokenRepositoryProtocol,
    CalendarRepositoryProtocol,
    EventRepositoryProtocol,
)
from planned.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from planned.core.exceptions import exceptions
from planned.domain.entities import Calendar, Event

from .base import BaseService


class CalendarService(BaseService):
    auth_token_repo: AuthTokenRepositoryProtocol
    calendar_repo: CalendarRepositoryProtocol
    event_repo: EventRepositoryProtocol
    google_gateway: GoogleCalendarGatewayProtocol
    running: bool = False

    def __init__(
        self,
        auth_token_repo: AuthTokenRepositoryProtocol,
        calendar_repo: CalendarRepositoryProtocol,
        event_repo: EventRepositoryProtocol,
        google_gateway: GoogleCalendarGatewayProtocol,
    ) -> None:
        self.auth_token_repo = auth_token_repo
        self.calendar_repo = calendar_repo
        self.event_repo = event_repo
        self.google_gateway = google_gateway


    async def sync_google(
        self,
        calendar: Calendar,
        lookback: datetime,
    ) -> tuple[list[Event], list[Event]]:
        events, deleted_events = [], []

        token = await self.auth_token_repo.get(calendar.auth_token_uuid)
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
        lookback: datetime = datetime.now(UTC) - timedelta(days=2)
        if calendar.last_sync_at:
            lookback = calendar.last_sync_at - timedelta(minutes=30)

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
        for calendar in await self.calendar_repo.all():
            try:
                events, deleted_events = await self.sync(calendar)
                for event in events:
                    await self.event_repo.put(event)
                for event in deleted_events:
                    logger.info(f"DELETING EVENT: {event.name}")
                    await self.event_repo.delete(event)
            except exceptions.TokenExpiredError:
                logger.info(f"Token expired for calendar {calendar.name}")
            except Exception as e:
                logger.exception(f"Error syncing calendar {calendar.name}: {e}")
