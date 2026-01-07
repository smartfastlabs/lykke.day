import secrets
from datetime import UTC, datetime
from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from fastapi.responses import RedirectResponse
from googleapiclient.discovery import build
from loguru import logger
from lykke.application.commands.calendar import RecordWebhookNotificationHandler

# TODO: Refactor OAuth flow to use commands/queries instead of direct repository access
# This is a complex OAuth callback flow that creates multiple entities in a single transaction.
# Consider creating a dedicated OAuthCallbackCommand to handle this flow properly.
from lykke.application.repositories import (
    AuthTokenRepositoryReadWriteProtocol,
    CalendarRepositoryReadWriteProtocol,
)
from lykke.core.constants import OAUTH_STATE_EXPIRY
from lykke.domain import data_objects
from lykke.domain.entities import CalendarEntity, UserEntity
from lykke.infrastructure.gateways.google import GoogleCalendarGateway
from lykke.presentation.workers.tasks import sync_single_calendar_task

from .dependencies.commands.calendar import get_record_webhook_notification_handler
from .dependencies.repositories import get_auth_token_repo, get_calendar_repo
from .dependencies.user import get_current_user

# Auth state storage (in memory for simplicity, use a database in production)
oauth_states = {}

router = APIRouter()


@router.get("/login")
async def google_login() -> RedirectResponse:
    state = secrets.token_urlsafe(16)
    authorization_url, state = GoogleCalendarGateway.get_flow(
        "login"
    ).authorization_url(
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
        AuthTokenRepositoryReadWriteProtocol, Depends(get_auth_token_repo)
    ],
    calendar_repo: Annotated[
        CalendarRepositoryReadWriteProtocol, Depends(get_calendar_repo)
    ],
) -> RedirectResponse:
    if not code or not verify_state(state, "login"):
        raise HTTPException(
            status_code=400,
            detail="Missing required parameters",
        )

    flow = GoogleCalendarGateway.get_flow("login")
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


@router.post("/webhook/{user_id}")
async def google_webhook(
    user_id: UUID,
    record_handler: Annotated[
        RecordWebhookNotificationHandler,
        Depends(get_record_webhook_notification_handler),
    ],
    x_goog_channel_id: Annotated[str | None, Header()] = None,
    x_goog_resource_id: Annotated[str | None, Header()] = None,
    x_goog_resource_state: Annotated[str | None, Header()] = None,
    x_goog_message_number: Annotated[str | None, Header()] = None,
) -> Response:
    """Webhook endpoint for Google Calendar push notifications.

    Google sends notifications to this endpoint when calendar events change.
    The notification includes headers with channel and resource information.
    The actual sync is performed asynchronously via a background task.

    Args:
        user_id: The user ID extracted from the webhook URL.

    Headers:
        X-Goog-Channel-ID: The channel ID from the watch request.
        X-Goog-Resource-ID: An opaque ID identifying the watched resource.
        X-Goog-Resource-State: The type of change (sync, exists, not_exists).
        X-Goog-Message-Number: Incrementing message number.

    Returns:
        Empty 200 response to acknowledge receipt.
    """
    logger.info(
        f"Received Google webhook for user {user_id}: channel_id={x_goog_channel_id}, "
        f"resource_id={x_goog_resource_id}, state={x_goog_resource_state}, "
        f"message_number={x_goog_message_number}"
    )

    if not x_goog_channel_id:
        return Response(status_code=200)

    # Handle sync state (initial verification from Google)
    if x_goog_resource_state == "sync":
        logger.info("Received sync verification from Google")
        return Response(status_code=200)

    # Look up calendar by subscription info
    calendar = await record_handler.run(
        subscription_id=x_goog_channel_id,
        resource_id=x_goog_resource_id,
    )

    if not calendar:
        logger.warning(
            f"No calendar found for user={user_id}, channel_id={x_goog_channel_id}"
        )
        return Response(status_code=200)

    # Schedule background task to sync the calendar
    await sync_single_calendar_task.kiq(user_id=user_id, calendar_id=calendar.id)
    logger.info(f"Scheduled sync task for calendar {calendar.id}")

    return Response(status_code=200)
