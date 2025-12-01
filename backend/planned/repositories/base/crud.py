import contextlib
from pathlib import Path
from typing import Generic

import aiofiles
import aiofiles.os

from .config import BaseConfigRepository, ObjectType


class BaseCrudRepository(BaseConfigRepository[ObjectType], Generic[ObjectType]):
    def to_json(self, obj: ObjectType) -> str:
        return obj.model_dump_json(indent=4, by_alias=False)

    async def put(self, obj: ObjectType, key: str | None = None) -> ObjectType:
        path = Path(self._get_file_path(key or obj.id))

        # Async mkdir - creates parent directories
        await aiofiles.os.makedirs(path.parent, exist_ok=True)

        async with aiofiles.open(path, mode="w") as f:
            await f.write(self.to_json(obj))

        return obj

    async def delete(self, key: str) -> None:
        with contextlib.suppress(FileExistsError):
            await aiofiles.os.remove(self._get_file_path(key))
