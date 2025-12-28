import asyncio

from planned.application.services import DayService
from planned.infrastructure.utils.dates import get_current_date


async def main():
    result = await (await DayService.for_date(get_current_date())).schedule()
    breakpoint()


if __name__ == "__main__":
    asyncio.run(main())
