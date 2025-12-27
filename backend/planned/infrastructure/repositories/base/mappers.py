"""Entity to/from database row conversion functions."""

import json
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


def entity_to_row(entity: BaseModel, table_name: str) -> dict[str, Any]:
    """Convert an entity to a database row dict.
    
    Handles JSONB serialization, enum conversion, and date extraction.
    """
    row: dict[str, Any] = {}
    
    # Get model dict (exclude unset fields)
    data = entity.model_dump(exclude_unset=False, by_alias=False)
    
    for key, value in data.items():
        if value is None:
            row[key] = None
        elif isinstance(value, (dict, list)):
            # Serialize to JSON for JSONB columns
            row[key] = json.loads(json.dumps(value, default=str))
        elif isinstance(value, (date, datetime)):
            row[key] = value
        elif hasattr(value, "value"):  # Enum
            row[key] = value.value if hasattr(value, "value") else str(value)
        elif isinstance(value, BaseModel):
            # Nested Pydantic model - serialize to dict
            row[key] = json.loads(value.model_dump_json())
        else:
            row[key] = value
    
    # Handle special cases for date-scoped entities
    if table_name in ("events", "messages", "tasks"):
        if table_name == "events" and "starts_at" in row:
            # Extract date from starts_at
            row["date"] = row["starts_at"].date() if isinstance(row["starts_at"], datetime) else row["starts_at"]
        elif table_name == "messages" and "sent_at" in row:
            # Extract date from sent_at
            row["date"] = row["sent_at"].date() if isinstance(row["sent_at"], datetime) else row["sent_at"]
        elif table_name == "tasks" and "scheduled_date" in row:
            # Use scheduled_date as date
            row["date"] = row["scheduled_date"]
    
    return row


def row_to_entity(row: dict[str, Any], entity_class: type[BaseModel]) -> BaseModel:
    """Convert a database row dict to an entity.
    
    Handles JSONB deserialization and enum conversion.
    Removes database-only fields like 'date' for date-scoped entities
    (the entity computes date from datetime fields).
    """
    # Convert row dict, handling JSONB fields that may be dicts/lists
    data: dict[str, Any] = {}
    
    # Special handling for Day entity - convert id (date string) to date field
    if entity_class.__name__ == "Day" and "id" in row and "date" not in row:
        from datetime import datetime as dt
        try:
            # id is a date string like "2025-11-27", convert to date object
            data["date"] = dt.strptime(row["id"], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            # If conversion fails, try to parse as ISO format
            try:
                data["date"] = dt.fromisoformat(row["id"]).date()
            except (ValueError, TypeError):
                pass  # Will let Pydantic validation handle the error
    
    # Remove 'date' field if present - it's database-only for querying
    # The entity will compute it from datetime fields
    row_without_date = {k: v for k, v in row.items() if k != "date"}
    
    for key, value in row_without_date.items():
        if key == "id" and entity_class.__name__ == "Day":
            # Skip id for Day, we've already converted it to date
            continue
        if value is None:
            data[key] = None
        elif isinstance(value, (dict, list)):
            # JSONB fields - pass through as-is (Pydantic will validate)
            data[key] = value
        else:
            data[key] = value
    
    # Create entity using model_validate (handles enum conversion, nested models, etc.)
    return entity_class.model_validate(data, from_attributes=True)

