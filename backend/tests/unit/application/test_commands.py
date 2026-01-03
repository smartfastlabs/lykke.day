"""Integration tests for application commands using real database."""

import datetime
from uuid import uuid4

import pytest

from planned.application.commands.create_entity import CreateEntityHandler
from planned.application.commands.delete_entity import DeleteEntityHandler
from planned.application.commands.update_entity import UpdateEntityHandler
from planned.application.queries.get_entity import GetEntityHandler
from planned.core.exceptions import NotFoundError
from planned.domain.entities import DayEntity
from planned.domain.value_objects.day import DayStatus
from planned.infrastructure.unit_of_work import SqlAlchemyUnitOfWorkFactory


@pytest.mark.asyncio
async def test_create_entity_handler(
    test_user
) -> None:
    """Test CreateEntityHandler creates an entity."""
    uow_factory = SqlAlchemyUnitOfWorkFactory()
    day = DayEntity(
        user_id=test_user.id,
        date=datetime.date(2025, 11, 27),
        status=DayStatus.UNSCHEDULED,
    )

    handler = CreateEntityHandler(uow_factory)
    result = await handler.create_entity(
        user_id=test_user.id,
        repository_name="days",
        entity=day,
    )

    assert result.id is not None
    assert result.date == datetime.date(2025, 11, 27)
    assert result.status == DayStatus.UNSCHEDULED


@pytest.mark.asyncio
async def test_delete_entity_handler(
    test_user
) -> None:
    """Test DeleteEntityHandler deletes an entity."""
    uow_factory = SqlAlchemyUnitOfWorkFactory()
    
    # First create a day
    day = DayEntity(
        user_id=test_user.id,
        date=datetime.date(2025, 11, 27),
        status=DayStatus.UNSCHEDULED,
    )
    
    create_handler = CreateEntityHandler(uow_factory)
    created_day = await create_handler.create_entity(
        user_id=test_user.id,
        repository_name="days",
        entity=day,
    )
    entity_id = created_day.id

    # Now delete it
    handler = DeleteEntityHandler(uow_factory)
    await handler.delete_entity(
        user_id=test_user.id,
        repository_name="days",
        entity_id=entity_id,
    )

    # Verify it's deleted
    get_handler = GetEntityHandler(uow_factory)
    with pytest.raises(NotFoundError):
        await get_handler.get_entity(
            user_id=test_user.id,
            repository_name="days",
            entity_id=entity_id,
        )


@pytest.mark.asyncio
async def test_get_entity_handler(
    test_user
) -> None:
    """Test GetEntityHandler retrieves an entity."""
    uow_factory = SqlAlchemyUnitOfWorkFactory()
    
    # First create a day
    day = DayEntity(
        user_id=test_user.id,
        date=datetime.date(2025, 11, 27),
        status=DayStatus.UNSCHEDULED,
    )
    
    create_handler = CreateEntityHandler(uow_factory)
    created_day = await create_handler.create_entity(
        user_id=test_user.id,
        repository_name="days",
        entity=day,
    )
    entity_id = created_day.id

    handler = GetEntityHandler(uow_factory)
    result = await handler.get_entity(
        user_id=test_user.id,
        repository_name="days",
        entity_id=entity_id,
    )

    assert result.id == entity_id
    assert result.date == datetime.date(2025, 11, 27)
    assert result.status == DayStatus.UNSCHEDULED


@pytest.mark.asyncio
async def test_get_entity_handler_not_found(
    test_user
) -> None:
    """Test GetEntityHandler raises NotFoundError when entity not found."""
    uow_factory = SqlAlchemyUnitOfWorkFactory()
    entity_id = uuid4()

    handler = GetEntityHandler(uow_factory)
    with pytest.raises(NotFoundError):
        await handler.get_entity(
            user_id=test_user.id,
            repository_name="days",
            entity_id=entity_id,
        )


@pytest.mark.asyncio
async def test_update_entity_handler(
    test_user
) -> None:
    """Test UpdateEntityHandler updates an entity."""
    uow_factory = SqlAlchemyUnitOfWorkFactory()
    
    # First create a day
    day = DayEntity(
        user_id=test_user.id,
        date=datetime.date(2025, 11, 27),
        status=DayStatus.UNSCHEDULED,
    )
    
    create_handler = CreateEntityHandler(uow_factory)
    created_day = await create_handler.create_entity(
        user_id=test_user.id,
        repository_name="days",
        entity=day,
    )
    entity_id = created_day.id
    
    # Now update it
    updated_day = DayEntity(
        id=entity_id,
        user_id=test_user.id,
        date=datetime.date(2025, 11, 27),
        status=DayStatus.SCHEDULED,
    )

    handler = UpdateEntityHandler(uow_factory)
    result = await handler.update_entity(
        user_id=test_user.id,
        repository_name="days",
        entity_id=entity_id,
        entity_data=updated_day,
    )

    assert result.status == DayStatus.SCHEDULED
    assert result.id == entity_id

