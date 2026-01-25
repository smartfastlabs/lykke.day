"""add time window to tasks

Revision ID: ef4fbd733438
Revises: 84ab3838ff56
Create Date: 2026-01-25 15:50:14.241584

"""

import json
from collections.abc import Sequence
from typing import Union

import fastapi_users_db_sqlalchemy
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ef4fbd733438"
down_revision: str | Sequence[str] | None = "84ab3838ff56"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def convert_schedule_to_time_window(schedule_dict: dict | None) -> dict | None:
    """Convert legacy schedule dict to TimeWindow dict, dropping timing_type."""
    if not schedule_dict:
        return None

    # Extract time fields, ignoring timing_type
    time_window = {}
    for field in ["available_time", "start_time", "end_time"]:
        if field in schedule_dict and schedule_dict[field] is not None:
            time_window[field] = schedule_dict[field]

    # Return None if no time fields were set
    return time_window if time_window else None


def upgrade() -> None:
    """Upgrade schema."""
    # Step 1: Add time_window column (nullable)
    op.add_column(
        "tasks",
        sa.Column(
            "time_window", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )

    # Step 2: Migrate data from schedule to time_window
    connection = op.get_bind()

    # Migrate tasks.schedule -> tasks.time_window
    # Use raw SQL with psycopg's JSONB support
    result = connection.execute(
        text("""
        SELECT id, schedule FROM tasks WHERE schedule IS NOT NULL
    """)
    )

    for row in result:
        task_id = row[0]
        schedule = row[1]

        if schedule:
            time_window = convert_schedule_to_time_window(schedule)
            if time_window:
                # Serialize dict to JSON string, then cast to JSONB
                time_window_json = json.dumps(time_window)
                connection.execute(
                    text(
                        "UPDATE tasks SET time_window = CAST(:time_window AS jsonb) WHERE id = :id"
                    ),
                    {"time_window": time_window_json, "id": task_id},
                )

    # Step 3: Migrate routine_definitions.tasks JSONB array
    # Update each task in the tasks array to convert schedule -> time_window
    result = connection.execute(
        text("""
        SELECT id, tasks FROM routine_definitions WHERE tasks IS NOT NULL
    """)
    )

    for row in result:
        routine_id = row[0]
        tasks = row[1]

        if tasks and isinstance(tasks, list):
            updated = False
            for task in tasks:
                if isinstance(task, dict) and "schedule" in task:
                    time_window = convert_schedule_to_time_window(task.get("schedule"))
                    if time_window:
                        task["time_window"] = time_window
                    # Remove schedule field
                    task.pop("schedule", None)
                    updated = True

            if updated:
                # Serialize list to JSON string, then cast to JSONB
                tasks_json = json.dumps(tasks)
                connection.execute(
                    text(
                        "UPDATE routine_definitions SET tasks = CAST(:tasks AS jsonb) WHERE id = :id"
                    ),
                    {"tasks": tasks_json, "id": routine_id},
                )

    # Step 4: Drop schedule column
    op.drop_column("tasks", "schedule")


def downgrade() -> None:
    """Downgrade schema."""
    # Add schedule column back
    op.add_column(
        "tasks",
        sa.Column(
            "schedule",
            postgresql.JSONB(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
        ),
    )

    # Migrate data back (time_window -> schedule, but we can't restore timing_type)
    connection = op.get_bind()

    result = connection.execute(
        text("""
        SELECT id, time_window FROM tasks WHERE time_window IS NOT NULL
    """)
    )

    for row in result:
        task_id = row[0]
        time_window = row[1]

        if time_window:
            # Convert back to schedule format (without timing_type)
            schedule = {}
            for field in ["available_time", "start_time", "end_time"]:
                if field in time_window:
                    schedule[field] = time_window[field]

            if schedule:
                # Serialize dict to JSON string, then cast to JSONB
                schedule_json = json.dumps(schedule)
                connection.execute(
                    text(
                        "UPDATE tasks SET schedule = CAST(:schedule AS jsonb) WHERE id = :id"
                    ),
                    {"schedule": schedule_json, "id": task_id},
                )

    # Drop time_window column
    op.drop_column("tasks", "time_window")
