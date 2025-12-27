import asyncio

from planned.application.services import CalendarService
from planned.infrastructure.repositories import (
    AuthTokenRepository,
    CalendarRepository,
    EventRepository,
)


async def main():
    # Create repositories
    auth_token_repo = AuthTokenRepository()  # type: ignore[type-abstract]
    calendar_repo = CalendarRepository()  # type: ignore[type-abstract]
    event_repo = EventRepository()  # type: ignore[type-abstract]

    # Create service
    calendar_service = CalendarService(
        auth_token_repo=auth_token_repo,
        calendar_repo=calendar_repo,
        event_repo=event_repo,
    )

    await calendar_service.sync_all()


if __name__ == "__main__":
    asyncio.run(main())
