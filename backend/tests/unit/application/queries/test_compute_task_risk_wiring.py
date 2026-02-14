"""Tests for ComputeTaskRiskHandler dependency wiring."""

# Pylint runs outside Poetry env in-editor; suppress import-resolution noise.
# pylint: disable=import-error

from __future__ import annotations

from uuid import uuid4

import pytest
from dobles import InstanceDouble, allow

from lykke.application.queries.compute_task_risk import ComputeTaskRiskHandler
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory
from lykke.domain.entities import UserEntity
from tests.support.dobles import create_read_only_repos_double


@pytest.mark.asyncio
async def test_handler_initializes_without_legacy_dependencies() -> None:
    """Ensure repository wiring works with postponed annotations.

    This guards against dependency wiring regressions with postponed annotations.
    """

    user = UserEntity(id=uuid4(), email="test@example.com", hashed_password="!")
    ro_repos = create_read_only_repos_double()
    ro_factory = InstanceDouble(
        f"{ReadOnlyRepositoryFactory.__module__}.{ReadOnlyRepositoryFactory.__name__}"
    )
    allow(ro_factory).create.and_return(ro_repos)

    handler = ComputeTaskRiskHandler(user=user, repository_factory=ro_factory)

    assert handler is not None

