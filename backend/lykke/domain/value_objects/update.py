"""Update objects for entity updates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from .base import BaseRequestObject
from .day import BrainDumpItem, DayStatus, DayTag, Goal
from .routine import RoutineSchedule, RoutineTask
from .sync import SyncSubscription
from .task import EventCategory, TaskCategory, TaskType
from .time_block import (
    DayTemplateTimeBlock,
    DayTimeBlock,
    TimeBlockCategory,
    TimeBlockType,
)
from .user import UserSetting, UserStatus


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
class TimeBlockDefinitionUpdateObject(BaseUpdateObject):
    """Update object for TimeBlockDefinition entity."""

    name: str | None = None
    description: str | None = None
    type: TimeBlockType | None = None
    category: TimeBlockCategory | None = None


@dataclass(kw_only=True)
class RoutineUpdateObject(BaseUpdateObject):
    """Update object for Routine entity."""

    name: str | None = None
    category: TaskCategory | None = None
    routine_schedule: RoutineSchedule | None = None
    description: str | None = None
    tasks: list[RoutineTask] | None = None


@dataclass(kw_only=True)
class UserUpdateObject(BaseUpdateObject):
    """Update object for User entity."""

    email: str | None = None
    phone_number: str | None = None
    hashed_password: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    is_verified: bool | None = None
    settings: UserSetting | None = None
    status: UserStatus | None = None
    default_conversation_id: UUID | None = None
    sms_conversation_id: UUID | None = None


@dataclass(kw_only=True)
class DayTemplateUpdateObject(BaseUpdateObject):
    """Update object for DayTemplate entity."""

    slug: str | None = None
    icon: str | None = None
    routine_ids: list[UUID] | None = None
    time_blocks: list[DayTemplateTimeBlock] | None = None


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
class DayUpdateObject(BaseUpdateObject):
    """Update object for Day entity."""

    status: DayStatus | None = None
    scheduled_at: datetime | None = None
    tags: list[DayTag] | None = None
    template_id: UUID | None = None
    time_blocks: list[DayTimeBlock] | None = None
    active_time_block_id: UUID | None = None
    goals: list[Goal] | None = None
    brain_dump_items: list[BrainDumpItem] | None = None


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
class ConversationUpdateObject(BaseUpdateObject):
    """Update object for Conversation entity."""

    status: str | None = None  # ConversationStatus enum as string
    context: dict | None = None
