import secrets
from datetime import UTC, datetime
from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from loguru import logger

from lykke.application.commands.google import (
    HandleGoogleLoginCallbackCommand,
    HandleGoogleLoginCallbackHandler,
)
from lykke.application.queries.google import (
    VerifyGoogleWebhookHandler,
    VerifyGoogleWebhookQuery,
)
from lykke.application.unit_of_work import ReadOnlyRepositoryFactory
from lykke.core.constants import OAUTH_STATE_EXPIRY
from lykke.domain.entities import UserEntity
from lykke.infrastructure.gateways.google import GoogleCalendarGateway
from lykke.infrastructure.repositories import UserRepository
from lykke.presentation.handler_factory import (
    CommandHandlerFactory,
    QueryHandlerFactory,
)
from lykke.presentation.webhook_relay import webhook_relay_manager
from lykke.presentation.workers.tasks.calendar import (
    resubscribe_calendar_task,
    sync_single_calendar_task,
)

from .dependencies.factories import command_handler_factory
from .dependencies.services import get_read_only_repository_factory
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
        state=state,
        prompt="consent select_account",
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
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> RedirectResponse:
    if not code:
        raise HTTPException(
            status_code=400,
            detail="Missing required parameters",
        )

    state_data = verify_state(state, "login")
    auth_token_id_from_state = state_data.get("auth_token_id")
    auth_token_id = UUID(auth_token_id_from_state) if auth_token_id_from_state else None

    handler = command_factory.create(HandleGoogleLoginCallbackHandler)
    result = await handler.handle(
        HandleGoogleLoginCallbackCommand(
            code=code,
            auth_token_id=auth_token_id,
        )
    )

    for calendar_id in result.calendars_to_resubscribe:
        try:
            await resubscribe_calendar_task.kiq(
                user_id=user.id, calendar_id=calendar_id
            )
            logger.info(
                f"Enqueued resubscribe task for calendar {calendar_id} after re-authentication"
            )
        except Exception as e:
            logger.error(
                f"Failed to enqueue resubscribe task for calendar {calendar_id}: {e}"
            )

    # Clean up state
    oauth_states.pop(state, None)

    return RedirectResponse(url="/me")


@router.post("/webhook/{user_id}/{calendar_id}")
async def google_webhook(
    request: Request,
    user_id: UUID,
    calendar_id: UUID,
    ro_repo_factory: Annotated[
        ReadOnlyRepositoryFactory, Depends(get_read_only_repository_factory)
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
    relay_response = await webhook_relay_manager.proxy_request(request)
    if relay_response is not None:
        return relay_response

    logger.info(
        f"Received Google webhook for user {user_id}, calendar {calendar_id}, "
        f"state={x_goog_resource_state}"
    )

    user_repo = UserRepository()
    try:
        user = await user_repo.get(user_id)
    except Exception:
        logger.warning(f"Received Google webhook for unknown user {user_id}")
        return Response(status_code=200)

    query_factory = QueryHandlerFactory(user=user, ro_repo_factory=ro_repo_factory)
    handler = query_factory.create(VerifyGoogleWebhookHandler)
    result = await handler.handle(
        VerifyGoogleWebhookQuery(
            calendar_id=calendar_id,
            channel_token=x_goog_channel_token,
            resource_state=x_goog_resource_state,
        )
    )

    if not result.should_sync:
        return Response(status_code=200)

    # Schedule background task to sync the calendar (initial + incremental)
    await sync_single_calendar_task.kiq(user_id=user_id, calendar_id=calendar_id)
    logger.info(f"Scheduled sync task for calendar {calendar_id}")

    return Response(status_code=200)
