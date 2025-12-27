import asyncio

from planned.application.services import CalendarService
from planned.core.di.providers import create_container


async def main():
    container = create_container()
    calendar_service = container.get(CalendarService)
    await calendar_service.sync_all()


if __name__ == "__main__":
    asyncio.run(main())
