import asyncio

from planned.services import planning_svc
from planned.utils.dates import get_current_date


async def main():
    result = await planning_svc.schedule_day(get_current_date())
    breakpoint()


if __name__ == "__main__":
    asyncio.run(main())
