import asyncio

from planned.services import DayService
from planned.utils.dates import get_current_date


async def main():
    result = await DayService(
        get_current_date(),
    ).schedule()
    breakpoint()


if __name__ == "__main__":
    asyncio.run(main())
