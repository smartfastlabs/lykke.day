---
name: Object Schema Mapper Guide
description: Guide for working with Entities, Value Objects, Tables, Schemas
tools:
  - read
  - write
  - shell
  - grep
---

# Object, Schema, and Mapper Architecture Guide

## Overview

This codebase has **FOUR distinct types of objects** that represent data at
different layers: **Domain Entities**, **Domain Value Objects**, **SQLAlchemy
Tables**, and **API Schemas**. Understanding when to use each type and how to map
between them is critical to maintaining clean architecture.

---

## The Four Object Types

### 1. **Domain Entities** (`lykke/domain/entities/`)

**What:** Rich business objects with behavior and business logic  
**Purpose:** Core business model with invariants and rules  
**Example:** `CalendarEntrySeriesEntity`, `TaskEntity`, `DayEntity`

```python
@dataclass(kw_only=True)
class CalendarEntrySeriesEntity(BaseEntityObject):
    user_id: UUID
    calendar_id: UUID
    name: str
    platform_id: str
    # ... business fields

    def some_business_method(self) -> None:
        """Business logic lives here"""
        pass
```

**Used in:**

- Application layer (commands/queries)
- Repository input and return values

**DO NOT:**

- ❌ Return entities directly from API endpoints
- ❌ Use entities in Pydantic schemas
- ❌ Store entities directly in database

---

### 2. **Domain Value Objects** (`lykke/domain/value_objects/`)

**What:** Small domain types with no identity (dataclasses or enums)  
**Purpose:** Encapsulate typed fields, embedded JSONB structures, and request/response shapes  
**Examples:** `TimeWindow`, `Action`, `LLMRunResultSnapshot`, `BaseQuery`

```python
@dataclass(kw_only=True)
class TimeWindow(BaseValueObject):
    available_time: time | None = None
    start_time: time | None = None
    end_time: time | None = None
    cutoff_time: time | None = None
```

**Used in:**

- Entity fields (stored as JSONB)
- Query/update request objects
- Application logic (typed enums, structured snapshots)

**DO NOT:**

- ❌ Give value objects their own database tables
- ❌ Treat them as entities with identity

> **💡 Value Objects Note:**  
> Value objects are **not frozen** in this codebase. Treat them as immutable and
> create new instances (via `clone()` or constructors) instead of mutating.

---

### 3. **SQLAlchemy Tables** (`lykke/infrastructure/database/tables/`)

**What:** Database table definitions using SQLAlchemy Core  
**Purpose:** Define database schema and columns  
**Example:** `calendar_entry_series`, `tasks_tbl`

```python
class CalendarEntrySeries(Base):
    __tablename__ = "calendar_entry_series"

    id = Column(PGUUID, primary_key=True)
    user_id = Column(PGUUID, nullable=False)
    name = Column(String, nullable=False)
    # ... database columns
```

**Used in:**

- Repository implementations
- Alembic migrations
- Database queries

**DO NOT:**

- ❌ Pass table objects to application layer
- ❌ Import tables outside infrastructure layer
- ❌ Use SQLAlchemy objects in business logic

---

### 4. **API Schemas** (`lykke/presentation/api/schemas/`)

**What:** Pydantic models for HTTP API validation and serialization  
**Purpose:** Define API contracts (requests/responses)  
**Example:** `CalendarEntrySeriesSchema`, `TaskSchema`

```python
class CalendarEntrySeriesSchema(BaseEntitySchema):
    user_id: UUID
    calendar_id: UUID
    name: str
    platform_id: str
    # ... API fields that match what clients expect
```

**Used in:**

- FastAPI route parameters (request validation)
- FastAPI return types (response serialization)
- OpenAPI schema generation

**DO NOT:**

- ❌ Use schemas in application layer (commands/queries)
- ❌ Pass schemas to repositories
- ❌ Store schemas in database

---

## The Mapping Flow

### Reading Data (Database → API)

