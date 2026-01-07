#!/usr/bin/env python3
"""Migrate data from local dev database to production.

Usage:
    poetry run python scripts/migrate_data_to_production.py

Environment Variables:
    SOURCE_DATABASE_URL - Source database URL (defaults to local dev)
    DEST_DATABASE_URL   - Destination database URL (required - production)

IMPORTANT: Use postgresql+psycopg:// (not psycopg2) - this project uses psycopg v3.

Example:
    DEST_DATABASE_URL="postgresql+psycopg://user:pass@host/db" \
    poetry run python scripts/migrate_data_to_production.py
"""

from __future__ import annotations

import asyncio
import os
import re
import sys
from typing import Any

from sqlalchemy import MetaData, Table, text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine


def normalize_postgres_url(url: str) -> str:
    """Normalize PostgreSQL URL to use psycopg (v3) driver.

    Converts various PostgreSQL URL formats to postgresql+psycopg://:
    - postgres://         -> postgresql+psycopg://
    - postgresql://       -> postgresql+psycopg://
    - postgresql+psycopg2:// -> postgresql+psycopg://
    - postgresql+asyncpg:// -> postgresql+psycopg://
    """
    if not url:
        return url

    pattern = r"^(postgres(?:ql)?(?:\+\w+)?)://"
    replacement = "postgresql+psycopg://"

    return re.sub(pattern, replacement, url)

# Tables in order of dependencies (parent tables first)
# This ensures foreign key constraints are satisfied
TABLE_NAMES = [
    "users",
    "calendars",
    "calendar_entries",
    "task_definitions",
    "routines",
    "day_templates",
    "days",
    "tasks",
    "auth_tokens",
    "push_subscriptions",
]


def get_source_url() -> str:
    """Get source database URL (local dev by default)."""
    url = os.environ.get(
        "SOURCE_DATABASE_URL",
        "postgresql+psycopg://lykke:password@localhost:5432/lykke_dev",
    )
    return normalize_postgres_url(url)


def get_dest_url() -> str:
    """Get destination database URL (required)."""
    url = os.environ.get("DEST_DATABASE_URL")
    if not url:
        print("\n❌ Error: DEST_DATABASE_URL environment variable is required")
        print("\nExample:")
        print('  DEST_DATABASE_URL="postgresql+psycopg://user:pass@host/db" \\')
        print("  poetry run python scripts/migrate_data_to_production.py")
        sys.exit(1)

    return normalize_postgres_url(url)


def mask_password(url: str) -> str:
    """Mask password in database URL for display."""
    import re

    return re.sub(r"(://[^:]+:)[^@]+(@)", r"\1****\2", url)


async def fetch_all_rows(
    conn: AsyncConnection, table: Table
) -> list[dict[str, Any]]:
    """Fetch all rows from a table."""
    result = await conn.execute(table.select())
    rows = result.fetchall()
    return [dict(row._mapping) for row in rows]


async def insert_rows(
    conn: AsyncConnection, table: Table, rows: list[dict[str, Any]]
) -> int:
    """Insert rows into a table, returning count of inserted rows."""
    if not rows:
        return 0

    # Insert in batches to avoid memory issues
    batch_size = 1000
    total = 0

    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        await conn.execute(table.insert().values(batch))
        total += len(batch)

    return total


async def get_row_count(conn: AsyncConnection, table_name: str) -> int:
    """Get the current row count for a table."""
    result = await conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
    return result.scalar() or 0


async def truncate_table(conn: AsyncConnection, table_name: str) -> None:
    """Truncate a table (CASCADE to handle foreign keys)."""
    await conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))


async def migrate_table(
    source_conn: AsyncConnection,
    dest_conn: AsyncConnection,
    source_metadata: MetaData,
    dest_metadata: MetaData,
    table_name: str,
    mode: str,
) -> tuple[int, int]:
    """Migrate a single table. Returns (source_count, migrated_count)."""
    source_table = source_metadata.tables.get(table_name)
    dest_table = dest_metadata.tables.get(table_name)

    if source_table is None:
        print(f"  ⚠️  Table '{table_name}' not found in source database")
        return (0, 0)

    if dest_table is None:
        print(f"  ⚠️  Table '{table_name}' not found in destination database")
        return (0, 0)

    # Fetch source data
    rows = await fetch_all_rows(source_conn, source_table)
    source_count = len(rows)

    if source_count == 0:
        print(f"  📭 {table_name}: No data to migrate")
        return (0, 0)

    # Check destination
    dest_count = await get_row_count(dest_conn, table_name)

    if mode == "skip" and dest_count > 0:
        print(f"  ⏭️  {table_name}: Skipped ({dest_count} rows already exist)")
        return (source_count, 0)

    if mode == "truncate" and dest_count > 0:
        await truncate_table(dest_conn, table_name)
        print(f"  🗑️  {table_name}: Truncated {dest_count} existing rows")

    # Insert data
    migrated = await insert_rows(dest_conn, dest_table, rows)
    print(f"  ✅ {table_name}: Migrated {migrated} rows")

    return (source_count, migrated)


