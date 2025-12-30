"""Integration tests for TaskDefinitionRepository."""

from uuid import uuid4

import pytest

from planned.core.exceptions import exceptions
from planned.domain.entities import TaskDefinition
from planned.domain.value_objects.task import TaskType
from planned.infrastructure.repositories import TaskDefinitionRepository


@pytest.mark.asyncio
async def test_get(task_definition_repo, test_user):
    """Test getting a task definition by ID."""
    task_def = TaskDefinition(
        user_uuid=test_user.uuid,
        name="Test Task",
        description="Test description",
        type=TaskType.ACTIVITY,
    )
    await task_definition_repo.put(task_def)

    result = await task_definition_repo.get(task_def.uuid)

    assert result.uuid == task_def.uuid
    assert result.name == "Test Task"


@pytest.mark.asyncio
async def test_get_not_found(task_definition_repo):
    """Test getting a non-existent task definition raises NotFoundError."""
    with pytest.raises(exceptions.NotFoundError):
        await task_definition_repo.get(uuid4())


@pytest.mark.asyncio
async def test_put(task_definition_repo, test_user):
    """Test creating a new task definition."""
    task_def = TaskDefinition(
        user_uuid=test_user.uuid,
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
    task_def1 = TaskDefinition(
        user_uuid=test_user.uuid,
        name="Task 1",
        description="Description 1",
        type=TaskType.ACTIVITY,
    )
    task_def2 = TaskDefinition(
        user_uuid=test_user.uuid,
        name="Task 2",
        description="Description 2",
        type=TaskType.ACTIVITY,
    )
    await task_definition_repo.put(task_def1)
    await task_definition_repo.put(task_def2)

    all_defs = await task_definition_repo.all()

    def_ids = [d.uuid for d in all_defs]
    assert task_def1.uuid in def_ids
    assert task_def2.uuid in def_ids


@pytest.mark.asyncio
async def test_user_isolation(task_definition_repo, test_user, create_test_user):
    """Test that different users' task definitions are properly isolated."""
    task_def = TaskDefinition(
        user_uuid=test_user.uuid,
        name="User1 Task",
        description="Description",
        type=TaskType.ACTIVITY,
    )
    await task_definition_repo.put(task_def)

    # Create another user
    user2 = await create_test_user()
    task_definition_repo2 = TaskDefinitionRepository(user_uuid=user2.uuid)

    # User2 should not see user1's task definition
    with pytest.raises(exceptions.NotFoundError):
        await task_definition_repo2.get(task_def.uuid)
