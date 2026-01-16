import hmac
import secrets
from datetime import UTC, datetime
from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from fastapi.responses import RedirectResponse
from googleapiclient.discovery import build
from loguru import logger

# TODO: Refactor OAuth flow to use commands/queries instead of direct repository access
# This is a complex OAuth callback flow that creates multiple entities in a single transaction.
# Consider creating a dedicated OAuthCallbackCommand to handle this flow properly.
from lykke.application.repositories import (
    AuthTokenRepositoryReadWriteProtocol,
    CalendarRepositoryReadOnlyProtocol,
    CalendarRepositoryReadWriteProtocol,
)
from lykke.core.constants import OAUTH_STATE_EXPIRY
from lykke.domain import data_objects
from lykke.domain.entities import CalendarEntity, UserEntity
from lykke.domain.value_objects.query import AuthTokenQuery, CalendarQuery
from lykke.infrastructure.gateways.google import GoogleCalendarGateway
from lykke.presentation.workers.tasks import sync_single_calendar_task

from .dependencies.repositories import (
    get_auth_token_repo,
    get_calendar_repo,
    get_calendar_repo_by_user_id,
)
from .dependencies.user import get_current_user

# Auth state storage (in memory for simplicity, use a database in production)
oauth_states = {}

router = APIRouter()


@router.get("/login")
async def google_login(
    auth_token_id: UUID | None = None,
) -> RedirectResponse:
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
    # If auth_token_id is provided, we're re-authenticating a specific account
    oauth_states[state] = {
        "expiry": datetime.now(UTC) + OAUTH_STATE_EXPIRY,
        "action": "login",
        "auth_token_id": str(auth_token_id) if auth_token_id else None,
    }

    return RedirectResponse(authorization_url)


