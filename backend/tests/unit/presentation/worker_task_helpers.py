"""Shared helpers for worker task unit tests."""

from __future__ import annotations

from datetime import time
from typing import Any, Protocol
from uuid import UUID, uuid4

from dobles import InstanceDouble, allow

from lykke.domain import value_objects
from lykke.domain.entities import UserEntity
from tests.support.dobles import create_user_repo_double


class TaskProtocol(Protocol):
    async def kiq(self, **kwargs: Any) -> None: ...


class HandlerProtocol(Protocol):
    user: UserEntity

    async def handle(self, command: object) -> None: ...


class GatewayProtocol(Protocol):
    async def publish_to_user_channel(
        self,
        user_id: UUID,
        channel_type: str,
        message: dict[str, Any],
    ) -> None: ...

    async def close(self) -> None: ...


def _protocol_path(protocol_class: type) -> str:
    return f"{protocol_class.__module__}.{protocol_class.__name__}"


def create_task_recorder() -> tuple[InstanceDouble, list[dict[str, Any]]]:
    calls: list[dict[str, Any]] = []
    task = InstanceDouble(_protocol_path(TaskProtocol))

    async def kiq(**kwargs: Any) -> None:
        calls.append(kwargs)

    task.kiq = kiq
    return task, calls


def create_handler_recorder(
    user: UserEntity | None = None,
) -> tuple[InstanceDouble, list[object]]:
    calls: list[object] = []
    handler = InstanceDouble(_protocol_path(HandlerProtocol))
    handler.user = user or build_user(uuid4())

    async def handle(command: object) -> None:
        calls.append(command)

    handler.handle = handle
    return handler, calls


def create_gateway_recorder() -> tuple[InstanceDouble, dict[str, bool]]:
    state = {"closed": False}
    gateway = InstanceDouble(_protocol_path(GatewayProtocol))

    async def publish_to_user_channel(
        user_id: UUID,
        channel_type: str,
        message: dict[str, Any],
    ) -> None:
        # No-op, but allows tests to assert it was called via dobles stubs if needed.
        _ = (user_id, channel_type, message)

    gateway.publish_to_user_channel = publish_to_user_channel

    async def close() -> None:
        state["closed"] = True

    gateway.close = close
    return gateway, state


def create_user_repo(users: list[UserEntity]) -> InstanceDouble:
    repo = create_user_repo_double()
    allow(repo).all.and_return(users)
    allow(repo).get.and_return(users[0])
    return repo


def build_user(
    user_id: UUID,
    *,
    llm_provider: value_objects.LLMProvider | None = None,
    morning_overview_time: time | None = None,
    timezone: str | None = None,
) -> UserEntity:
    return UserEntity(
        id=user_id,
        email="user@example.com",
        hashed_password="hash",
        settings=value_objects.UserSetting(
            llm_provider=llm_provider,
            morning_overview_time=morning_overview_time,
            timezone=timezone,
        ),
    )
