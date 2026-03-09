import secrets
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from loguru import logger

from lykke.application.gateways import RedisStorageGatewayProtocol
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
from lykke.infrastructure.unauthenticated import UnauthenticatedIdentityAccess
from lykke.presentation.handler_factory import QueryHandlerFactory
from lykke.presentation.workers.tasks.calendar import (
    resubscribe_calendar_task,
    sync_single_calendar_task,
)

from .dependencies.factories import create_command_handler
from .dependencies.services import (
    get_read_only_repository_factory,
    get_redis_storage_gateway,
)
from .dependencies.user import get_current_user

router = APIRouter()


def _oauth_state_key(state: str) -> str:
    return f"oauth-state:{state}"


def _oauth_state_ttl_seconds() -> int:
    return max(1, int(OAUTH_STATE_EXPIRY.total_seconds()))


async def _store_oauth_state(
    *,
    storage_gateway: RedisStorageGatewayProtocol,
    state: str,
    action: str,
    auth_token_id: UUID | None = None,
) -> None:
    payload = {
        "action": action,
        "auth_token_id": str(auth_token_id) if auth_token_id else None,
    }
    await storage_gateway.set_json(
        key=_oauth_state_key(state),
        value=payload,
        ttl_seconds=_oauth_state_ttl_seconds(),
    )


@router.get("/login")
async def google_login(
    storage_gateway: Annotated[
        RedisStorageGatewayProtocol, Depends(get_redis_storage_gateway)
    ],
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

    # Store state in Redis with TTL to support multi-worker callbacks.
    await _store_oauth_state(
        storage_gateway=storage_gateway,
        state=state,
        action="login",
        auth_token_id=auth_token_id,
    )

    return RedirectResponse(authorization_url)


async def verify_state(
    storage_gateway: RedisStorageGatewayProtocol,
    state: str,
    expected_action: str,
) -> dict[str, object]:
    """
    Verify the state parameter and check if it matches the expected action.
    Returns the state data if valid.
    """

    state_data = await storage_gateway.get_json(_oauth_state_key(state))
    if state_data is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid state parameter",
        )
    if state_data.get("action") != expected_action:
        await storage_gateway.delete(_oauth_state_key(state))
        raise HTTPException(
            status_code=400,
            detail="Invalid action parameter",
        )

    return state_data


def _parse_auth_token_id_from_state(state_data: dict[str, object]) -> UUID | None:
    raw_auth_token_id = state_data.get("auth_token_id")
    if raw_auth_token_id is None:
        return None
    if not isinstance(raw_auth_token_id, str):
        raise HTTPException(status_code=400, detail="Invalid auth token in state")
    try:
        return UUID(raw_auth_token_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid auth token in state") from exc


@router.get("/callback/login")
async def google_login_callback(
    state: str,
    code: str,
    user: Annotated[UserEntity, Depends(get_current_user)],
    handler: Annotated[HandleGoogleLoginCallbackHandler, Depends(create_command_handler(HandleGoogleLoginCallbackHandler))],
    storage_gateway: Annotated[
        RedisStorageGatewayProtocol, Depends(get_redis_storage_gateway)
    ],
) -> RedirectResponse:
    if not code:
        raise HTTPException(
            status_code=400,
            detail="Missing required parameters",
        )

    state_data = await verify_state(storage_gateway, state, "login")
    auth_token_id = _parse_auth_token_id_from_state(state_data)

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

    # Consume state so it cannot be reused.
    await storage_gateway.delete(_oauth_state_key(state))

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
    logger.info(
        f"Received Google webhook for user {user_id}, calendar {calendar_id}, "
        f"state={x_goog_resource_state}"
    )

    identity_access = UnauthenticatedIdentityAccess()
    user = await identity_access.get_user_by_id(user_id)
    if user is None:
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
