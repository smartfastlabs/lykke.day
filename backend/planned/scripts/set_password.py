import asyncio

from planned.services import auth_svc


async def main():
    result = await auth_svc.set_password("password")
    breakpoint()


if __name__ == "__main__":
    asyncio.run(main())
