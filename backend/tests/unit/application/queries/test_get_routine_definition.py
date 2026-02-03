"""Unit tests for GetRoutineDefinitionHandler."""

from uuid import uuid4

import pytest
from dobles import allow

from lykke.application.queries.routine_definition import (
    GetRoutineDefinitionHandler,
    GetRoutineDefinitionQuery,
)
from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities import RoutineDefinitionEntity, UserEntity
from tests.support.dobles import (
    create_read_only_repos_double,
    create_routine_definition_repo_double,
)


@pytest.mark.asyncio
async def test_get_routine_definition_returns_routine_definition_by_id():
    """Verify get_routine_definition returns the correct routine definition."""
    user_id = uuid4()
    routine_definition_id = uuid4()

    routine_definition = RoutineDefinitionEntity(
        id=routine_definition_id,
        user_id=user_id,
        name="Morning Routine Definition",
        category=value_objects.TaskCategory.HEALTH,
        routine_definition_schedule=value_objects.RecurrenceSchedule(
            frequency=value_objects.TaskFrequency.DAILY,
        ),
        tasks=[],
    )

    # Setup repository
    routine_repo = create_routine_definition_repo_double()
    allow(routine_repo).get.with_args(routine_definition_id).and_return(
        routine_definition
    )
    ro_repos = create_read_only_repos_double(routine_definition_repo=routine_repo)
    user = UserEntity(id=user_id, email="test@example.com", hashed_password="!")
    handler = GetRoutineDefinitionHandler(ro_repos, user)

    # Act
    result = await handler.handle(
        GetRoutineDefinitionQuery(routine_definition_id=routine_definition_id)
    )

    # Assert
    assert result == routine_definition
    assert result.id == routine_definition_id
    assert result.name == "Morning Routine Definition"


@pytest.mark.asyncio
async def test_get_routine_definition_raises_not_found_for_invalid_id():
    """Verify get_routine_definition raises NotFoundError for invalid ID."""
    user_id = uuid4()
    invalid_id = uuid4()

    # Setup repository to raise NotFoundError
    routine_repo = create_routine_definition_repo_double()
    allow(routine_repo).get.with_args(invalid_id).and_raise(
        NotFoundError("Routine definition not found")
    )
    ro_repos = create_read_only_repos_double(routine_definition_repo=routine_repo)
    user = UserEntity(id=user_id, email="test@example.com", hashed_password="!")
    handler = GetRoutineDefinitionHandler(ro_repos, user)

    # Act & Assert
    with pytest.raises(NotFoundError):
        await handler.handle(
            GetRoutineDefinitionQuery(routine_definition_id=invalid_id)
        )
