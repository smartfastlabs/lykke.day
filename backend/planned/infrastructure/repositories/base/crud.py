import contextlib
from pathlib import Path
from typing import Literal

import aiofiles
import aiofiles.os

from planned.core.exceptions import exceptions

from .config import BaseConfigRepository, ConfigObjectType
from .repository import ChangeEvent


class BaseCrudRepository(BaseConfigRepository[ConfigObjectType]):
    def to_json(self, obj: ConfigObjectType) -> str:
        return obj.model_dump_json(indent=4, by_alias=False)

    async def put(self, obj: ConfigObjectType) -> ConfigObjectType:
        path = Path(self._get_file_path(obj.id))

        exists = await aiofiles.os.path.exists(path)

        await aiofiles.os.makedirs(path.parent, exist_ok=True)

        async with aiofiles.open(path, mode="w") as f:
            await f.write(self.to_json(obj))

        event_type: Literal["create", "update"] = "update" if exists else "create"
        event = ChangeEvent[ConfigObjectType](type=event_type, value=obj)
        await self.signal_source.send_async("change", event=event)
        return obj

    async def delete(self, key: str) -> None:
        try:
            obj = await self.get(key)
        except exceptions.NotFoundError:
            with contextlib.suppress(FileNotFoundError):
                await aiofiles.os.remove(self._get_file_path(key))
            return

        with contextlib.suppress(FileNotFoundError):
            await aiofiles.os.remove(self._get_file_path(key))

        event = ChangeEvent[ConfigObjectType](type="delete", value=obj)
        await self.signal_source.send_async("change", event=event)