```
┌──────────────┐
│   Database   │
└──────┬───────┘
       │ (raw rows)
       ↓
┌──────────────────┐
│ SQLAlchemy Table │  infrastructure/database/tables/
└──────┬───────────┘
       │ row_to_entity()
       ↓
┌──────────────────┐
│ Domain Entity    │  domain/entities/
└──────┬───────────┘
       │ map_*_to_schema()
       ↓
┌──────────────────┐
│   API Schema     │  presentation/api/schemas/
└──────┬───────────┘
       │
       ↓
 JSON Response
```

### Writing Data (API → Database)

```
  JSON Request
       │
       ↓
┌──────────────────┐
│   API Schema     │  presentation/api/schemas/
└──────┬───────────┘
       │ (validated by Pydantic)
       ↓
┌──────────────────┐
│ Domain Entity    │  domain/entities/
│  (created from   │  (created in command/query)
│   schema data)   │
└──────┬───────────┘
       │ entity_to_row()
       ↓
┌──────────────────┐
│ SQLAlchemy Table │  infrastructure/database/tables/
└──────┬───────────┘
       │
       ↓
┌──────────────┐
│   Database   │
└──────────────┘
```

---

## Required Mappers for Each Object Type

When adding or modifying an object, you MUST update ALL of these:

### ✅ Checklist for New Entity

- [ ] **Domain Entity** - Create in `domain/entities/*.py`
- [ ] **SQLAlchemy Table** - Create in `infrastructure/database/tables/*.py`
- [ ] **API Schema** - Create in `presentation/api/schemas/*.py`
- [ ] **Repository** - Create in `infrastructure/repositories/*.py` with:
  - [ ] `entity_to_row()` method
  - [ ] `row_to_entity()` method
- [ ] **Mapper Function** - Add to `presentation/api/schemas/mappers.py`:
  - [ ] `map_*_to_schema()` function
- [ ] **Migration** - Create Alembic migration for database changes
- [ ] **Tests** - Add tests for all mappers

### ✅ Checklist for New Embedded Value Object Field

- [ ] **Value Object** - Create in `domain/value_objects/*.py`
- [ ] **Entity Field** - Add to `domain/entities/*.py`
- [ ] **Database Column** - Add JSONB column to table
- [ ] **Repository `entity_to_row()`** - Serialize with `dataclass_to_json_dict`
- [ ] **Repository `row_to_entity()`** - Rehydrate into value object
- [ ] **Schema/Mapper** - Add schema field + map in `mappers.py`
- [ ] **Migration** - Create Alembic migration for database column
- [ ] **Tests** - Add round-trip tests for serialization

### ✅ Checklist for Adding Field to Existing Entity

- [ ] **Domain Entity** - Add field to `domain/entities/*.py`
- [ ] **SQLAlchemy Table** - Add column to `infrastructure/database/tables/*.py`
- [ ] **API Schema** - Add field to `presentation/api/schemas/*.py`
- [ ] **Repository `entity_to_row()`** - Handle new field in conversion
- [ ] **Repository `row_to_entity()`** - Handle new field in conversion
- [ ] **Mapper** - Update `map_*_to_schema()` in `mappers.py` to include new field
- [ ] **Migration** - Create Alembic migration for database column
- [ ] **Tests** - Update tests to include new field

---

## Common Mistakes and How to Avoid Them

### ❌ Mistake 1: Using Schemas Where Entities Should Be Used

**Wrong:**

```python
# In a command handler
def execute(self, command: CreateTaskCommand) -> TaskSchema:  # ❌ Wrong!
    schema = TaskSchema(...)
    self.repository.add(schema)  # ❌ Repository expects entity!
```

**Right:**

```python
# In a command handler
def execute(self, command: CreateTaskCommand) -> TaskEntity:  # ✅ Correct!
    entity = TaskEntity(...)
    self.repository.add(entity)  # ✅ Entity goes to repository
    return entity
```

---

### ❌ Mistake 2: Missing Mapper Function

**Wrong:**

```python
# In a router
@router.get("/series/{id}")
async def get_series(entity: CalendarEntrySeriesEntity) -> CalendarEntrySeriesSchema:
    return entity  # ❌ Can't return entity directly!
```

**Right:**

