"""Unit tests for ListBasePersonalitiesHandler."""

from uuid import uuid4

import pytest

from lykke.application.queries.list_base_personalities import (
    ListBasePersonalitiesHandler,
    ListBasePersonalitiesQuery,
)
from lykke.domain.entities import UserEntity
from tests.support.dobles import create_read_only_repos_double


class _RepositoryFactory:
    def __init__(self, ro_repos: object) -> None:
        self._ro_repos = ro_repos

    def create(self, user: object) -> object:
        _ = user
        return self._ro_repos


@pytest.mark.asyncio
async def test_list_base_personalities_includes_defaults() -> None:
    """Ensure base personalities list includes expected slugs."""
    handler = ListBasePersonalitiesHandler(
        user=UserEntity(id=uuid4(), email="test@example.com", hashed_password="!"),
        repository_factory=_RepositoryFactory(create_read_only_repos_double()),
    )

    result = await handler.handle(ListBasePersonalitiesQuery())

    slugs = {personality.slug for personality in result}
    assert "default" in slugs
    assert "calm_coach" in slugs
    assert "direct" in slugs
    assert "cheerful" in slugs
    assert "analytical" in slugs
