"""Update objects for entity updates."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from .alarm import Alarm
from .base import BaseRequestObject
from .day import DayStatus, DayTag
from .routine import RoutineSchedule, RoutineTask
from .sync import SyncSubscription
from .task import EventCategory, TaskCategory, TaskType
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


@dataclass(kw_only=True)
class DayTemplateUpdateObject(BaseUpdateObject):
    """Update object for DayTemplate entity."""

    slug: str | None = None
    alarm: Alarm | None = None
    icon: str | None = None
    routine_ids: list[UUID] | None = None


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
class DayUpdateObject(BaseUpdateObject):
    """Update object for Day entity."""

    alarm: Alarm | None = None
    status: DayStatus | None = None
    scheduled_at: datetime | None = None
    tags: list[DayTag] | None = None
    template_id: UUID | None = None

