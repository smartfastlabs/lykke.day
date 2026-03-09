"""E2E tests for usecase config routes."""

import pytest


@pytest.mark.asyncio
async def test_user_status_checkin_preview_returns_none_without_llm_provider(
    authenticated_client,
) -> None:
    """Preview endpoint should return null when user has no LLM provider."""
    client, _ = await authenticated_client()

    response = client.post("/usecase-configs/user_status_use_case/checkin-preview")

    assert response.status_code == 200
    assert response.json() is None
