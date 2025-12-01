from datetime import UTC, date as dt_date, datetime
from zoneinfo import ZoneInfo

from gcsa.event import Event as GoogleEvent
from pydantic import Field, computed_field

from planned import settings

from .base import BaseObject


class Event(BaseObject):
    name: str
    calendar_id: str
    platform_id: str
    platform: str
    status: str
    starts_at: datetime
    ends_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @computed_field  # mypy: ignore
    @property
    def date(self) -> dt_date:
        return self.starts_at.astimezone(ZoneInfo(settings.TIMEZONE)).date()

    @classmethod
    def from_google(cls, calendar_id: str, google_event: GoogleEvent) -> "Event":
        event = cls(
            calendar_id=calendar_id,
            status=google_event.other.get("status", "NA"),
            name=google_event.summary,
            starts_at=google_event.start.replace(tzinfo=UTC).astimezone(
                ZoneInfo(settings.TIMEZONE)
            ),
            ends_at=google_event.end.replace(tzinfo=UTC).astimezone(
                ZoneInfo(settings.TIMEZONE)
            ),
            platform_id=google_event.id or "NA",
            platform="google",
            created_at=google_event.created.astimezone(UTC).replace(tzinfo=None),
            updated_at=google_event.updated.astimezone(UTC).replace(tzinfo=None),
            id=f"google:{calendar_id}-{google_event.id}",
        )
        return event
