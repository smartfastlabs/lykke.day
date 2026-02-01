"""Update objects for entity updates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .base import BaseRequestObject

if TYPE_CHECKING:
    from datetime import date as dt_date, datetime, time
    from uuid import UUID

    from .ai_chat import FactoidCriticality, FactoidType
    from .day import Alarm, DayStatus, DayTag
    from .high_level_plan import HighLevelPlan
    from .routine_definition import (
        RecurrenceSchedule,
        RoutineDefinitionTask,
        TimeWindow,
    )
    from .sync import SyncSubscription
    from .task import (
        CalendarEntryAttendanceStatus,
        EventCategory,
        TaskCategory,
        TaskFrequency,
        TaskStatus,
        TaskType,
    )
    from .time_block import (
        DayTemplateTimeBlock,
        DayTimeBlock,
        TimeBlockCategory,
        TimeBlockType,
    )
    from .user import UserSettingUpdate, UserStatus


@dataclass(kw_only=True)
class BaseUpdateObject(BaseRequestObject):
    """Base class for all update objects.

    Update objects contain optional fields for all updateable fields on an entity.
    Fields that should not be updated (like id, user_id, created_at, etc.) are
    excluded from update objects.
    """


@dataclass(kw_only=True)
class TaskDefinitionUpdateObject(BaseUpdateObject):
    """Update object for TaskDefinition entity."""

    name: str | None = None
    description: str | None = None
    type: TaskType | None = None


@dataclass(kw_only=True)
class TaskUpdateObject(BaseUpdateObject):
    """Update object for Task entity."""

    scheduled_date: dt_date | None = None
    status: TaskStatus | None = None
    snoozed_until: datetime | None = None


@dataclass(kw_only=True)
class TriggerUpdateObject(BaseUpdateObject):
    """Update object for Trigger entity."""

    name: str | None = None
    description: str | None = None


@dataclass(kw_only=True)
class TacticUpdateObject(BaseUpdateObject):
    """Update object for Tactic entity."""

    name: str | None = None
    description: str | None = None


@dataclass(kw_only=True)
class TimeBlockDefinitionUpdateObject(BaseUpdateObject):
    """Update object for TimeBlockDefinition entity."""

    name: str | None = None
    description: str | None = None
    type: TimeBlockType | None = None
    category: TimeBlockCategory | None = None


@dataclass(kw_only=True)
class RoutineDefinitionUpdateObject(BaseUpdateObject):
    """Update object for RoutineDefinition entity."""

    name: str | None = None
    category: TaskCategory | None = None
    routine_definition_schedule: RecurrenceSchedule | None = None
    description: str | None = None
    time_window: TimeWindow | None = None
    tasks: list[RoutineDefinitionTask] | None = None


@dataclass(kw_only=True)
class UserUpdateObject(BaseUpdateObject):
    """Update object for User entity."""

    email: str | None = None
    phone_number: str | None = None
    hashed_password: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    is_verified: bool | None = None
    settings_update: UserSettingUpdate | None = None
    status: UserStatus | None = None


@dataclass(kw_only=True)
class AuthTokenUpdateObject(BaseUpdateObject):
    """Update object for AuthToken entity."""

    token: str | None = None
    refresh_token: str | None = None
    token_uri: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    scopes: list[Any] | None = None
    expires_at: datetime | None = None


@dataclass(kw_only=True)
class DayTemplateUpdateObject(BaseUpdateObject):
    """Update object for DayTemplate entity."""

    slug: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    icon: str | None = None
    routine_definition_ids: list[UUID] | None = None
    time_blocks: list[DayTemplateTimeBlock] | None = None
    alarms: list[Alarm] | None = None
    high_level_plan: HighLevelPlan | None = None


@dataclass(kw_only=True)
class CalendarUpdateObject(BaseUpdateObject):
    """Update object for Calendar entity."""

    name: str | None = None
    auth_token_id: UUID | None = None
    default_event_category: EventCategory | None = None
    last_sync_at: datetime | None = None
    sync_subscription: SyncSubscription | None = None
    sync_subscription_id: str | None = None


@dataclass(kw_only=True)
class CalendarEntrySeriesUpdateObject(BaseUpdateObject):
    """Update object for CalendarEntrySeries entity."""

    name: str | None = None
    event_category: EventCategory | None = None


@dataclass(kw_only=True)
class CalendarEntryUpdateObject(BaseUpdateObject):
    """Update object for CalendarEntry entity."""

    name: str | None = None
    status: str | None = None
    attendance_status: CalendarEntryAttendanceStatus | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    frequency: TaskFrequency | None = None
    category: EventCategory | None = None
    calendar_entry_series_id: UUID | None = None
    updated_at: datetime | None = None
    # Note: actions is a list, but we typically don't update it directly via update object


@dataclass(kw_only=True)
class DayUpdateObject(BaseUpdateObject):
    """Update object for Day entity."""

    status: DayStatus | None = None
    scheduled_at: datetime | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    tags: list[DayTag] | None = None
    template_id: UUID | None = None
    time_blocks: list[DayTimeBlock] | None = None
    active_time_block_id: UUID | None = None
    alarms: list[Alarm] | None = None
    high_level_plan: HighLevelPlan | None = None


@dataclass(kw_only=True)
class PushSubscriptionUpdateObject(BaseUpdateObject):
    """Update object for PushSubscription entity."""

    device_name: str | None = None


@dataclass(kw_only=True)
class BotPersonalityUpdateObject(BaseUpdateObject):
    """Update object for BotPersonality entity."""

    name: str | None = None
    user_amendments: str | None = None


@dataclass(kw_only=True)
class FactoidUpdateObject(BaseUpdateObject):
    """Update object for Factoid entity."""

    content: str | None = None
    factoid_type: FactoidType | None = None
    criticality: FactoidCriticality | None = None
    user_confirmed: bool | None = None