async def run_migration(mode: str) -> None:
    """Run the full migration."""
    source_url = get_source_url()
    dest_url = get_dest_url()

    print("\n" + "=" * 60)
    print("🚀 Database Migration: Dev → Production")
    print("=" * 60)
    print(f"\n📤 Source:      {mask_password(source_url)}")
    print(f"📥 Destination: {mask_password(dest_url)}")
    print(f"📋 Mode:        {mode}")
    print()

    # Create engines
    source_engine: AsyncEngine = create_async_engine(source_url)
    dest_engine: AsyncEngine = create_async_engine(dest_url)

    try:
        # Reflect metadata from both databases
        source_metadata = MetaData()
        dest_metadata = MetaData()

        async with source_engine.connect() as source_conn:
            await source_conn.run_sync(
                lambda conn: source_metadata.reflect(bind=conn)
            )

        async with dest_engine.connect() as dest_conn:
            await dest_conn.run_sync(lambda conn: dest_metadata.reflect(bind=conn))

        # Show summary before migration
        print("📊 Source Database Summary:")
        async with source_engine.connect() as source_conn:
            for table_name in TABLE_NAMES:
                if table_name in source_metadata.tables:
                    count = await get_row_count(source_conn, table_name)
                    print(f"   {table_name}: {count} rows")

        print("\n📊 Destination Database Summary (before):")
        async with dest_engine.connect() as dest_conn:
            for table_name in TABLE_NAMES:
                if table_name in dest_metadata.tables:
                    count = await get_row_count(dest_conn, table_name)
                    print(f"   {table_name}: {count} rows")

        # Confirm before proceeding
        print("\n" + "=" * 60)
        print("⚠️  WARNING: This will modify the production database!")
        print("=" * 60)
        response = input("\nType 'yes' to proceed: ")

        if response.lower() != "yes":
            print("\n❌ Migration cancelled.")
            return

        # Run migration
        print("\n🔄 Starting migration...")
        print("-" * 40)

        total_source = 0
        total_migrated = 0

        async with source_engine.connect() as source_conn:
            async with dest_engine.begin() as dest_conn:
                for table_name in TABLE_NAMES:
                    source_count, migrated = await migrate_table(
                        source_conn,
                        dest_conn,
                        source_metadata,
                        dest_metadata,
                        table_name,
                        mode,
                    )
                    total_source += source_count
                    total_migrated += migrated

        # Show final summary
        print("\n" + "-" * 40)
        print("📊 Destination Database Summary (after):")
        async with dest_engine.connect() as dest_conn:
            for table_name in TABLE_NAMES:
                if table_name in dest_metadata.tables:
                    count = await get_row_count(dest_conn, table_name)
                    print(f"   {table_name}: {count} rows")

        print("\n" + "=" * 60)
        print(f"✅ Migration complete!")
        print(f"   Total rows in source: {total_source}")
        print(f"   Total rows migrated:  {total_migrated}")
        print("=" * 60 + "\n")

    finally:
        await source_engine.dispose()
        await dest_engine.dispose()


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate data from local dev database to production",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Skip tables that already have data
  poetry run python scripts/migrate_data_to_production.py --mode skip

  # Truncate existing data before migrating
  poetry run python scripts/migrate_data_to_production.py --mode truncate

Environment Variables:
  SOURCE_DATABASE_URL  - Source database (default: local dev)
  DEST_DATABASE_URL    - Destination database (required)
        """,
    )
    parser.add_argument(
        "--mode",
        choices=["skip", "truncate"],
        default="skip",
        help="How to handle existing data: 'skip' (default) or 'truncate'",
    )

    args = parser.parse_args()

    asyncio.run(run_migration(args.mode))


if __name__ == "__main__":
    main()

