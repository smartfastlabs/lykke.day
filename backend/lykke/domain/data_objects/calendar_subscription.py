"""Data object for Google Calendar push notification subscription."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(kw_only=True)
class CalendarSubscription:
    """Represents a Google Calendar watch channel subscription.

    Attributes:
        channel_id: Unique identifier for the notification channel.
        resource_id: An opaque ID that identifies the resource being watched.
        expiration: When the subscription expires (UTC).
    """

    channel_id: str
    resource_id: str
    expiration: datetime

