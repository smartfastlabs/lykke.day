"""Migrate days.reminders to tasks (TaskType.REMINDER), then drop days.reminders.

Revision ID: a1b2c3d4e5f6
Revises: 2699bc117edc
Create Date: 2026-01-31

"""

from collections.abc import Sequence
from datetime import datetime
from typing import Union
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "2699bc117edc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _reminder_status_to_task_status(reminder_status: str) -> str:
    """Map old ReminderStatus to TaskStatus."""
    if reminder_status == "INCOMPLETE":
        return "NOT_STARTED"
    if reminder_status == "COMPLETE":
        return "COMPLETE"
    if reminder_status == "PUNT":
        return "PUNT"
    return "NOT_STARTED"


def upgrade() -> None:
    """Migrate reminders from days.reminders JSONB into tasks table, then drop column."""
    connection = op.get_bind()

    # 1. Select all days that have reminders
    result = connection.execute(
        text(
            "SELECT id, user_id, date, reminders FROM days "
            "WHERE reminders IS NOT NULL AND reminders != '[]'::jsonb"
        )
    )
    rows = result.fetchall()

    for row in rows:
        _day_id, day_user_id, date_val, reminders_json = row
        if not reminders_json:
            continue
        reminders = reminders_json if isinstance(reminders_json, list) else []
        user_id_str = str(day_user_id) if day_user_id else None
        if not user_id_str:
            continue
        for reminder in reminders:
            if not isinstance(reminder, dict):
                continue
            rid = reminder.get("id")
            name = reminder.get("name") or ""
            status_str = reminder.get("status", "INCOMPLETE")
            created_at = reminder.get("created_at")

            task_id = rid
            if isinstance(task_id, str):
                task_id = UUID(task_id)
            task_id_str = str(task_id)

            task_status = _reminder_status_to_task_status(
                status_str if isinstance(status_str, str) else "INCOMPLETE"
            )
            completed_at = None
            if task_status == "COMPLETE" and created_at:
                if isinstance(created_at, str):
                    completed_at = datetime.fromisoformat(
                        created_at.replace("Z", "+00:00")
                    )
                else:
                    completed_at = created_at

            connection.execute(
                text("""
                    INSERT INTO tasks (
                        id, user_id, date, scheduled_date, name, status, type,
                        description, category, frequency, completed_at, snoozed_until,
                        time_window, routine_definition_id, tags, actions
                    ) VALUES (
                        :id, :user_id, :date_val, :date_val, :name, :status, 'REMINDER',
                        NULL, 'PLANNING', 'ONCE', :completed_at, NULL,
                        NULL, NULL, '[]'::jsonb, '[]'::jsonb
                    )
                """),
                {
                    "id": task_id_str,
                    "user_id": user_id_str,
                    "date_val": date_val,
                    "name": name,
                    "status": task_status,
                    "completed_at": completed_at,
                },
            )

    # 2. Drop the reminders column from days
    op.drop_column("days", "reminders")


def downgrade() -> None:
    """Re-add days.reminders column (data is not restored)."""
    op.add_column(
        "days",
        sa.Column("reminders", JSONB, nullable=True),
    )
