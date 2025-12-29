"""Import all data from the data/ directory into the database."""

import asyncio
import json
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

from loguru import logger
from sqlalchemy.dialects.postgresql import insert as pg_insert

from planned.core.config import settings
from planned.domain.entities import (
    AuthToken,
    Calendar,
    DayTemplate,
    PushSubscription,
    Routine,
    TaskDefinition,
)
from planned.infrastructure.database import get_engine
from planned.infrastructure.repositories import (
    AuthTokenRepository,
    CalendarRepository,
    DayTemplateRepository,
    PushSubscriptionRepository,
    RoutineRepository,
    TaskDefinitionRepository,
)


def load_json_file(file_path: Path) -> dict[str, Any]:
    """Load and parse a JSON file."""
    with open(file_path) as f:
        return json.load(f)


async def import_auth_tokens(data_path: Path) -> int:
    """Import auth tokens from data/auth-tokens/ directory."""
    auth_tokens_dir = data_path / "auth-tokens"
    if not auth_tokens_dir.exists():
        logger.warning(f"Auth tokens directory not found: {auth_tokens_dir}")
        return 0

    repo = AuthTokenRepository()  # type: ignore[type-abstract]
    count = 0

    for json_file in auth_tokens_dir.glob("*.json"):
        try:
            data = load_json_file(json_file)
            # Parse datetime strings if present
            if data.get("expires_at"):
                dt_str = data["expires_at"].replace("Z", "+00:00")
                data["expires_at"] = datetime.fromisoformat(dt_str)
            if data.get("created_at"):
                dt_str = data["created_at"].replace("Z", "+00:00")
                data["created_at"] = datetime.fromisoformat(dt_str)

            auth_token = AuthToken.model_validate(data, from_attributes=True)
            await repo.put(auth_token)
            count += 1
            logger.info(f"Imported auth token: {auth_token.id}")
        except Exception as e:
            logger.error(f"Error importing auth token from {json_file}: {e}")

    return count


async def import_calendars(data_path: Path) -> int:
    """Import calendars from data/calendars/ directory."""
    calendars_dir = data_path / "calendars"
    if not calendars_dir.exists():
        logger.warning(f"Calendars directory not found: {calendars_dir}")
        return 0

    repo = CalendarRepository()  # type: ignore[type-abstract]
    count = 0

    for json_file in calendars_dir.glob("*.json"):
        try:
            data = load_json_file(json_file)
            # Parse datetime strings if present
            if data.get("last_sync_at"):
                dt_str = data["last_sync_at"].replace("Z", "+00:00")
                data["last_sync_at"] = datetime.fromisoformat(dt_str)

            calendar = Calendar.model_validate(data, from_attributes=True)
            await repo.put(calendar)
            count += 1
            logger.info(f"Imported calendar: {calendar.id}")
        except Exception as e:
            logger.error(f"Error importing calendar from {json_file}: {e}")

    return count


async def import_push_subscriptions(data_path: Path) -> int:
    """Import push subscriptions from data/push-subscriptions/ directory."""
    push_subscriptions_dir = data_path / "push-subscriptions"
    if not push_subscriptions_dir.exists():
        logger.warning(
            f"Push subscriptions directory not found: {push_subscriptions_dir}"
        )
        return 0

    repo = PushSubscriptionRepository()  # type: ignore[type-abstract]
    count = 0

    for json_file in push_subscriptions_dir.glob("*.json"):
        try:
            data = load_json_file(json_file)
            # Parse datetime strings if present
            if data.get("created_at"):
                dt_str = data["created_at"].replace("Z", "+00:00")
                data["created_at"] = datetime.fromisoformat(dt_str)

            push_subscription = PushSubscription.model_validate(
                data, from_attributes=True
            )
            await repo.put(push_subscription)
            count += 1
            logger.info(f"Imported push subscription: {push_subscription.id}")
        except Exception as e:
            logger.error(f"Error importing push subscription from {json_file}: {e}")

    return count


async def import_day_templates(data_path: Path) -> int:
    """Import day templates from data/config/day-templates/ directory."""
    day_templates_dir = data_path / "config" / "day-templates"
    if not day_templates_dir.exists():
        logger.warning(f"Day templates directory not found: {day_templates_dir}")
        return 0

    repo = DayTemplateRepository()  # type: ignore[type-abstract]
    count = 0

    for json_file in day_templates_dir.glob("*.json"):
        try:
            data = load_json_file(json_file)
            # Use filename without extension as the slug
            template_slug = json_file.stem
            data["slug"] = template_slug

            # Handle legacy "routines" field - map to "tasks"
            if "routines" in data and "tasks" not in data:
                data["tasks"] = data.pop("routines")

            day_template = DayTemplate.model_validate(data, from_attributes=True)
            await repo.put(day_template)
            count += 1
            logger.info(f"Imported day template: {day_template.slug}")
        except Exception as e:
            logger.error(f"Error importing day template from {json_file}: {e}")

    return count


