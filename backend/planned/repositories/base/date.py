import asyncio
import contextlib
import datetime
import json
import os
import shutil
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Generic, TypeVar

import aiofiles
import aiofiles.os
from blinker import Signal

from planned import settings
from planned.objects.base import BaseDateObject
from planned.utils.json import read_directory

ObjectType = TypeVar(
    "ObjectType",
    bound=BaseDateObject,
)


async def delete_dir(path: str) -> None:
    abs_path = os.path.abspath(path)

    # swallow "doesn't exist" errors
    with contextlib.suppress(FileNotFoundError):
        await asyncio.to_thread(shutil.rmtree, abs_path)


class BaseDateRepository(Generic[ObjectType]):
    Object: type[ObjectType]
    _prefix: str
    signal_source: Signal

    def __init__(self) -> None:
        self.signal_source = Signal()

    def get_object(self, data: dict) -> ObjectType:
        return self.Object.model_validate(data, by_alias=False, by_name=True)

    def to_json(self, obj: ObjectType) -> str:
        return obj.model_dump_json(indent=4, by_alias=False)

    async def get(self, date: datetime.date, key: str) -> ObjectType:
        async with aiofiles.open(self._get_file_path(date, key)) as f:
            contents = await f.read()

        data = json.loads(contents)
        data["id"] = key
        return self.get_object(data)

    async def put(self, obj: ObjectType) -> ObjectType:
        path = Path(self._get_file_path(obj.date, obj.id))

        await aiofiles.os.makedirs(path.parent, exist_ok=True)

        async with aiofiles.open(path, mode="w") as f:
            await f.write(self.to_json(obj))

        await self.signal_source.send_async("put", obj=obj)
        return obj

    async def search(self, date: datetime.date) -> list[ObjectType]:
        temp: list[ObjectType] = await read_directory(
            f"{settings.DATA_PATH}/dates/{date}/{self._prefix}",
            self.Object,
        )

        return temp

    async def delete(self, obj: ObjectType) -> None:
        with contextlib.suppress(FileExistsError):
            await aiofiles.os.remove(self._get_file_path(obj.date, obj.id))

        await self.signal_source.send_async("delete", obj=obj)

    async def delete_by_date(
        self,
        date: datetime.date | str,
        filter_by: Callable[[ObjectType], bool] | None = None,
    ) -> None:
        dir_path = os.path.abspath(
            f"{settings.DATA_PATH}/dates/{date}/{self._prefix}",
        )

        if filter_by is None:
            await delete_dir(dir_path)
            return

        if not os.path.exists(dir_path):
            return

        async def maybe_delete(filepath: str) -> None:
            async with aiofiles.open(filepath) as f:
                data = json.loads(await f.read())
            obj = self.get_object(data)
            if filter_by(obj):
                await aiofiles.os.remove(filepath)

        await asyncio.gather(
            *[
                maybe_delete(os.path.join(dir_path, filename))
                for filename in os.listdir(dir_path)
                if os.path.isfile(os.path.join(dir_path, filename))
            ]
        )

    def _get_file_path(self, date: datetime.date, key: str) -> str:
        return os.path.abspath(
            f"{settings.DATA_PATH}/dates/{date}/{self._prefix}/{key}.json"
        )
