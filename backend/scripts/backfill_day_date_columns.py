#!/usr/bin/env python3
"""Backfill date/day_id columns for day-scoped tables.

Usage:
    poetry run python scripts/backfill_day_date_columns.py
    poetry run python scripts/backfill_day_date_columns.py --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from datetime import UTC, date as dt_date, datetime
from uuid import NAMESPACE_DNS, UUID, uuid5

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from lykke.infrastructure.database import close_engine, get_engine

DAY_NAMESPACE = uuid5(NAMESPACE_DNS, "lykke.day")


@dataclass(frozen=True)
class BackfillStats:
    table: str
    scanned: int = 0
    updated: int = 0
    skipped_missing_date: int = 0


def _build_day_id(user_id: UUID, date_value: dt_date) -> UUID:
    return uuid5(DAY_NAMESPACE, f"{user_id}:{date_value.isoformat()}")


async def _backfill_existing_date_table(
    conn: AsyncConnection,
    *,
    table_name: str,
    dry_run: bool,
) -> BackfillStats:
    rows = (
        await conn.execute(
            text(
                f"""
                SELECT id, user_id, date, day_id
                FROM {table_name}
                WHERE day_id IS NULL
                """
            )
        )
    ).fetchall()

    updates: list[dict[str, object]] = []
    skipped_missing_date = 0
    for row in rows:
        row_id, user_id, date_value, _existing_day_id = row
        if user_id is None or date_value is None:
            skipped_missing_date += 1
            continue
        updates.append(
            {
                "id": row_id,
                "day_id": _build_day_id(user_id, date_value),
            }
        )

    if updates and not dry_run:
        await conn.execute(
            text(f"UPDATE {table_name} SET day_id = :day_id WHERE id = :id"),
            updates,
        )

    return BackfillStats(
        table=table_name,
        scanned=len(rows),
        updated=len(updates),
        skipped_missing_date=skipped_missing_date,
    )


async def _backfill_datetime_derived_table(
    conn: AsyncConnection,
    *,
    table_name: str,
    datetime_column: str,
    dry_run: bool,
) -> BackfillStats:
    rows = (
        await conn.execute(
            text(
                f"""
                SELECT id, user_id, date, day_id, {datetime_column}
                FROM {table_name}
                WHERE date IS NULL OR day_id IS NULL
                """
            )
        )
    ).fetchall()

    updates: list[dict[str, object]] = []
    skipped_missing_date = 0
    for row in rows:
        row_id, user_id, date_value, _existing_day_id, dt_value = row
        if user_id is None:
            skipped_missing_date += 1
            continue

        resolved_date = date_value
        if resolved_date is None:
            if isinstance(dt_value, datetime):
                resolved_date = dt_value.date()
            else:
                skipped_missing_date += 1
                continue

        updates.append(
            {
                "id": row_id,
                "date_value": resolved_date,
                "day_id": _build_day_id(user_id, resolved_date),
            }
        )

    if updates and not dry_run:
        await conn.execute(
            text(
                f"""
                UPDATE {table_name}
                SET date = :date_value, day_id = :day_id
                WHERE id = :id
                """
            ),
            updates,
        )

    return BackfillStats(
        table=table_name,
        scanned=len(rows),
        updated=len(updates),
        skipped_missing_date=skipped_missing_date,
    )


def _print_stats(stats: list[BackfillStats], dry_run: bool) -> None:
    mode = "DRY RUN" if dry_run else "APPLY"
    print(f"\nBackfill mode: {mode}")
    print("-" * 72)
    total_scanned = 0
    total_updated = 0
    total_skipped = 0
    for item in stats:
        total_scanned += item.scanned
        total_updated += item.updated
        total_skipped += item.skipped_missing_date
        print(
            f"{item.table:20} scanned={item.scanned:<6} updated={item.updated:<6} "
            f"skipped_missing_date={item.skipped_missing_date}"
        )
    print("-" * 72)
    print(
        f"TOTAL                scanned={total_scanned:<6} updated={total_updated:<6} "
        f"skipped_missing_date={total_skipped}"
    )


async def run_backfill(*, dry_run: bool) -> None:
    engine = get_engine()
    try:
        async with engine.begin() as conn:
            stats: list[BackfillStats] = []

            for table_name in ("tasks", "routines", "brain_dumps", "calendar_entries"):
                stats.append(
                    await _backfill_existing_date_table(
                        conn, table_name=table_name, dry_run=dry_run
                    )
                )

            stats.append(
                await _backfill_datetime_derived_table(
                    conn,
                    table_name="messages",
                    datetime_column="created_at",
                    dry_run=dry_run,
                )
            )
            stats.append(
                await _backfill_datetime_derived_table(
                    conn,
                    table_name="push_notifications",
                    datetime_column="sent_at",
                    dry_run=dry_run,
                )
            )

            if dry_run:
                await conn.rollback()

            _print_stats(stats, dry_run=dry_run)
    finally:
        await close_engine()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill date/day_id columns for day-scoped tables."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview rows to update without persisting changes.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    print(f"Started at: {datetime.now(UTC).isoformat()}")
    asyncio.run(run_backfill(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
