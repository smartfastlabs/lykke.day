"""SQLAlchemy Core table definitions for all entities."""

from __future__ import annotations

from sqlalchemy import Column, Date, DateTime, Index, MetaData, String, Table, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

metadata = MetaData()


# Users
users = Table(
    "users",
    metadata,
    Column("uuid", PGUUID, primary_key=True),
    Column("username", String, nullable=False),
    Column("email", String, nullable=False),
    Column("phone_number", String, nullable=True),
    Column("password_hash", Text, nullable=False),
    Column("settings", JSONB),  # UserSetting as JSONB
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=True),
    Index("idx_users_email", "email", unique=True),
)

# Auth Tokens
auth_tokens = Table(
    "auth_tokens",
    metadata,
    Column("uuid", PGUUID, primary_key=True),
    Column("user_uuid", PGUUID, nullable=False),
    Column("platform", String, nullable=False),
    Column("token", Text, nullable=False),
    Column("refresh_token", Text),
    Column("token_uri", Text),
    Column("client_id", Text),
    Column("client_secret", Text),
    Column("scopes", JSONB),
    Column("expires_at", DateTime),
    Column("created_at", DateTime, nullable=False),
    Index("idx_auth_tokens_user_uuid", "user_uuid"),
)

# Calendars
calendars = Table(
    "calendars",
    metadata,
    Column("uuid", PGUUID, primary_key=True),
    Column("user_uuid", PGUUID, nullable=False),
    Column("name", String, nullable=False),
    Column("auth_token_uuid", String, nullable=False),
    Column("platform_id", String, nullable=False),
    Column("platform", String, nullable=False),
    Column("last_sync_at", DateTime),
    Index("idx_calendars_user_uuid", "user_uuid"),
)

# Day Templates
day_templates = Table(
    "day_templates",
    metadata,
    Column("uuid", PGUUID, primary_key=True),
    Column("user_uuid", PGUUID, nullable=False),
    Column("slug", String, nullable=False),
    Column("tasks", JSONB),  # list[str]
    Column("alarm", JSONB),  # Alarm | None
    Column("icon", String),
    Index("idx_day_templates_user_uuid", "user_uuid"),
    Index("idx_day_templates_user_slug", "user_uuid", "slug", unique=True),
)

# Days
days = Table(
    "days",
    metadata,
    Column("uuid", PGUUID, primary_key=True),
    Column("user_uuid", PGUUID, nullable=False),
    Column("date", Date, nullable=False),
    Column("template_uuid", PGUUID, nullable=False),
    Column("tags", JSONB),  # list[DayTag]
    Column("alarm", JSONB),  # Alarm | None
    Column("status", String, nullable=False),  # DayStatus enum as string
    Column("scheduled_at", DateTime),
    Index("idx_days_date", "date"),
    Index("idx_days_user_uuid", "user_uuid"),
)

# Events
events = Table(
    "events",
    metadata,
    Column("uuid", PGUUID, primary_key=True),
    Column("user_uuid", PGUUID, nullable=False),
    Column("date", Date, nullable=False),  # extracted from starts_at for querying
    Column("name", String, nullable=False),
    Column("calendar_uuid", String, nullable=False),
    Column("platform_id", String, nullable=False),
    Column("platform", String, nullable=False),
    Column("status", String, nullable=False),
    Column("starts_at", DateTime, nullable=False),
    Column("frequency", String, nullable=False),  # TaskFrequency enum as string
    Column("ends_at", DateTime),
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=False),
    Column("people", JSONB),  # list[Person]
    Column("actions", JSONB),  # list[Action]
    Index("idx_events_date", "date"),
    Index("idx_events_calendar_uuid", "calendar_uuid"),
    Index("idx_events_user_uuid", "user_uuid"),
)

# Messages
messages = Table(
    "messages",
    metadata,
    Column("uuid", PGUUID, primary_key=True),
    Column("user_uuid", PGUUID, nullable=False),
    Column("date", Date, nullable=False),  # extracted from sent_at for querying
    Column("author", String, nullable=False),  # Literal["system", "agent", "user"]
    Column("sent_at", DateTime, nullable=False),
    Column("content", Text, nullable=False),
    Column("read_at", DateTime),
    Index("idx_messages_date", "date"),
    Index("idx_messages_user_uuid", "user_uuid"),
)

# Push Subscriptions
push_subscriptions = Table(
    "push_subscriptions",
    metadata,
    Column("uuid", PGUUID, primary_key=True),
    Column("user_uuid", PGUUID, nullable=False),
    Column("device_name", String),
    Column("endpoint", String, nullable=False),
    Column("p256dh", String, nullable=False),
    Column("auth", String, nullable=False),
    Column("created_at", DateTime, nullable=False),
    Index("idx_push_subscriptions_user_uuid", "user_uuid"),
)

# Routines
routines = Table(
    "routines",
    metadata,
    Column("uuid", PGUUID, primary_key=True),
    Column("user_uuid", PGUUID, nullable=False),
    Column("name", String, nullable=False),
    Column("category", String, nullable=False),  # TaskCategory enum as string
    Column("routine_schedule", JSONB, nullable=False),  # RoutineSchedule
    Column("description", String, nullable=False),
    Column("tasks", JSONB),  # list[RoutineTask]
    Index("idx_routines_user_uuid", "user_uuid"),
)

# Task Definitions
task_definitions = Table(
    "task_definitions",
    metadata,
    Column("uuid", PGUUID, primary_key=True),
    Column("user_uuid", PGUUID, nullable=False),
    Column("name", String, nullable=False),
    Column("description", String, nullable=False),
    Column("type", String, nullable=False),  # TaskType enum as string
    Index("idx_task_definitions_user_uuid", "user_uuid"),
)

# Tasks
tasks = Table(
    "tasks",
    metadata,
    Column("uuid", PGUUID, primary_key=True),
    Column("user_uuid", PGUUID, nullable=False),
    Column("date", Date, nullable=False),  # extracted from scheduled_date for querying
    Column("scheduled_date", Date, nullable=False),
    Column("name", String, nullable=False),
    Column("status", String, nullable=False),  # TaskStatus enum as string
    Column("task_definition", JSONB, nullable=False),  # TaskDefinition
    Column("category", String, nullable=False),  # TaskCategory enum as string
    Column("frequency", String, nullable=False),  # TaskFrequency enum as string
    Column("completed_at", DateTime),
    Column("schedule", JSONB),  # TaskSchedule | None
    Column("routine_uuid", String),
    Column("tags", JSONB),  # list[TaskTag]
    Column("actions", JSONB),  # list[Action]
    Index("idx_tasks_date", "date"),
    Index("idx_tasks_routine_uuid", "routine_uuid"),
    Index("idx_tasks_user_uuid", "user_uuid"),
)
