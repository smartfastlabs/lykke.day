import secrets
from datetime import UTC, datetime
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from googleapiclient.discovery import build

# TODO: Refactor OAuth flow to use commands/queries instead of direct repository access
# This is a complex OAuth callback flow that creates multiple entities in a single transaction.
# Consider creating a dedicated OAuthCallbackCommand to handle this flow properly.
from planned.application.repositories import (
    AuthTokenRepositoryProtocol,
    CalendarRepositoryProtocol,
)
from planned.core.constants import OAUTH_STATE_EXPIRY
from planned.domain.entities import CalendarEntity, UserEntity
from planned.infrastructure import data_objects
from planned.infrastructure.gateways.google import get_flow

from .dependencies.repositories import get_auth_token_repo, get_calendar_repo
from .dependencies.user import get_current_user

# Auth state storage (in memory for simplicity, use a database in production)
oauth_states = {}

router = APIRouter()


@router.get("/login")
async def google_login() -> RedirectResponse:
    state = secrets.token_urlsafe(16)
    authorization_url, state = get_flow("login").authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=state,
        prompt="consent",
    )

    # Store state for validation on callback
    oauth_states[state] = {
        "expiry": datetime.now(UTC) + OAUTH_STATE_EXPIRY,
        "action": "login",
    }

    return RedirectResponse(authorization_url)


def verify_state(
    state: str,
    expected_action: str,
) -> bool:
    """
    Verify the state parameter and check if it matches the expected action.
    """

    if state not in oauth_states:
        raise HTTPException(
            status_code=400,
            detail="Invalid state parameter",
        )

    state_data = oauth_states[state]
    if datetime.now(UTC) > cast("datetime", state_data["expiry"]):
        del oauth_states[state]
        raise HTTPException(
            status_code=400,
            detail="State parameter expired",
        )
    elif state_data["action"] != expected_action:
        del oauth_states[state]
        raise HTTPException(
            status_code=400,
            detail="Invalid action parameter",
        )

    return True


@router.get("/callback/login")
async def google_login_callback(
    state: str,
    code: str,
    user: Annotated[UserEntity, Depends(get_current_user)],
    auth_token_repo: Annotated[
        AuthTokenRepositoryProtocol, Depends(get_auth_token_repo)
    ],
    calendar_repo: Annotated[CalendarRepositoryProtocol, Depends(get_calendar_repo)],
) -> RedirectResponse:
    if not code or not verify_state(state, "login"):
        raise HTTPException(
            status_code=400,
            detail="Missing required parameters",
        )

    flow = get_flow("login")
    flow.fetch_token(code=code)

    auth_token: data_objects.AuthToken = await auth_token_repo.put(
        data_objects.AuthToken(
            user_id=user.id,
            client_id=flow.credentials.client_id,
            client_secret=flow.credentials.client_secret,
            expires_at=flow.credentials.expiry,
            platform="google",
            refresh_token=flow.credentials.refresh_token,
            scopes=flow.credentials.scopes,
            token=flow.credentials.token,
            token_uri=flow.credentials.token_uri,
        ),
    )

    service = build(
        "calendar",
        "v3",
        credentials=flow.credentials,
    )
    calendar_list = service.calendarList().list().execute()

    for calendar in calendar_list.get("items", []):
        await calendar_repo.put(
            CalendarEntity(
                user_id=user.id,
                name=calendar["summary"],
                platform="google",
                platform_id=calendar["id"],
                auth_token_id=auth_token.id,
            ),
        )

    return RedirectResponse(url="/app")
