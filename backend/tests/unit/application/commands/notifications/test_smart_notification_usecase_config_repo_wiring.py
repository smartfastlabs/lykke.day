"""Wiring tests for SmartNotificationHandler LLM dependencies."""

# Pylint runs outside Poetry env in-editor; suppress import-resolution noise.
# pylint: disable=import-error

from __future__ import annotations

from uuid import uuid4

import pytest
from dobles import InstanceDouble, allow

from lykke.application.commands.notifications.evaluate_smart_notification import (
    SmartNotificationHandler,
)
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory, UnitOfWorkFactory
from lykke.domain.entities import UserEntity
from tests.support.dobles import create_read_only_repos_double, create_uow_double


@pytest.mark.asyncio
async def test_smart_notification_handler_has_usecase_config_repo() -> None:
    """Regression test for AttributeError: missing usecase_config_ro_repo.
    """

    user = UserEntity(id=uuid4(), email="test@example.com", hashed_password="!")
    ro_repos = create_read_only_repos_double()
    ro_factory = InstanceDouble(
        f"{ReadOnlyRepositoryFactory.__module__}.{ReadOnlyRepositoryFactory.__name__}"
    )
    allow(ro_factory).create.and_return(ro_repos)

    uow = create_uow_double()
    uow_factory = InstanceDouble(
        f"{UnitOfWorkFactory.__module__}.{UnitOfWorkFactory.__name__}"
    )
    allow(uow_factory).create.and_return(uow)

    handler = SmartNotificationHandler(
        user=user,
        uow_factory=uow_factory,
        repository_factory=ro_factory,
    )

    # Wired via annotated dependency on SmartNotificationHandler.
    assert handler.usecase_config_ro_repo is ro_repos.usecase_config_ro_repo

