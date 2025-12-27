import asyncio

from planned.application.services import calendar_svc


async def main():
    await calendar_svc.sync_all()


if __name__ == "__main__":
    asyncio.run(main())
