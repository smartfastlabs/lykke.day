"""Unit tests for TaskRepository mapper methods."""

from datetime import date as dt_date
from uuid import uuid4

import pytest

from lykke.domain.entities import TaskEntity
from lykke.domain.value_objects.task import (
    TaskCategory,
    TaskFrequency,
    TaskStatus,
    TaskType,
)
from lykke.infrastructure.repositories import TaskRepository


def test_entity_to_row_converts_enums_to_values():
    """Test that entity_to_row converts enum instances to their string values.
    
    This is a regression test for a bug where str(task.status) was producing
    'TaskStatus.NOT_STARTED' instead of 'NOT_STARTED', causing deserialization to fail.
    """
    user_id = uuid4()
    test_date = dt_date(2026, 1, 12)
    
    # Create a task entity with various enum values
    task = TaskEntity(
        id=uuid4(),
        user_id=user_id,
        name="Enum Test Task",
        status=TaskStatus.NOT_STARTED,
        type=TaskType.CHORE,
        description="Testing enum serialization",
        category=TaskCategory.CLEANING,
        frequency=TaskFrequency.WEEKLY,
        scheduled_date=test_date,
    )
    
    # Convert to row (simulating save to database)
    row = TaskRepository.entity_to_row(task)
    
    # Verify the row has enum VALUES as strings, not enum representations
    # Should be "NOT_STARTED" not "TaskStatus.NOT_STARTED"
    assert row["status"] == "NOT_STARTED", f"Expected 'NOT_STARTED', got {row['status']!r}"
    assert row["type"] == "CHORE", f"Expected 'CHORE', got {row['type']!r}"
    assert row["category"] == "CLEANING", f"Expected 'CLEANING', got {row['category']!r}"
    assert row["frequency"] == "WEEKLY", f"Expected 'WEEKLY', got {row['frequency']!r}"


def test_row_to_entity_converts_string_values_to_enums():
    """Test that row_to_entity converts string values back to enum instances."""
    user_id = uuid4()
    test_date = dt_date(2026, 1, 12)
    task_id = uuid4()
    
    row = {
        "id": task_id,
        "user_id": user_id,
        "date": test_date,
        "scheduled_date": test_date,
        "name": "String enum task",
        "status": "NOT_STARTED",  # String value, not enum
        "type": "CHORE",
        "description": "Test description",
        "category": "CLEANING",
        "frequency": "WEEKLY",
        "completed_at": None,
        "schedule": None,
        "routine_id": None,
        "tags": [],
        "actions": [],
    }
    
    # Convert to entity (simulating load from database)
    entity = TaskRepository.row_to_entity(row)
    
    # Verify enums are properly restored
    assert entity.status == TaskStatus.NOT_STARTED
    assert isinstance(entity.status, TaskStatus)
    assert entity.type == TaskType.CHORE
    assert isinstance(entity.type, TaskType)
    assert entity.category == TaskCategory.CLEANING
    assert isinstance(entity.category, TaskCategory)
    assert entity.frequency == TaskFrequency.WEEKLY
    assert isinstance(entity.frequency, TaskFrequency)


def test_entity_to_row_and_back_roundtrip():
    """Test that converting entity->row->entity preserves all enum values correctly."""
    user_id = uuid4()
    test_date = dt_date(2026, 1, 12)
    
    # Create a task entity
    original_task = TaskEntity(
        id=uuid4(),
        user_id=user_id,
        name="Roundtrip Test Task",
        status=TaskStatus.NOT_STARTED,
        type=TaskType.CHORE,
        description="Testing roundtrip serialization",
        category=TaskCategory.CLEANING,
        frequency=TaskFrequency.WEEKLY,
        scheduled_date=test_date,
    )
    
    # Convert to row and back
    row = TaskRepository.entity_to_row(original_task)
    restored_task = TaskRepository.row_to_entity(row)
    
    # Verify all enum fields are preserved
    assert restored_task.status == original_task.status
    assert restored_task.type == original_task.type
    assert restored_task.category == original_task.category
    assert restored_task.frequency == original_task.frequency
    assert restored_task.name == original_task.name
    assert restored_task.id == original_task.id
    assert restored_task.user_id == original_task.user_id
