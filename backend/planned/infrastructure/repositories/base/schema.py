"""SQLAlchemy Core table definitions for all entities."""

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Index,
    MetaData,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID

metadata = MetaData()

# Auth Tokens
auth_tokens = Table(
    "auth_tokens",
    metadata,
    Column("id", String, primary_key=True),
    Column("platform", String, nullable=False),
    Column("token", Text, nullable=False),
    Column("refresh_token", Text),
    Column("token_uri", Text),
    Column("client_id", Text),
    Column("client_secret", Text),
    Column("scopes", JSONB),
    Column("expires_at", DateTime),
    Column("uuid", PGUUID),
    Column("created_at", DateTime, nullable=False),
)

# Calendars
calendars = Table(
    "calendars",
    metadata,
    Column("id", String, primary_key=True),
    Column("name", String, nullable=False),
    Column("auth_token_id", String, nullable=False),
    Column("platform_id", String, nullable=False),
    Column("platform", String, nullable=False),
    Column("last_sync_at", DateTime),
)

# Day Templates
day_templates = Table(
    "day_templates",
    metadata,
    Column("id", String, primary_key=True),
    Column("tasks", JSONB),  # list[str]
    Column("alarm", JSONB),  # Alarm | None
    Column("icon", String),
)

# Days
days = Table(
    "days",
    metadata,
    Column("id", String, primary_key=True),  # date as string
    Column("date", Date, nullable=False),
    Column("template_id", String, nullable=False),
    Column("tags", JSONB),  # list[DayTag]
    Column("alarm", JSONB),  # Alarm | None
    Column("status", String, nullable=False),  # DayStatus enum as string
    Column("scheduled_at", DateTime),
    Index("idx_days_date", "date"),
)

# Events
events = Table(
    "events",
    metadata,
    Column("id", String, primary_key=True),
    Column("date", Date, nullable=False),  # extracted from starts_at for querying
    Column("name", String, nullable=False),
    Column("calendar_id", String, nullable=False),
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
    Index("idx_events_calendar_id", "calendar_id"),
)

# Messages
messages = Table(
    "messages",
    metadata,
    Column("id", String, primary_key=True),
    Column("date", Date, nullable=False),  # extracted from sent_at for querying
    Column("author", String, nullable=False),  # Literal["system", "agent", "user"]
    Column("sent_at", DateTime, nullable=False),
    Column("content", Text, nullable=False),
    Column("read_at", DateTime),
    Index("idx_messages_date", "date"),
)

# Push Subscriptions
push_subscriptions = Table(
    "push_subscriptions",
    metadata,
    Column("id", String, primary_key=True),
    Column("device_name", String),
    Column("endpoint", String, nullable=False),
    Column("p256dh", String, nullable=False),
    Column("auth", String, nullable=False),
    Column("uuid", PGUUID),
    Column("created_at", DateTime, nullable=False),
)

# Routines
routines = Table(
    "routines",
    metadata,
    Column("id", String, primary_key=True),
    Column("name", String, nullable=False),
    Column("category", String, nullable=False),  # TaskCategory enum as string
    Column("routine_schedule", JSONB, nullable=False),  # RoutineSchedule
    Column("description", String, nullable=False),
    Column("tasks", JSONB),  # list[RoutineTask]
)

# Task Definitions
task_definitions = Table(
    "task_definitions",
    metadata,
    Column("id", String, primary_key=True),
    Column("name", String, nullable=False),
    Column("description", String, nullable=False),
    Column("type", String, nullable=False),  # TaskType enum as string
)

# Tasks
tasks = Table(
    "tasks",
    metadata,
    Column("id", String, primary_key=True),
    Column("date", Date, nullable=False),  # extracted from scheduled_date for querying
    Column("scheduled_date", Date, nullable=False),
    Column("name", String, nullable=False),
    Column("status", String, nullable=False),  # TaskStatus enum as string
    Column("task_definition", JSONB, nullable=False),  # TaskDefinition
    Column("category", String, nullable=False),  # TaskCategory enum as string
    Column("frequency", String, nullable=False),  # TaskFrequency enum as string
    Column("completed_at", DateTime),
    Column("schedule", JSONB),  # TaskSchedule | None
    Column("routine_id", String),
    Column("tags", JSONB),  # list[TaskTag]
    Column("actions", JSONB),  # list[Action]
    Index("idx_tasks_date", "date"),
    Index("idx_tasks_routine_id", "routine_id"),
)