```python
# In a router
@router.get("/series/{id}")
async def get_series(entity: CalendarEntrySeriesEntity) -> CalendarEntrySeriesSchema:
    return map_calendar_entry_series_to_schema(entity)  # ✅ Use mapper!
```

**Where to add mapper:**

```python
# In presentation/api/schemas/mappers.py
def map_calendar_entry_series_to_schema(
    series: CalendarEntrySeriesEntity,
) -> CalendarEntrySeriesSchema:
    """Convert CalendarEntrySeries entity to schema."""
    return CalendarEntrySeriesSchema(
        id=series.id,
        user_id=series.user_id,
        # ... map all fields
    )
```

---

### ❌ Mistake 3: Incomplete Repository Mapping

**Wrong:**

```python
# Adding new field to entity but forgetting repository
class TaskEntity:
    new_field: str  # ✅ Added to entity

# But repository still has old mapping
@staticmethod
def entity_to_row(task: TaskEntity) -> dict[str, Any]:
    return {
        "id": task.id,
        "name": task.name,
        # ❌ Missing new_field!
    }
```

**Right:**

```python
@staticmethod
def entity_to_row(task: TaskEntity) -> dict[str, Any]:
    return {
        "id": task.id,
        "name": task.name,
        "new_field": task.new_field,  # ✅ Added to mapping!
    }

@classmethod
def row_to_entity(cls, row: dict[str, Any]) -> TaskEntity:
    data = dict(row)
    # Handle new_field conversion if needed
    return TaskEntity(**data)  # ✅ new_field included!
```

---

### ❌ Mistake 4: Giving Value Objects Their Own Tables

**Wrong:**

```python
# In entity - embedding a Value Object
class TaskEntity:
    time_window: TimeWindow  # ✅ Value object

# In table - creating a separate table
class TimeWindowTable(Base):
    __tablename__ = "time_windows"  # ❌ Value objects should not have tables!
```

**Right:**

```python
# In table - store value object as JSONB on parent table
class Task(Base):
    time_window = Column(JSONB)  # ✅ Embedded value object
```

---

### ❌ Mistake 5: Wrong Object Type in Layer

**Wrong:**

```python
# Using schema in application layer
class CreateTaskCommand:
    def __init__(self, task_schema: TaskSchema):  # ❌ Schema in application layer!
        self.task_schema = task_schema
```

**Right:**

```python
# Using entity in application layer
class CreateTaskCommand:
    def __init__(self, **task_data):  # ✅ Raw data or entity
        self.task_data = task_data

    def execute(self):
        entity = TaskEntity(**self.task_data)  # ✅ Create entity
        self.repository.add(entity)
```

---

## Special Cases

### JSONB Fields (Embedded Value Objects)

**Important:** Only **Value Objects** should be stored as JSONB.

- ✅ **Value Objects** (e.g., `Action`, `Alarm`, `TimeWindow`) → Embedded as JSONB
- ❌ **Entities** (e.g., `TaskEntity`) → Have their own tables, referenced by ID

