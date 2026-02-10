"""Command to handle Google OAuth login callback."""

from dataclasses import dataclass
from uuid import UUID

from googleapiclient.discovery import build
from loguru import logger

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.application.repositories import (
    AuthTokenRepositoryReadOnlyProtocol,
    CalendarRepositoryReadOnlyProtocol,
)
from lykke.core.exceptions import AuthenticationError
from lykke.domain import value_objects
from lykke.domain.entities import AuthTokenEntity, CalendarEntity
from lykke.domain.events.base import EntityUpdatedEvent
from lykke.domain.events.calendar_events import CalendarUpdatedEvent
from lykke.domain.value_objects.update import (
    AuthTokenUpdateObject,
    CalendarUpdateObject,
)


@dataclass(frozen=True)
class HandleGoogleLoginCallbackCommand(Command):
    """Command to handle Google OAuth callback and update calendars."""

    code: str
    auth_token_id: UUID | None = None


@dataclass(frozen=True)
class HandleGoogleLoginCallbackResult:
    """Result of handling Google OAuth callback."""

    calendars_to_resubscribe: list[UUID]


class HandleGoogleLoginCallbackHandler(
    BaseCommandHandler[
        HandleGoogleLoginCallbackCommand,
        HandleGoogleLoginCallbackResult,
    ]
):
    """Handle Google OAuth callback and update auth tokens/calendars."""

    google_gateway: GoogleCalendarGatewayProtocol
    auth_token_ro_repo: AuthTokenRepositoryReadOnlyProtocol
    calendar_ro_repo: CalendarRepositoryReadOnlyProtocol

    async def handle(
        self, command: HandleGoogleLoginCallbackCommand
    ) -> HandleGoogleLoginCallbackResult:
        """Handle OAuth callback, updating tokens/calendars in a transaction."""
        flow = self.google_gateway.get_flow("login")
        flow.fetch_token(code=command.code)

        service = build("calendar", "v3", credentials=flow.credentials)
        calendar_list = service.calendarList().list().execute()
        google_platform_ids = {cal["id"] for cal in calendar_list.get("items", [])}

        calendars_to_resubscribe: list[UUID] = []

        async with self.new_uow() as uow:
            existing_auth_token = None
            if command.auth_token_id:
                try:
                    existing_auth_token = await self.auth_token_ro_repo.get(
                        command.auth_token_id
                    )
                    if existing_auth_token.user_id != self.user.id:
                        raise AuthenticationError("Auth token does not belong to user")
                    logger.info(
                        f"Re-authenticating specific auth token {existing_auth_token.id} "
                        f"for user {self.user.id}"
                    )
                except AuthenticationError:
                    raise
                except Exception as exc:
                    logger.warning(
                        f"Could not find auth token {command.auth_token_id} from state: {exc}"
                    )
                    existing_auth_token = None

            if not existing_auth_token and google_platform_ids:
                existing_calendars = await self.calendar_ro_repo.search(
                    value_objects.CalendarQuery()
                )
                matching_calendar = next(
                    (
                        cal
                        for cal in existing_calendars
                        if cal.platform_id in google_platform_ids
                        and cal.platform == "google"
                    ),
                    None,
                )
                if matching_calendar and matching_calendar.auth_token_id is not None:
                    try:
                        existing_auth_token = await self.auth_token_ro_repo.get(
                            matching_calendar.auth_token_id
                        )
                        logger.info(
                            f"Matched existing auth token {existing_auth_token.id} "
                            f"via calendar {matching_calendar.id} for user {self.user.id}"
                        )
                    except Exception as exc:
                        logger.warning(
                            f"Could not find auth token {matching_calendar.auth_token_id}: {exc}"
                        )

            auth_token_data = AuthTokenEntity(
                user_id=self.user.id,
                client_id=flow.credentials.client_id,
                client_secret=flow.credentials.client_secret,
                expires_at=flow.credentials.expiry,
                platform="google",
                refresh_token=flow.credentials.refresh_token,
                scopes=flow.credentials.scopes,
                token=flow.credentials.token,
                token_uri=flow.credentials.token_uri,
            )

            if existing_auth_token:
                auth_token_data.id = existing_auth_token.id
                auth_token_data.add_event(
                    EntityUpdatedEvent(
                        user_id=self.user.id,
                        update_object=AuthTokenUpdateObject(
                            token=auth_token_data.token,
                            refresh_token=auth_token_data.refresh_token,
                            token_uri=auth_token_data.token_uri,
                            client_id=auth_token_data.client_id,
                            client_secret=auth_token_data.client_secret,
                            scopes=auth_token_data.scopes,
                            expires_at=auth_token_data.expires_at,
                        ),
                    )
                )
                uow.add(auth_token_data)
            else:
                await uow.create(auth_token_data)

            if existing_auth_token:
                all_user_calendars = await self.calendar_ro_repo.search(
                    value_objects.CalendarQuery()
                )
                for cal in all_user_calendars:
                    if (
                        cal.auth_token_id == existing_auth_token.id
                        and cal.platform == "google"
                        and cal.sync_subscription is not None
                    ):
                        calendars_to_resubscribe.append(cal.id)

            for google_calendar in calendar_list.get("items", []):
                platform_id = google_calendar["id"]
                existing_calendar = await self.calendar_ro_repo.search_one_or_none(
                    value_objects.CalendarQuery(platform_id=platform_id)
                )

                if existing_calendar:
                    update_data = CalendarUpdateObject(
                        name=google_calendar["summary"],
                        auth_token_id=auth_token_data.id,
                    )
                    updated = existing_calendar.apply_update(
                        update_data, CalendarUpdatedEvent
                    )
                    uow.add(updated)
                    logger.info(
                        f"Updating existing calendar {existing_calendar.id} "
                        f"(platform_id: {platform_id}) for user {self.user.id}"
                    )
                    continue

                new_calendar = CalendarEntity(
                    user_id=self.user.id,
                    name=google_calendar["summary"],
                    platform="google",
                    platform_id=platform_id,
                    auth_token_id=auth_token_data.id,
                )
                await uow.create(new_calendar)
                logger.info(
                    f"Creating new calendar (platform_id: {platform_id}) for user {self.user.id}"
                )

        return HandleGoogleLoginCallbackResult(
            calendars_to_resubscribe=calendars_to_resubscribe
        )