def serialize_for_jsonb(value: Any) -> Any:
    """Recursively serialize values for JSONB storage, converting time objects to strings."""
    if isinstance(value, (time, date, datetime)):
        # Convert time/date/datetime to ISO format string
        return value.isoformat()
    elif isinstance(value, dict):
        return {k: serialize_for_jsonb(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [serialize_for_jsonb(item) for item in value]
    else:
        return value


async def upsert_config_object(
    repo: Any,
    obj: Any,
) -> None:
    """Upsert a config object with custom JSONB serialization."""
    engine = get_engine()
    row = type(repo).entity_to_row(obj)  # type: ignore[misc]
    table = repo.table

    # Serialize JSONB fields to ensure time objects are converted to strings
    # For RoutineRepository, routine_schedule and tasks are JSONB fields that may contain time objects
    # We serialize any dict/list values that might contain time objects
    for key, value in row.items():
        if isinstance(value, (dict, list)):
            row[key] = serialize_for_jsonb(value)

    async with engine.begin() as conn:
        # Use PostgreSQL INSERT ... ON CONFLICT DO UPDATE
        insert_stmt = pg_insert(table).values(**row)
        update_dict = {k: v for k, v in row.items() if k != "id"}
        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=["id"],
            set_=update_dict,
        )
        await conn.execute(upsert_stmt)


async def import_task_definitions(data_path: Path) -> int:
    """Import task definitions from data/config/task-definitions/ directory."""
    task_definitions_dir = data_path / "config" / "task-definitions"
    if not task_definitions_dir.exists():
        logger.warning(f"Task definitions directory not found: {task_definitions_dir}")
        return 0

    repo = TaskDefinitionRepository()  # type: ignore[type-abstract]
    count = 0

    for json_file in task_definitions_dir.glob("*.json"):
        try:
            data = load_json_file(json_file)
            # Use filename without extension as the ID
            task_definition_id = json_file.stem
            data["id"] = task_definition_id

            task_definition = TaskDefinition.model_validate(data, from_attributes=True)
            await upsert_config_object(repo, task_definition)
            count += 1
            logger.info(f"Imported task definition: {task_definition.id}")
        except Exception as e:
            logger.error(f"Error importing task definition from {json_file}: {e}")

    return count


async def import_routines(data_path: Path) -> int:
    """Import routines from data/config/routines/ directory."""
    routines_dir = data_path / "config" / "routines"
    if not routines_dir.exists():
        logger.warning(f"Routines directory not found: {routines_dir}")
        return 0

    repo = RoutineRepository()  # type: ignore[type-abstract]
    count = 0

    for json_file in routines_dir.glob("*.json"):
        try:
            data = load_json_file(json_file)
            # Use filename without extension as the ID
            routine_id = json_file.stem
            data["id"] = routine_id

            routine = Routine.model_validate(data, from_attributes=True)
            await upsert_config_object(repo, routine)
            count += 1
            logger.info(f"Imported routine: {routine.id}")
        except Exception as e:
            logger.error(f"Error importing routine from {json_file}: {e}")

    return count


async def main():
    """Import all data from the data directory."""
    data_path = Path(settings.DATA_PATH)
    if not data_path.exists():
        logger.error(f"Data path does not exist: {data_path}")
        return

    logger.info(f"Starting data import from {data_path}")

    counts = {
        "auth_tokens": 0,
        "calendars": 0,
        "push_subscriptions": 0,
        "day_templates": 0,
        "task_definitions": 0,
        "routines": 0,
    }

    try:
        counts["auth_tokens"] = await import_auth_tokens(data_path)
        counts["calendars"] = await import_calendars(data_path)
        counts["push_subscriptions"] = await import_push_subscriptions(data_path)
        counts["day_templates"] = await import_day_templates(data_path)
        counts["task_definitions"] = await import_task_definitions(data_path)
        counts["routines"] = await import_routines(data_path)

        logger.info("Data import completed successfully!")
        logger.info(f"Summary: {counts}")
    except Exception as e:
        logger.error(f"Error during data import: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
