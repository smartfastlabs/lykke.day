"""Unit tests for ListBasePersonalitiesHandler."""

from uuid import uuid4

import pytest

from lykke.application.queries.list_base_personalities import (
    ListBasePersonalitiesHandler,
    ListBasePersonalitiesQuery,
)
from tests.support.dobles import create_read_only_repos_double


@pytest.mark.asyncio
async def test_list_base_personalities_includes_defaults() -> None:
    """Ensure base personalities list includes expected slugs."""
    handler = ListBasePersonalitiesHandler(create_read_only_repos_double(), uuid4())

    result = await handler.handle(ListBasePersonalitiesQuery())

    slugs = {personality.slug for personality in result}
    assert "default" in slugs
    assert "calm_coach" in slugs
    assert "direct" in slugs
    assert "cheerful" in slugs
    assert "analytical" in slugs
