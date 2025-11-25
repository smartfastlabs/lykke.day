from datetime import UTC, date as dt_date, datetime

from gcsa.event import Event as GoogleEvent
from pydantic import Field, computed_field

from .base import BaseObject


class Event(BaseObject):
    name: str
    calendar_id: str = Field(alias="calendarId")
    platform_id: str = Field(alias="platformId")
    platform: str
    status: str
    starts_at: datetime | None = Field(default=None, alias="startsAt")
    ends_at: datetime | None = Field(default=None, alias="endsAt")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), alias="createdAt"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), alias="updatedAt"
    )

    @computed_field
    @property
    def date(self) -> dt_date:
        return self.starts_at.date()

    @computed_field
    @property
    def guid(self) -> str:
        return f"event:{self.platform}-{self.platform_id}"

    @classmethod
    def from_google(cls, calendar_id: str, google_event: GoogleEvent) -> "Event":
        event = cls(
            calendar_id=calendar_id,
            status=google_event.other.get("status", "NA"),
            name=google_event.summary,
            starts_at=google_event.start.astimezone(UTC).replace(
                tzinfo=None,
            )
            if isinstance(google_event.start, datetime)
            else google_event.start,
            ends_at=google_event.end.astimezone(UTC).replace(
                tzinfo=None,
            )
            if isinstance(google_event.end, datetime)
            else google_event.end,
            platform_id=google_event.id or "NA",
            platform="google",
            created_at=google_event.created.astimezone(UTC).replace(
                tzinfo=None
            ),
            updated_at=google_event.updated.astimezone(UTC).replace(
                tzinfo=None
            ),
        )
        return event
