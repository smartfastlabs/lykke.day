import asyncio
import sys
from pathlib import Path

# Add parent directory to path so we can import planned
sys.path.insert(0, str(Path(__file__).parent.parent))

from planned.application.services import auth_svc


async def main():
    result = await auth_svc.set_password("password")
    breakpoint()


if __name__ == "__main__":
    asyncio.run(main())
