import contextlib
from pathlib import Path
from typing import Generic

import aiofiles
import aiofiles.os

from planned import exceptions

from .config import BaseConfigRepository, ObjectType


class BaseCrudRepository(BaseConfigRepository[ObjectType], Generic[ObjectType]):
    def to_json(self, obj: ObjectType) -> str:
        return obj.model_dump_json(indent=4, by_alias=False)

    async def put(self, obj: ObjectType) -> ObjectType:
        path = Path(self._get_file_path(obj.id))

        exists = await aiofiles.os.path.exists(path)

        await aiofiles.os.makedirs(path.parent, exist_ok=True)

        async with aiofiles.open(path, mode="w") as f:
            await f.write(self.to_json(obj))

        event_type = "update" if exists else "create"
        await self.signal_source.send_async(event_type, obj=obj)
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

        await self.signal_source.send_async("delete", obj=obj)