When an entity contains embedded value objects (stored as JSONB in the parent's table):

**In Entity:**

```python
@dataclass(kw_only=True)
class TaskEntity:
    time_window: TimeWindow | None  # Value object embedded as JSONB
    actions: list[Action]  # List of value objects as JSONB
```

**In Repository `entity_to_row()`:**

```python
from lykke.core.utils.serialization import dataclass_to_json_dict

if task.time_window:
    row["time_window"] = dataclass_to_json_dict(task.time_window)

if task.actions:
    row["actions"] = [dataclass_to_json_dict(action) for action in task.actions]
```

**In Repository `row_to_entity()`:**

```python
if isinstance(data.get("time_window"), dict):
    data["time_window"] = TimeWindow(**data["time_window"])

if data.get("actions"):
    data["actions"] = [
        Action(**action) if isinstance(action, dict) else action
        for action in data["actions"]
    ]
```

**In Mapper:**

```python
def map_task_to_schema(task: TaskEntity) -> TaskSchema:
    time_window_schema = (
        map_time_window_to_schema(task.time_window) if task.time_window else None
    )
    action_schemas = [map_action_to_schema(action) for action in task.actions]
    return TaskSchema(
        time_window=time_window_schema,
        actions=action_schemas,
        # ...
    )
```

---

### Enum Fields

Enums need special handling in repositories:

**To Database:**

```python
def entity_to_row(task: TaskEntity) -> dict[str, Any]:
    return {
        "status": task.status.value,  # Convert enum to string
    }
```

**From Database:**

```python
def row_to_entity(cls, row: dict[str, Any]) -> TaskEntity:
    if "status" in data and isinstance(data["status"], str):
        data["status"] = TaskStatus(data["status"])  # Convert string to enum
    return TaskEntity(**data)
```

---

### List/Array Fields

**To Database:**

```python
def entity_to_row(task: TaskEntity) -> dict[str, Any]:
    return {
        "tags": [tag.value for tag in task.tags],  # List of enums to strings
    }
```

**From Database:**

```python
def row_to_entity(cls, row: dict[str, Any]) -> TaskEntity:
    if data.get("tags") and isinstance(data["tags"], list):
        data["tags"] = [TaskTag(tag) for tag in data["tags"]]  # Strings to enums
    return TaskEntity(**data)
```

---

## Quick Reference: Object Type by Layer

| Layer          | Object Type               | Example                |
| -------------- | ------------------------- | ---------------------- |
| Presentation   | Schema (Pydantic)         | `TaskSchema`           |
| Application    | Entity or Value Object    | `TaskEntity`, `Action` |
| Domain         | Entity or Value Object    | `TaskEntity`, `Action` |
| Infrastructure | Table (SQLAlchemy)        | `tasks_tbl`            |
| Mappers        | Functions                 | `map_task_to_schema()` |

---

## Testing Your Mappers

Always test the full round trip:

```python
def test_task_mapping_round_trip():
    # Create entity
    entity = TaskEntity(id=uuid4(), name="Test")

    # Entity → Row → Entity
    row = TaskRepository.entity_to_row(entity)
    entity_from_row = TaskRepository.row_to_entity(row)
    assert entity == entity_from_row

    # Entity → Schema
    schema = map_task_to_schema(entity)
    assert schema.id == entity.id
    assert schema.name == entity.name
```

---

## Tools to Help

### Check for Missing Mappers

We have an automated script that checks for missing mappers, schemas, and repository methods:

```bash
# From backend/ directory
make check-mappers

# Or directly:
poetry run python scripts/check_mappers.py
```

This script will:

- ✅ Check that every entity has a corresponding schema
- ✅ Check that every entity has a mapper function
- ⚠️ Warn about entities without database tables (verify if intentional)
- ⚠️ Warn about repositories using default mapping methods

Run this script before committing to catch mapping issues early!

### Verify Repository Methods

```python
# Every repository MUST have both methods
class MyRepository(UserScopedBaseRepository):
    @staticmethod
    def entity_to_row(entity: MyEntity) -> dict[str, Any]:
        # Required!
        pass

    @classmethod
    def row_to_entity(cls, row: dict[str, Any]) -> MyEntity:
        # Required!
        pass
```

---

## Summary

**Golden Rules:**

1. **Entities** for business logic (application & domain layers)
2. **Value Objects** for typed fields and embedded JSONB (no own table)
3. **Schemas** for API contracts (presentation layer only)
4. **Tables** for database access (infrastructure layer only)
5. **Mappers** for entity → schema conversion (in `mappers.py`)
6. **Repository methods** for entity ↔ table conversion
7. **ALWAYS** update all layers when adding/changing objects
8. **NEVER** skip mappers or use wrong object type in a layer
9. **NEVER** give value objects their own tables

---

**Decision Tree: Which Type Should I Use?**

```
Does it need identity and lifecycle?
├─ YES → Entity (domain/entities/)
└─ NO → Value Object (domain/value_objects/)

Is it for the API?
└─ YES → Schema (presentation/api/schemas/)

Is it for the database?
└─ YES → Table (infrastructure/database/tables/)
```

---

When in doubt, follow an existing object through all layers as a template.
