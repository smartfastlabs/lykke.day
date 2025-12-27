import json
import os
from typing import Generic, TypeVar

import aiofiles

from planned import exceptions, settings
from planned.objects.base import BaseObject
from planned.utils.json import read_directory

from .repository import BaseRepository

ConfigObjectType = TypeVar(
    "ConfigObjectType",
    bound=BaseObject,
)


class BaseConfigRepository(BaseRepository[ConfigObjectType]):
    Object: type[ConfigObjectType]
    _prefix: str

    def get_object(self, data: dict) -> ConfigObjectType:
        return self.Object.model_validate(data, by_alias=False, by_name=True)

    async def get(self, key: str) -> ConfigObjectType:
        path: str = self._get_file_path(key)
        try:
            async with aiofiles.open(path) as f:
                contents = await f.read()
        except FileNotFoundError:
            raise exceptions.NotFoundError(
                f"`{self.Object.__name__}` with key '{key}' not found. Path was '{path}'.",
            )

        data = json.loads(contents)
        data["id"] = key
        return self.get_object(data)

    async def all(self) -> list[ConfigObjectType]:
        return await read_directory(
            f"{settings.DATA_PATH}/{self._prefix}",
            self.Object,
        )

    def _get_file_path(self, key: str) -> str:
        return os.path.abspath(f"{settings.DATA_PATH}/{self._prefix}/{key}.json")
