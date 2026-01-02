"""Integration tests for application queries using real database."""

import datetime

import pytest

from planned.application.commands.create_entity import (
    CreateEntityCommand,
    CreateEntityHandler,
)
from planned.application.queries.list_entities import (
    ListEntitiesQuery,
    ListEntitiesHandler,
)
from planned.domain import entities, value_objects
from planned.domain.value_objects.day import DayStatus
from planned.infrastructure.unit_of_work import SqlAlchemyUnitOfWorkFactory


@pytest.mark.asyncio
async def test_list_entities_handler_no_pagination(
    test_user
) -> None:
    """Test ListEntitiesHandler returns all entities when pagination disabled."""
    uow_factory = SqlAlchemyUnitOfWorkFactory()
    
    # Create some days
    day1 = entities.Day(
        user_id=test_user.id,
        date=datetime.date(2025, 11, 27),
        status=DayStatus.UNSCHEDULED,
    )
    day2 = entities.Day(
        user_id=test_user.id,
        date=datetime.date(2025, 11, 28),
        status=DayStatus.UNSCHEDULED,
    )
    
    create_handler = CreateEntityHandler(uow_factory)
    await create_handler.handle(
        CreateEntityCommand(
            user_id=test_user.id,
            repository_name="days",
            entity=day1,
        )
    )
    await create_handler.handle(
        CreateEntityCommand(
            user_id=test_user.id,
            repository_name="days",
            entity=day2,
        )
    )

    handler = ListEntitiesHandler(uow_factory)
    query = ListEntitiesQuery(
        user_id=test_user.id,
        repository_name="days",
        paginate=False,
    )

    result = await handler.handle(query)

    assert isinstance(result, list)
    assert len(result) >= 2
    dates = [day.date for day in result]
    assert datetime.date(2025, 11, 27) in dates
    assert datetime.date(2025, 11, 28) in dates


@pytest.mark.asyncio
async def test_list_entities_handler_with_pagination(
    test_user
) -> None:
    """Test ListEntitiesHandler returns paginated response."""
    uow_factory = SqlAlchemyUnitOfWorkFactory()
    
    # Create 10 days
    create_handler = CreateEntityHandler(uow_factory)
    for i in range(10):
        day = entities.Day(
            user_id=test_user.id,
            date=datetime.date(2025, 11, 27 + i),
            status=DayStatus.UNSCHEDULED,
        )
        await create_handler.handle(
            CreateEntityCommand(
                user_id=test_user.id,
                repository_name="days",
                entity=day,
            )
        )

    handler = ListEntitiesHandler(uow_factory)
    query = ListEntitiesQuery(
        user_id=test_user.id,
        repository_name="days",
        limit=5,
        offset=0,
        paginate=True,
    )

    result = await handler.handle(query)

    assert hasattr(result, "items")
    assert hasattr(result, "total")
    assert hasattr(result, "limit")
    assert hasattr(result, "offset")
    assert hasattr(result, "has_next")
    assert hasattr(result, "has_previous")
    assert len(result.items) == 5
    assert result.total >= 10
    assert result.limit == 5
    assert result.offset == 0
    assert result.has_next is True
    assert result.has_previous is False


@pytest.mark.asyncio
async def test_list_entities_handler_with_search_query(
    test_user
) -> None:
    """Test ListEntitiesHandler uses search_query when provided."""
    uow_factory = SqlAlchemyUnitOfWorkFactory()
    
    # Create a day
    day = entities.Day(
        user_id=test_user.id,
        date=datetime.date(2025, 11, 27),
        status=DayStatus.UNSCHEDULED,
    )
    
    create_handler = CreateEntityHandler(uow_factory)
    await create_handler.handle(
        CreateEntityCommand(
            user_id=test_user.id,
            repository_name="days",
            entity=day,
        )
    )

    handler = ListEntitiesHandler(uow_factory)
    search_query = value_objects.DateQuery(date=datetime.date(2025, 11, 27))
    query = ListEntitiesQuery(
        user_id=test_user.id,
        repository_name="days",
        search_query=search_query,
        paginate=False,
    )

    result = await handler.handle(query)

    assert len(result) >= 1
    assert any(d.date == datetime.date(2025, 11, 27) for d in result)

