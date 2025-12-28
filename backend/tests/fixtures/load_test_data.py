"""Fixture for loading test data from tests/data directory into the database."""

import json
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio

from planned.domain.entities import (
    Day,
    DayTemplate,
    Event,
    Routine,
    TaskDefinition,
)
from planned.infrastructure.repositories import (
    DayRepository,
    DayTemplateRepository,
    EventRepository,
    RoutineRepository,
    TaskDefinitionRepository,
)

# Path to test data directory
TEST_DATA_DIR = Path(__file__).parent.parent / "data"


def load_json_file(path: Path) -> dict[str, Any]:
    """Load a JSON file and return its contents."""
    with open(path, "r") as f:
        return json.load(f)


async def load_config_objects():
    """Load all config objects from tests/data/config/ into the database."""
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from planned.infrastructure.database import get_engine
    from planned.infrastructure.repositories.base.schema import (
        day_templates,
        routines,
        task_definitions,
    )

    config_dir = TEST_DATA_DIR / "config"
    engine = get_engine()

    # Load day templates
    day_templates_dir = config_dir / "day-templates"
    if day_templates_dir.exists():
        for template_file in day_templates_dir.glob("*.json"):
            data = load_json_file(template_file)
            # Use filename (without .json) as id if not specified
            if "id" not in data:
                data["id"] = template_file.stem
            template = DayTemplate.model_validate(data)
            # Use repository mapper to convert to row
            row = DayTemplateRepository.entity_to_row(template)  # type: ignore[attr-defined]
            async with engine.begin() as conn:
                stmt = pg_insert(day_templates).values(**row)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["id"], set_={k: v for k, v in row.items() if k != "id"}
                )
                await conn.execute(stmt)

    # Load task definitions
    task_definitions_dir = config_dir / "task-definitions"
    if task_definitions_dir.exists():
        for task_def_file in task_definitions_dir.glob("*.json"):
            data = load_json_file(task_def_file)
            # Use filename (without .json) as id if not specified
            if "id" not in data:
                data["id"] = task_def_file.stem
            task_def = TaskDefinition.model_validate(data)
            # Use repository mapper to convert to row
            row = TaskDefinitionRepository.entity_to_row(task_def)  # type: ignore[attr-defined]
            async with engine.begin() as conn:
                stmt = pg_insert(task_definitions).values(**row)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["id"], set_={k: v for k, v in row.items() if k != "id"}
                )
                await conn.execute(stmt)

    # Load routines
    routines_dir = config_dir / "routines"
    if routines_dir.exists():
        for routine_file in routines_dir.glob("*.json"):
            data = load_json_file(routine_file)
            # Use filename (without .json) as id if not specified
            if "id" not in data:
                data["id"] = routine_file.stem
            routine = Routine.model_validate(data)
            # Use repository mapper to convert to row
            row = RoutineRepository.entity_to_row(routine)  # type: ignore[attr-defined]
            async with engine.begin() as conn:
                stmt = pg_insert(routines).values(**row)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["id"], set_={k: v for k, v in row.items() if k != "id"}
                )
                await conn.execute(stmt)


async def load_date_scoped_objects():
    """Load all date-scoped objects from tests/data/dates/ into the database."""
    dates_dir = TEST_DATA_DIR / "dates"

    if not dates_dir.exists():
        return

    day_repo = DayRepository()
    event_repo = EventRepository()

    # Iterate through date directories (e.g., 2025-11-27/)
    for date_dir in dates_dir.iterdir():
        if not date_dir.is_dir():
            continue

        # Load day.json if it exists
        day_file = date_dir / "day.json"
        if day_file.exists():
            data = load_json_file(day_file)
            # Ensure date is set from directory name
            if "date" not in data:
                data["date"] = date_dir.name
            day = Day.model_validate(data)
            await day_repo.put(day)

        # Load events from events/ subdirectory
        events_dir = date_dir / "events"
        if events_dir.exists():
            for event_file in events_dir.glob("*.json"):
                data = load_json_file(event_file)
                # Use filename (without .json) as id if not specified
                if "id" not in data:
                    data["id"] = event_file.stem
                event = Event.model_validate(data)
                await event_repo.put(event)


@pytest_asyncio.fixture
async def load_test_data(clear_database):
    """Load all test data from tests/data/ into the database.
    
    This fixture depends on clear_database to ensure it runs after the database
    is cleared but before tests run.
    """
    await load_config_objects()
    await load_date_scoped_objects()

