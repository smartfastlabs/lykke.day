import os
from typing import TypeVar

import aiofiles
import aiofiles.os

from planned.objects.base import BaseObject

T = TypeVar("T", bound=BaseObject)


async def read_directory(directory: str, model: type[T]) -> list[T]:
    """
    Read all *.json files in `directory` and deserialize them into instances of `model`.

    Assumes each file contains a single JSON object suitable for
    `model.model_validate_json(...)`.
    """
    abs_dir = os.path.abspath(directory)

    try:
        filenames = await aiofiles.os.listdir(abs_dir)
    except FileNotFoundError:
        return []

    json_files = [f for f in filenames if f.endswith(".json")]
    objects: list[T] = []

    for filename in json_files:
        full_path = os.path.join(abs_dir, filename)

        # aiofiles.os.path.isfile does not exist; must use sync call
        if not os.path.isfile(full_path):
            continue

        async with aiofiles.open(full_path) as f:
            contents = await f.read()

        try:
            obj = model.model_validate_json(
                contents,
                by_alias=False,
                by_name=True,
            )
            objects.append(obj)
        except Exception as e:
            print(f"Error loading object from {full_path}: {e}")
            continue

    return objects
