import contextlib
import datetime
import os
from pathlib import Path
from typing import Generic, TypeVar

import aiofiles
import aiofiles.os

from planned import settings
from planned.objects.base import BaseObject
from planned.utils.json import read_directory

ObjectType = TypeVar(
    "ObjectType",
    bound=BaseObject,
)


class BaseRepository(Generic[ObjectType]):
    Object: type[ObjectType]
    _prefix: str

    def parse_json(self, data: dict) -> ObjectType:
        return self.Object.model_validate_json(data, by_alias=False, by_name=True)

    def to_json(self, obj: ObjectType) -> dict:
        return obj.model_dump_json(indent=4, by_alias=False)

    async def get(self, id: str) -> ObjectType:
        async with aiofiles.open(self._get_file_path(id)) as f:
            contents = await f.read()

        return self.parse_json(contents)

    async def put(self, obj, key: str | None = None):
        path = Path(self._get_file_path(key or obj))

        # Async mkdir - creates parent directories
        await aiofiles.os.makedirs(path.parent, exist_ok=True)

        async with aiofiles.open(path, mode="w") as f:
            await f.write(self.to_json(obj))

        return obj

    async def search(self, date: datetime.date | None = None):
        if date is None:
            return await read_directory(
                os.path.abspath(f"{settings.DATA_PATH}/{self._prefix}"),
                self.Object,
            )

        if hasattr(self.Object, "date"):
            return await read_directory(
                f"{settings.DATA_PATH}/{self._prefix}/{date}",
                self.Object,
            )

        raise Exception(f"You can't search {self.Object.__name__}s by date!")

    async def delete(self, id: str) -> None:
        try:
            await aiofiles.os.remove(self._get_file_path(temp))
        except FileNotFoundError:
            pass

    async def delete_by_date(self, date=datetime.date) -> None:
        with contextlib.suppress(FileNotFoundError):
            await aiofiles.os.rmdir(
                os.path.abspath(f"{settings.DATA_PATH}/{self._prefix}/{date}"),
            )

    def _get_object_path(self, temp: str | ObjectType) -> str:
        if isinstance(temp, self.Object):
            if hasattr(self.Object, "date"):
                return f"{self._prefix}/{temp.date}/{temp.id}"
            return f"{self._prefix}/{temp.id}"

        return f"{self._prefix}/{temp}"

    def _get_file_path(self, temp: str | ObjectType) -> str:
        return os.path.abspath(f"{settings.DATA_PATH}/{self._get_object_path(temp)}.json")