def verify_state(
    state: str,
    expected_action: str,
) -> dict:
    """
    Verify the state parameter and check if it matches the expected action.
    Returns the state data if valid.
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

    return state_data


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
    if not code:
        raise HTTPException(
            status_code=400,
            detail="Missing required parameters",
        )

    state_data = verify_state(state, "login")
    auth_token_id_from_state = state_data.get("auth_token_id")

    flow = GoogleCalendarGateway.get_flow("login")
    flow.fetch_token(code=code)

    # First, get the calendars from Google to understand which account this is
    service = build(
        "calendar",
        "v3",
        credentials=flow.credentials,
    )
    calendar_list = service.calendarList().list().execute()
    google_platform_ids = {cal["id"] for cal in calendar_list.get("items", [])}

    # Determine which auth token to update/create
    existing_auth_token = None

    if auth_token_id_from_state:
        # If we have a specific auth_token_id from state, use that (re-auth from calendar page)
        try:
            existing_auth_token = await auth_token_repo.get(UUID(auth_token_id_from_state))
            # Verify it belongs to this user
            if existing_auth_token.user_id != user.id:
                raise HTTPException(
                    status_code=403,
                    detail="Auth token does not belong to user",
                )
            logger.info(
                f"Re-authenticating specific auth token {existing_auth_token.id} "
                f"for user {user.id}"
            )
        except Exception as e:
            logger.warning(
                f"Could not find auth token {auth_token_id_from_state} from state: {e}"
            )
            # Fall through to matching logic

    if not existing_auth_token:
        # Try to match by finding calendars with matching platform_ids
        # This handles the case where we're re-authenticating but don't have auth_token_id
        if google_platform_ids:
            # Find existing calendars that match these platform_ids
            existing_calendars = await calendar_repo.search(
                CalendarQuery()  # Will get all user's calendars due to user scoping
            )
            matching_calendar = next(
                (
                    cal
                    for cal in existing_calendars
                    if cal.platform_id in google_platform_ids and cal.platform == "google"
                ),
                None,
            )

            if matching_calendar:
                # Found a matching calendar, use its auth_token_id
                try:
                    existing_auth_token = await auth_token_repo.get(
                        matching_calendar.auth_token_id
                    )
                    logger.info(
                        f"Matched existing auth token {existing_auth_token.id} "
                        f"via calendar {matching_calendar.id} for user {user.id}"
                    )
                except Exception as e:
                    logger.warning(f"Could not find auth token {matching_calendar.auth_token_id}: {e}")

    # Create or update the auth token
    auth_token_data = data_objects.AuthToken(
        user_id=user.id,
        client_id=flow.credentials.client_id,
        client_secret=flow.credentials.client_secret,
        expires_at=flow.credentials.expiry,
        platform="google",
        refresh_token=flow.credentials.refresh_token,
        scopes=flow.credentials.scopes,
        token=flow.credentials.token,
        token_uri=flow.credentials.token_uri,
    )

    # If an existing token was found, update it in place by setting its id
    if existing_auth_token:
        auth_token_data.id = existing_auth_token.id
        logger.info(f"Updating existing auth token {existing_auth_token.id} for user {user.id}")
    else:
        logger.info(f"Creating new auth token for user {user.id}")

    auth_token: data_objects.AuthToken = await auth_token_repo.put(auth_token_data)

    # Process each calendar from Google
    # This will create new calendars or update existing ones based on platform_id
    for google_calendar in calendar_list.get("items", []):
        platform_id = google_calendar["id"]

        # Check if a calendar with this platform_id already exists
        existing_calendar = await calendar_repo.search_one_or_none(
            CalendarQuery(platform_id=platform_id)
        )

        calendar_data = CalendarEntity(
            user_id=user.id,
            name=google_calendar["summary"],
            platform="google",
            platform_id=platform_id,
            auth_token_id=auth_token.id,
        )

        # If an existing calendar was found, update it in place by preserving its id
        # and any sync subscription settings
        if existing_calendar:
            calendar_data.id = existing_calendar.id
            # Preserve sync subscription if it exists
            if existing_calendar.sync_subscription:
                calendar_data.sync_subscription = existing_calendar.sync_subscription
                calendar_data.sync_subscription_id = existing_calendar.sync_subscription_id
            # Preserve default_event_category if it exists
            if existing_calendar.default_event_category:
                calendar_data.default_event_category = existing_calendar.default_event_category
            logger.info(
                f"Updating existing calendar {existing_calendar.id} "
                f"(platform_id: {platform_id}) for user {user.id}"
            )
        else:
            logger.info(
                f"Creating new calendar (platform_id: {platform_id}) for user {user.id}"
            )

        await calendar_repo.put(calendar_data)

    # Clean up state
    if state in oauth_states:
        del oauth_states[state]

    return RedirectResponse(url="/app")


@router.post("/webhook/{user_id}/{calendar_id}")
async def google_webhook(
    user_id: UUID,
    calendar_id: UUID,
    calendar_repo: Annotated[
        CalendarRepositoryReadOnlyProtocol, Depends(get_calendar_repo_by_user_id)
    ],
    x_goog_channel_token: Annotated[str | None, Header()] = None,
    x_goog_resource_state: Annotated[str | None, Header()] = None,
) -> Response:
    """Webhook endpoint for Google Calendar push notifications.

    Google sends notifications to this endpoint when calendar events change.
    The actual sync is performed asynchronously via a background task.

    Args:
        user_id: The user ID extracted from the webhook URL.
        calendar_id: The calendar ID extracted from the webhook URL.

    Headers:
        X-Goog-Channel-Token: Secret token for webhook verification.
        X-Goog-Resource-State: The type of change (sync, exists, not_exists).

    Returns:
        Empty 200 response to acknowledge receipt.
    """
    logger.info(
        f"Received Google webhook for user {user_id}, calendar {calendar_id}, "
        f"state={x_goog_resource_state}"
    )

    # Look up the calendar to get the expected token
    try:
        calendar = await calendar_repo.get(calendar_id)
    except Exception:
        logger.warning(f"Calendar {calendar_id} not found for user {user_id}")
        return Response(status_code=200)

    if not calendar.sync_subscription:
        logger.warning(f"Calendar {calendar_id} has no sync subscription")
        return Response(status_code=200)

    if not x_goog_channel_token:
        logger.warning(f"Missing token for calendar {calendar_id}")
        return Response(status_code=200)

    client_state = calendar.sync_subscription.client_state
    if client_state is None:
        logger.warning(f"Missing client_state for calendar {calendar_id}")
        return Response(status_code=200)

    if not hmac.compare_digest(client_state, x_goog_channel_token):
        logger.warning(f"Invalid token for calendar {calendar_id}")
        return Response(status_code=200)

    if x_goog_resource_state == "sync":
        logger.info("Received sync verification from Google, triggering initial sync")

    # Schedule background task to sync the calendar (initial + incremental)
    await sync_single_calendar_task.kiq(user_id=user_id, calendar_id=calendar_id)
    logger.info(f"Scheduled sync task for calendar {calendar_id}")

    return Response(status_code=200)
        X-Goog-Channel-Token: Secret token for webhook verification.
        X-Goog-Resource-State: The type of change (sync, exists, not_exists).

    Returns:
        Empty 200 response to acknowledge receipt.
    """
    logger.info(
        f"Received Google webhook for user {user_id}, calendar {calendar_id}, "
        f"state={x_goog_resource_state}"
    )

    # Look up the calendar to get the expected token
    try:
        calendar = await calendar_repo.get(calendar_id)
    except Exception:
        logger.warning(f"Calendar {calendar_id} not found for user {user_id}")
        return Response(status_code=200)

    if not calendar.sync_subscription:
        logger.warning(f"Calendar {calendar_id} has no sync subscription")
        return Response(status_code=200)

    if not x_goog_channel_token:
        logger.warning(f"Missing token for calendar {calendar_id}")
        return Response(status_code=200)

    client_state = calendar.sync_subscription.client_state
    if client_state is None:
        logger.warning(f"Missing client_state for calendar {calendar_id}")
        return Response(status_code=200)

    if not hmac.compare_digest(client_state, x_goog_channel_token):
        logger.warning(f"Invalid token for calendar {calendar_id}")
        return Response(status_code=200)

    if x_goog_resource_state == "sync":
        logger.info("Received sync verification from Google, triggering initial sync")

    # Schedule background task to sync the calendar (initial + incremental)
    await sync_single_calendar_task.kiq(user_id=user_id, calendar_id=calendar_id)
    logger.info(f"Scheduled sync task for calendar {calendar_id}")

    return Response(status_code=200)
