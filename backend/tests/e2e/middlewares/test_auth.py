"""E2E tests for AuthMiddleware."""

import pytest
from dobles import InstanceDouble

from planned.app import app
from planned.core.exceptions import exceptions
from planned.infrastructure.utils.dates import get_current_datetime
from planned.presentation.middlewares.auth import AuthMiddleware


@pytest.mark.asyncio
async def test_dispatch_success():
    """Test successful middleware dispatch with valid session."""
    from uuid import uuid4
    obj = AuthMiddleware(app)
    url = InstanceDouble("starlette.datastructures.URL")
    url.path = "/some-url"
    request = InstanceDouble(
        "fastapi.Request",
        session={
            "user_uuid": str(uuid4()),
            "logged_in_at": str(get_current_datetime()),
        },
        url=url,
    )

    called: bool = False

    async def call_next(tmp):
        nonlocal called
        called = True
        assert tmp is request
        return "called"

    assert await obj.dispatch(request, call_next) == "called"
    assert called


@pytest.mark.asyncio
async def test_dispatch_not_logged_in():
    """Test middleware raises AuthorizationError when not logged in."""
    obj = AuthMiddleware(app)
    url = InstanceDouble("starlette.datastructures.URL")
    url.path = "/some-url"
    request = InstanceDouble(
        "fastapi.Request",
        session={},
        url=url,
    )

    with pytest.raises(exceptions.AuthorizationError):
        await obj.dispatch(request, None)


@pytest.mark.asyncio
async def test_dispatch_no_session():
    """Test middleware raises ServerError when session doesn't exist."""
    obj = AuthMiddleware(app)
    url = InstanceDouble("starlette.datastructures.URL")
    url.path = "/some-url"
    request = InstanceDouble(
        "fastapi.Request",
        url=url,
    )

    with pytest.raises(exceptions.ServerError):
        await obj.dispatch(request, None)


@pytest.mark.asyncio
async def test_dispatch_invalid_session():
    """Test middleware raises AuthorizationError with invalid session data."""
    obj = AuthMiddleware(app)
    url = InstanceDouble("starlette.datastructures.URL")
    url.path = "/some-url"
    request = InstanceDouble(
        "fastapi.Request",
        session={"logged_in_at": "Bob Barker"},
        url=url,
    )

    with pytest.raises(exceptions.AuthorizationError):
        await obj.dispatch(request, None)

