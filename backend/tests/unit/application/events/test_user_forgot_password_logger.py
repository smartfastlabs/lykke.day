"""Unit tests for UserForgotPasswordLoggerHandler."""

from __future__ import annotations

from uuid import uuid4

import pytest

from lykke.application.events.handlers.user_forgot_password_logger import (
    UserForgotPasswordLoggerHandler,
)
from lykke.domain.entities import UserEntity
from lykke.domain.events.user_events import UserForgotPasswordEvent
from tests.support.dobles import create_read_only_repos_double


class _RepositoryFactory:
    def __init__(self, ro_repos: object) -> None:
        self._ro_repos = ro_repos

    def create(self, user: object) -> object:
        _ = user
        return self._ro_repos


@pytest.mark.asyncio
async def test_user_forgot_password_logger_handles_event() -> None:
    user_id = uuid4()
    handler = UserForgotPasswordLoggerHandler(
        user=UserEntity(id=user_id, email="test@example.com", hashed_password="!"),
        repository_factory=_RepositoryFactory(create_read_only_repos_double()),
    )

    event = UserForgotPasswordEvent(
        user_id=user_id,
        email="test@example.com",
        reset_token="token-123",
        request_origin="https://example.com",
        user_agent="pytest",
    )

    await handler.handle(event)


@pytest.mark.asyncio
async def test_user_forgot_password_logger_ignores_unrelated_event() -> None:
    user_id = uuid4()
    handler = UserForgotPasswordLoggerHandler(
        user=UserEntity(id=user_id, email="test@example.com", hashed_password="!"),
        repository_factory=_RepositoryFactory(create_read_only_repos_double()),
    )

    class _OtherEvent:
        pass

    await handler.handle(_OtherEvent())  # type: ignore[arg-type]
