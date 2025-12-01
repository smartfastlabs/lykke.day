import asyncio
from datetime import UTC, datetime, timedelta

from loguru import logger

from planned.gateways import google
from planned.objects import Calendar, Event
from planned.repositories import auth_token_repo, calendar_repo, event_repo


class CalendarService:
    running: bool = False

    async def sync_google(
        self,
        calendar: Calendar,
        lookback: datetime,
    ) -> tuple[list[Event], list[Event]]:
        events, deleted_events = [], []

        token = await auth_token_repo.get(calendar.auth_token_id)
        for event in google.load_calendar_events(
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

        try:
            if calendar.platform == "google":
                calendar.last_sync_at = datetime.now(UTC)
                return await self.sync_google(
                    calendar,
                    lookback=lookback,
                )
        except Exception as e:
            logger.info(f"Error syncing calendar: {e}")
            raise

        raise NotImplementedError(
            f"Sync not implemented for platform {calendar.platform}"
        )

    async def sync_all(self) -> None:
        for calendar in await calendar_repo.all():
            events, deleted_events = await self.sync(calendar)
            for event in events:
                await event_repo.put(event)
            for event in deleted_events:
                await event_repo.delete(event)


calendar_svc = CalendarService()
