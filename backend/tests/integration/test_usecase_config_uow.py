"""Integration tests for UseCaseConfig entity with Unit of Work.

This test ensures that UseCaseConfigEntity is properly registered in the
Unit of Work's entity repository mapping, preventing the error:
"ValueError: No repository found for entity type UseCaseConfigEntity"
"""

import pytest

from lykke.domain.entities.usecase_config import UseCaseConfigEntity
from lykke.infrastructure.gateways import StubPubSubGateway
from lykke.infrastructure.unit_of_work import SqlAlchemyUnitOfWorkFactory


@pytest.mark.asyncio
async def test_usecase_config_can_be_created_through_uow(test_user):
    """Test that UseCaseConfigEntity can be created through Unit of Work.

    This regression test ensures that UseCaseConfigEntity is properly
    registered in SqlAlchemyUnitOfWork._ENTITY_REPO_MAP. Without this
    registration, uow.create() or uow.add() will raise:
    ValueError: No repository found for entity type UseCaseConfigEntity
    """
    user_id = test_user.id

    # Create a UseCaseConfigEntity
    config = UseCaseConfigEntity(
        user_id=user_id,
        usecase="notification",
        config={"user_amendments": ["Test amendment"]},
    )

    # Create UoW and add the entity - this should not raise ValueError
    uow_factory = SqlAlchemyUnitOfWorkFactory(pubsub_gateway=StubPubSubGateway())
    async with uow_factory.create(user_id) as uow:
        # This will fail if UseCaseConfigEntity is not in _ENTITY_REPO_MAP
        created_config = await uow.create(config)
        assert created_config.id is not None
        assert created_config.usecase == "notification"
        assert created_config.config == {"user_amendments": ["Test amendment"]}

    # Verify the entity was persisted by reading it back
    async with uow_factory.create(user_id) as uow:
        from lykke.domain.value_objects import UseCaseConfigQuery

        retrieved = await uow.usecase_config_ro_repo.search(
            UseCaseConfigQuery(usecase="notification")
        )
        assert len(retrieved) == 1
        assert retrieved[0].usecase == "notification"
        assert retrieved[0].config == {"user_amendments": ["Test amendment"]}


@pytest.mark.asyncio
async def test_usecase_config_can_be_added_through_uow(test_user):
    """Test that UseCaseConfigEntity can be added through Unit of Work.

    This regression test ensures that UseCaseConfigEntity can be added
    via uow.add() after calling entity.create() manually.
    """
    user_id = test_user.id

    # Create a UseCaseConfigEntity and call create() manually
    config = UseCaseConfigEntity(
        user_id=user_id,
        usecase="notification",
        config={"user_amendments": ["Another test"]},
    )
    config.create()  # Manually emit EntityCreatedEvent

    # Add through UoW - this should not raise ValueError
    uow_factory = SqlAlchemyUnitOfWorkFactory(pubsub_gateway=StubPubSubGateway())
    async with uow_factory.create(user_id) as uow:
        # This will fail if UseCaseConfigEntity is not in _ENTITY_REPO_MAP
        added_config = uow.add(config)
        assert added_config.id is not None
        assert added_config.usecase == "notification"


@pytest.mark.asyncio
async def test_usecase_config_can_be_updated_through_uow(test_user):
    """Test that UseCaseConfigEntity can be updated through Unit of Work.

    This ensures that updates work correctly after the entity is registered.
    """
    user_id = test_user.id

    # Create initial config
    config = UseCaseConfigEntity(
        user_id=user_id,
        usecase="notification",
        config={"user_amendments": ["Original"]},
    )

    uow_factory = SqlAlchemyUnitOfWorkFactory(pubsub_gateway=StubPubSubGateway())
    async with uow_factory.create(user_id) as uow:
        created = await uow.create(config)
        config_id = created.id

    # Update the config
    from datetime import UTC, datetime

    from lykke.domain.events.base import EntityUpdatedEvent
    from lykke.domain.value_objects.update import BaseUpdateObject

    updated_config = UseCaseConfigEntity(
        id=config_id,
        user_id=user_id,
        usecase="notification",
        config={"user_amendments": ["Updated"]},
        created_at=created.created_at,
        updated_at=datetime.now(UTC),
    )
    # Add EntityUpdatedEvent so UoW knows to update, not insert
    updated_config.add_event(EntityUpdatedEvent(update_object=BaseUpdateObject()))

    async with uow_factory.create(user_id) as uow:
        # This should work if entity is registered
        uow.add(updated_config)

    # Verify update
    async with uow_factory.create(user_id) as uow:
        from lykke.domain.value_objects import UseCaseConfigQuery

        retrieved = await uow.usecase_config_ro_repo.search(
            UseCaseConfigQuery(usecase="notification")
        )
        assert len(retrieved) == 1
        assert retrieved[0].config == {"user_amendments": ["Updated"]}
