import json
import os
from typing import Generic, TypeVar

import aiofiles

from planned import exceptions, settings
from planned.objects.base import BaseObject
from planned.utils.json import read_directory

ObjectType = TypeVar(
    "ObjectType",
    bound=BaseObject,
)


class BaseConfigRepository(Generic[ObjectType]):
    Object: type[ObjectType]
    _prefix: str

    def get_object(self, data: dict) -> ObjectType:
        return self.Object.model_validate(data, by_alias=False, by_name=True)

    async def get(self, key: str) -> ObjectType:
        try:
            async with aiofiles.open(self._get_file_path(key)) as f:
                contents = await f.read()
        except FileNotFoundError:
            raise exceptions.NotFoundError(
                f"`{self.__class__.__name__}` with key '{key}' not found",
            )

        data = json.loads(contents)
        data["id"] = key
        return self.get_object(data)

    async def all(self) -> list[ObjectType]:
        return await read_directory(
            f"{settings.DATA_PATH}/{self._prefix}",
            self.Object,
        )

    def _get_file_path(self, key: str) -> str:
        return os.path.abspath(f"{settings.DATA_PATH}/{self._prefix}/{key}.json")
