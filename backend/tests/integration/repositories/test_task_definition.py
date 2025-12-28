"""Integration tests for TaskDefinitionRepository."""

import pytest
import pytest_asyncio

from planned.core.exceptions import exceptions
from planned.domain.value_objects.task import TaskDefinition, TaskType


@pytest.mark.asyncio
async def test_get(task_definition_repo, test_user):
    """Test getting a task definition by ID."""
    from uuid import UUID
    
    task_def = TaskDefinition(
        user_uuid=UUID(test_user.id),
        id="test-task",
        name="Test Task",
        description="Test description",
        type=TaskType.ACTIVITY,
    )
    await task_definition_repo.put(task_def)
    
    result = await task_definition_repo.get("test-task")
    
    assert result.id == "test-task"
    assert result.name == "Test Task"


@pytest.mark.asyncio
async def test_get_not_found(task_definition_repo):
    """Test getting a non-existent task definition raises NotFoundError."""
    with pytest.raises(exceptions.NotFoundError):
        await task_definition_repo.get("nonexistent")


@pytest.mark.asyncio
async def test_put(task_definition_repo, test_user):
    """Test creating a new task definition."""
    from uuid import UUID
    
    task_def = TaskDefinition(
        user_uuid=UUID(test_user.id),
        id="new-task",
        name="New Task",
        description="New description",
        type=TaskType.ACTIVITY,
    )
    
    result = await task_definition_repo.put(task_def)
    
    assert result.name == "New Task"
    assert result.type == TaskType.ACTIVITY


@pytest.mark.asyncio
async def test_all(task_definition_repo, test_user):
    """Test getting all task definitions."""
    from uuid import UUID
    
    task_def1 = TaskDefinition(
        user_uuid=UUID(test_user.id),
        id="task1",
        name="Task 1",
        description="Description 1",
        type=TaskType.ACTIVITY,
    )
    task_def2 = TaskDefinition(
        user_uuid=UUID(test_user.id),
        id="task2",
        name="Task 2",
        description="Description 2",
        type=TaskType.ACTIVITY,
    )
    await task_definition_repo.put(task_def1)
    await task_definition_repo.put(task_def2)
    
    all_defs = await task_definition_repo.all()
    
    def_ids = [d.id for d in all_defs]
    assert "task1" in def_ids
    assert "task2" in def_ids


@pytest.mark.asyncio
async def test_user_isolation(task_definition_repo, test_user, create_test_user):
    """Test that different users' task definitions are properly isolated."""
    from uuid import UUID
    
    task_def = TaskDefinition(
        user_uuid=UUID(test_user.id),
        id="user1-task",
        name="User1 Task",
        description="Description",
        type=TaskType.ACTIVITY,
    )
    await task_definition_repo.put(task_def)
    
    # Create another user
    user2 = await create_test_user()
    from planned.infrastructure.repositories import TaskDefinitionRepository
    task_definition_repo2 = TaskDefinitionRepository(user_uuid=UUID(user2.id))
    
    # User2 should not see user1's task definition
    with pytest.raises(exceptions.NotFoundError):
        await task_definition_repo2.get("user1-task")

