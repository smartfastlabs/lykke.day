import os
from contextlib import suppress

import aiofiles
from passlib.context import CryptContext

from planned import settings

from .base import BaseService

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

_PATH = os.path.abspath(
    f"{settings.DATA_PATH}/.password-hash",
)


class AuthService(BaseService):
    hash: str | None = None

    def __init__(self) -> None:
        """Initialize AuthService. No repository dependencies required."""
        pass

    @classmethod
    def new(cls) -> "AuthService":
        """Create a new instance of AuthService. No repositories needed."""
        return cls()

    async def set_password(self, value: str) -> None:
        self.hash = pwd_context.hash(value)
        async with aiofiles.open(_PATH, mode="w") as f:
            await f.write(self.hash)

    async def confirm_password(self, value: str) -> bool:
        if not self.hash:
            with suppress(FileNotFoundError):
                async with aiofiles.open(_PATH) as f:
                    self.hash = await f.read()

        return pwd_context.verify(value, self.hash)


auth_svc = AuthService()
