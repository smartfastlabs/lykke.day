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
async def test_handler_wires_audit_log_ro_repo_from_annotations() -> None:
    """Ensure repository wiring works with postponed annotations.

    This guards against the common pitfall where injected dependency types are only
    imported under TYPE_CHECKING, causing BaseHandler to be unable to resolve the
    annotation string at runtime.
    """

    user = UserEntity(id=uuid4(), email="test@example.com", hashed_password="!")
    ro_repos = create_read_only_repos_double()
    ro_factory = InstanceDouble(
        f"{ReadOnlyRepositoryFactory.__module__}.{ReadOnlyRepositoryFactory.__name__}"
    )
    allow(ro_factory).create.and_return(ro_repos)

    handler = ComputeTaskRiskHandler(user=user, repository_factory=ro_factory)

    assert handler.audit_log_ro_repo is ro_repos.audit_log_ro_repo

