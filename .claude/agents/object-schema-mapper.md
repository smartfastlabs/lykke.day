---
name: Object Schema Mapper Guide
description: Guide for working with the 4-object architecture (Entities, Data Objects, Tables, Schemas)
tools:
  - read
  - write
  - shell
  - grep
---

# Object, Schema, and Mapper Architecture Guide

## Overview

This codebase has **FOUR distinct types of objects** that represent data at different layers. Understanding when to use each type and how to map between them is critical to maintaining clean architecture.

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

### 2. **Data Objects** (`lykke/domain/data_objects/`)

**What:** "Anemic Domain Entities" - dataclasses that need database persistence but lack business logic  
**Purpose:** Store data in the database for things that don't warrant full entity treatment  
**Example:** `TaskDefinition`, `TimeBlockDefinition`, `PushSubscription`, `AuthToken`

```python
@dataclass(kw_only=True)
class TaskDefinition(BaseEntityObject):
    user_id: UUID
    name: str
    description: str
    type: TaskType
```

**Used in:**

- Database persistence (have their own dedicated tables)
- Referenced by entities (e.g., `TaskEntity` has a `task_definition_id` foreign key)
- Application and domain layers for simple data management

**Key Difference from Entities:**

- No business methods or complex business logic
- Just data storage with basic validation
- Always have their own database table (not embedded as JSONB)
- Simpler than full entities but still need persistence

**Key Difference from Value Objects:**

- **Data Objects** have their own database tables and IDs
- **Value Objects** are embedded as JSONB within other entities' tables
- Data Objects are referenced by ID, Value Objects are embedded by value

> **💡 Value Objects Note:**  
> Value Objects (in `lykke/domain/value_objects/`) like `Action`, `Alarm`, `TaskSchedule`, `RoutineSchedule` are immutable dataclasses that are ONLY stored as JSONB within entity tables. They don't have their own tables or IDs. If something needs its own table, it should be a Data Object or Entity, not a Value Object.

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

### ✅ Checklist for New Object Type

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

### ✅ Checklist for Adding Field to Existing Object

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

### ❌ Mistake 4: Storing Data Objects as JSONB Instead of Their Own Table

**Wrong:**

```python
# In entity - embedding a Data Object
class TaskEntity:
    task_definition: TaskDefinition  # ❌ Data Object should be referenced by ID!

# In table - storing Data Object as JSONB
class Task(Base):
    task_definition = Column(JSONB)  # ❌ Should have task_definition_id instead!
```

**Right:**

```python
# In entity - reference Data Object by ID
class TaskEntity:
    task_definition_id: UUID  # ✅ Reference by ID
    task_definition: TaskDefinition  # ✅ Loaded from repository, not embedded

# In table - foreign key to Data Object's table
class Task(Base):
    task_definition_id = Column(PGUUID, nullable=False)  # ✅ Foreign key!

# TaskDefinition has its own table
class TaskDefinition(Base):
    __tablename__ = "task_definitions"
    id = Column(PGUUID, primary_key=True)  # ✅ Own table with ID
```

**Remember:**

- **Data Objects** → Own table, referenced by ID
- **Value Objects** → Embedded as JSONB

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

**Important:** Only **Value Objects** should be stored as JSONB, never Data Objects!

- ✅ **Value Objects** (e.g., `Action`, `Alarm`, `TaskSchedule`) → Embedded as JSONB
- ❌ **Data Objects** (e.g., `TaskDefinition`) → Have their own tables, referenced by ID

When an entity contains embedded value objects (stored as JSONB in the parent's table):

**In Entity:**

```python
@dataclass(kw_only=True)
class TaskEntity:
    schedule: TaskSchedule | None  # Value object embedded as JSONB
    actions: list[Action]  # List of value objects as JSONB
```

**In Repository `entity_to_row()`:**

```python
from lykke.core.utils.serialization import dataclass_to_json_dict

if task.schedule:
    row["schedule"] = dataclass_to_json_dict(task.schedule)

if task.actions:
    row["actions"] = [dataclass_to_json_dict(action) for action in task.actions]
```

**In Repository `row_to_entity()`:**

```python
if isinstance(data.get("schedule"), dict):
    data["schedule"] = TaskSchedule(**data["schedule"])

if data.get("actions"):
    data["actions"] = [
        Action(**action) if isinstance(action, dict) else action
        for action in data["actions"]
    ]
```

**In Mapper:**

```python
def map_task_to_schema(task: TaskEntity) -> TaskSchema:
    schedule_schema = map_task_schedule_to_schema(task.schedule) if task.schedule else None
    action_schemas = [map_action_to_schema(action) for action in task.actions]
    return TaskSchema(
        schedule=schedule_schema,
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

| Layer          | Object Type           | Example                        |
| -------------- | --------------------- | ------------------------------ |
| Presentation   | Schema (Pydantic)     | `TaskSchema`                   |
| Application    | Entity or Data Object | `TaskEntity`, `TaskDefinition` |
| Domain         | Entity or Data Object | `TaskEntity`, `TaskDefinition` |
| Infrastructure | Table (SQLAlchemy)    | `tasks_tbl`                    |
| Mappers        | Functions             | `map_task_to_schema()`         |

**Note:** Data Objects are "anemic entities" - they have database tables but no business logic.

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
2. **Data Objects** for things that need persistence but not business logic ("anemic entities")
3. **Value Objects** for immutable data embedded as JSONB (no own table)
4. **Schemas** for API contracts (presentation layer only)
5. **Tables** for database access (infrastructure layer only)
6. **Mappers** for entity → schema conversion (in `mappers.py`)
7. **Repository methods** for entity ↔ table conversion
8. **ALWAYS** update all layers when adding/changing objects
9. **NEVER** skip mappers or use wrong object type in a layer
10. **NEVER** store Data Objects as JSONB - they get their own tables!

---

**Decision Tree: Which Type Should I Use?**

```
Does it need business logic?
├─ YES → Entity (domain/entities/)
└─ NO → Does it need its own database table?
    ├─ YES → Data Object (domain/data_objects/)
    └─ NO → Value Object (domain/value_objects/, stored as JSONB)

Is it for the API?
└─ YES → Schema (presentation/api/schemas/)

Is it for the database?
└─ YES → Table (infrastructure/database/tables/)
```

---

When in doubt, follow an existing object through all layers as a template.
