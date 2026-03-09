"""Unit tests for google OAuth state helpers."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from lykke.presentation.api.routers.google import (
    _parse_auth_token_id_from_state,
    verify_state,
)


@pytest.mark.asyncio
async def test_verify_state_returns_matching_action_payload() -> None:
    storage_gateway = AsyncMock()
    storage_gateway.get_json.return_value = {"action": "login", "auth_token_id": None}

    result = await verify_state(storage_gateway, "state-1", "login")

    assert result["action"] == "login"
    storage_gateway.delete.assert_not_called()


@pytest.mark.asyncio
async def test_verify_state_rejects_wrong_action_and_consumes_state() -> None:
    storage_gateway = AsyncMock()
    storage_gateway.get_json.return_value = {"action": "refresh"}

    with pytest.raises(HTTPException) as exc:
        await verify_state(storage_gateway, "state-2", "login")

    assert exc.value.status_code == 400
    storage_gateway.delete.assert_awaited_once()


def test_parse_auth_token_id_from_state_accepts_uuid_string() -> None:
    token_id = uuid4()
    parsed = _parse_auth_token_id_from_state({"auth_token_id": str(token_id)})
    assert parsed == token_id


def test_parse_auth_token_id_from_state_rejects_invalid_value() -> None:
    with pytest.raises(HTTPException) as exc:
        _parse_auth_token_id_from_state({"auth_token_id": 123})
    assert exc.value.status_code == 400
