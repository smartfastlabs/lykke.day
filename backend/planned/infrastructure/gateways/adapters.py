"""Adapters that implement gateway protocols using infrastructure implementations."""

from datetime import datetime
from typing import TYPE_CHECKING

from planned.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from planned.application.gateways.web_push_protocol import WebPushGatewayProtocol
from planned.domain.entities import AuthToken, Calendar, CalendarEntry, NotificationPayload, PushSubscription

if TYPE_CHECKING:
    from google_auth_oauthlib.flow import Flow

from . import google, web_push


class GoogleCalendarGatewayAdapter(GoogleCalendarGatewayProtocol):
    """Adapter that implements GoogleCalendarGatewayProtocol using infrastructure implementation."""

    async def load_calendar_events(
        self,
        calendar: Calendar,
        lookback: datetime,
        token: AuthToken,
    ) -> list[CalendarEntry]:
        """Load calendar entries from Google Calendar."""
        return await google.load_calendar_events(
            calendar,
            lookback=lookback,
            token=token,
        )

    def get_flow(self, flow_name: str) -> "Flow":
        """Get OAuth flow for Google authentication."""
        return google.get_flow(flow_name)


class WebPushGatewayAdapter(WebPushGatewayProtocol):
    """Adapter that implements WebPushGatewayProtocol using infrastructure implementation."""

    async def send_notification(
        self,
        subscription: PushSubscription,
        content: str | dict | NotificationPayload,
    ) -> None:
        """Send a push notification to a subscription."""
        await web_push.send_notification(
            subscription=subscription,
            content=content,
        )

