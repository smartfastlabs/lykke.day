"""Fixtures for e2e tests - full API tests with test client."""

import datetime
from datetime import time
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from lykke.app import app
from lykke.domain.entities import UserEntity
from lykke.domain.entities.day_template import DayTemplateEntity
from lykke.domain.value_objects.alarm import Alarm, AlarmType
from lykke.domain.value_objects.user import UserSetting
from lykke.infrastructure.database.tables import User as UserDB
from lykke.infrastructure.database.utils import reset_engine
from lykke.infrastructure.repositories import DayTemplateRepository, UserRepository
from lykke.presentation.api.routers.dependencies.user import (
    get_current_user,
    get_current_user_from_token,
)


@pytest.fixture
def setup_test_user_day_template():
    """Fixture that returns a function to create a test user with DayTemplate."""

    async def _setup():
        """Create a test user with default DayTemplate."""
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        user_repo = UserRepository()
        test_user_email = f"test_{uuid4()}@lykke.day"
        test_user = UserEntity(
            email=test_user_email,
            hashed_password=pwd_context.hash("test_password"),
            settings=UserSetting(),
        )
        test_user = await user_repo.put(test_user)

        test_user_id = test_user.id
        day_template_repo = DayTemplateRepository(user_id=test_user_id)

        # Create default template (UUID will be auto-generated)
        default_template = DayTemplateEntity(
            user_id=test_user_id,
            slug="default",
            alarm=Alarm(
                name="Default Alarm",
                time=time(7, 15),
                type=AlarmType.FIRM,
            ),
        )
        await day_template_repo.put(default_template)
        return test_user

    return _setup


@pytest.fixture
def test_client():
    """FastAPI TestClient for e2e tests."""
    with TestClient(app) as client:
        yield client


async def schedule_day_for_user(user_id: UUID, date: datetime.date) -> None:
    """Helper function to schedule a day for a user in tests.
    
    This is used instead of the removed HTTP endpoint to ensure days exist
    before creating tasks or testing other functionality.
    """
    from lykke.application.commands.day import ScheduleDayHandler
    from lykke.application.queries import PreviewDayHandler
    from lykke.infrastructure.gateways import StubPubSubGateway
    from lykke.infrastructure.unit_of_work import (
        SqlAlchemyReadOnlyRepositoryFactory,
        SqlAlchemyUnitOfWorkFactory,
    )
    
    ro_repo_factory = SqlAlchemyReadOnlyRepositoryFactory()
    uow_factory = SqlAlchemyUnitOfWorkFactory(pubsub_gateway=StubPubSubGateway())
    ro_repos = ro_repo_factory.create(user_id)
    preview_handler = PreviewDayHandler(ro_repos, user_id)
    schedule_handler = ScheduleDayHandler(ro_repos, uow_factory, user_id, preview_handler)
    await schedule_handler.schedule_day(date=date)


@pytest.fixture
def authenticated_client(test_client, setup_test_user_day_template, request):
    """Test client with authenticated session."""

    # Register cleanup finalizer
    def cleanup():
        app.dependency_overrides.clear()

    request.addfinalizer(cleanup)

    async def _authenticated_client():
        """Return authenticated test client and user."""
        # Use setup_test_user_day_template to create user and default template
        await reset_engine()
        user = await setup_test_user_day_template()

        # Override get_current_user dependency to return our test user
        # This bypasses the actual authentication for testing
        app.dependency_overrides[get_current_user] = lambda: user
        
        # Also override get_current_user_from_token for WebSocket endpoints
        from fastapi import WebSocket
        async def _get_user_from_token(websocket: WebSocket) -> UserEntity:
            return user
        app.dependency_overrides[get_current_user_from_token] = _get_user_from_token

        return test_client, user

    return _authenticated_client


@pytest.fixture
def create_entity_with_uow(test_client):
    """Helper fixture to create entities through UOW so audit logs are broadcast.
    
    When tests create entities directly via repository.put(), audit logs are NOT
    created or broadcast to Redis. This helper ensures entities are properly created
    through the UOW so that:
    1. Audit logs are created
    2. Audit logs are broadcast to Redis for WebSocket tests
    """
    async def _create_entity(entity, user_id):
        """Create an entity through the UOW.
        
        Args:
            entity: The entity to create (with create() already called)
            user_id: The user ID for the UOW
        """
        from lykke.infrastructure.gateways import RedisPubSubGateway
        from lykke.infrastructure.unit_of_work import SqlAlchemyUnitOfWorkFactory
        
        # Get Redis pool from app state
        redis_pool = getattr(test_client.app.state, "redis_pool", None)
        pubsub_gateway = RedisPubSubGateway(redis_pool=redis_pool)
        uow_factory = SqlAlchemyUnitOfWorkFactory(pubsub_gateway=pubsub_gateway)
        
        # Use UOW to create entity
        async with uow_factory.create(user_id) as uow:
            # Entity should already have EntityCreatedEvent from create()
            # If not, call create() on it
            if not hasattr(entity, '_events') or not entity._events:
                entity.create()
            uow.add(entity)
            # UOW commit will create audit logs and broadcast to Redis
    
    return _create_entity


@pytest.fixture
def create_entity_with_audit_log():
    """Helper to create entities with audit logs directly in DB (no real-time broadcast).
    
    This is useful for tests that need audit logs in the database but don't need
    real-time WebSocket notifications. Avoids event loop issues with TestClient.
    """
    async def _create_with_audit(entity, user_id):
        """Create an entity and its audit log directly in the DB.
        
        Args:
            entity: The entity to create
            user_id: The user ID
        """
        from datetime import UTC, datetime
        
        from lykke.domain.entities import AuditLogEntity
        from lykke.infrastructure.repositories import AuditLogRepository
        
        # Get the appropriate repository for the entity
        if hasattr(entity, 'scheduled_date'):
            # Task entity
            from lykke.infrastructure.repositories import TaskRepository
            repo = TaskRepository(user_id=user_id)
        elif hasattr(entity, 'platform'):
            # Calendar entry
            from lykke.infrastructure.repositories import CalendarEntryRepository
            repo = CalendarEntryRepository(user_id=user_id)
        else:
            raise ValueError(f"Unknown entity type: {type(entity)}")
        
        # Save the entity
        await repo.put(entity)
        
        # Create audit log manually
        entity_type = type(entity).__name__.replace("Entity", "").lower()
        audit_log = AuditLogEntity(
            user_id=user_id,
            activity_type="EntityCreatedEvent",
            entity_id=entity.id,
            entity_type=entity_type,
            occurred_at=datetime.now(UTC),
            meta={
                "entity_data": {
                    "id": str(entity.id),
                    "user_id": str(entity.user_id),
                    **({"scheduled_date": entity.scheduled_date.isoformat()} if hasattr(entity, 'scheduled_date') else {}),
                    **({"date": entity.date.isoformat()} if hasattr(entity, 'date') else {}),
                }
            },
        )
        audit_log_repo = AuditLogRepository(user_id=user_id)
        await audit_log_repo.put(audit_log)
        
        return entity
    
    return _create_with_audit
