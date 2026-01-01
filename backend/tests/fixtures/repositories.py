"""In-memory repository implementations for testing.

These repositories store data in memory and are useful for fast unit tests
that don't require a database connection.
"""

from typing import Any
from uuid import UUID

from planned.application.repositories import (
    AuthTokenRepositoryProtocol,
    CalendarRepositoryProtocol,
    DayRepositoryProtocol,
    DayTemplateRepositoryProtocol,
    EventRepositoryProtocol,
    MessageRepositoryProtocol,
    PushSubscriptionRepositoryProtocol,
    RoutineRepositoryProtocol,
    TaskDefinitionRepositoryProtocol,
    TaskRepositoryProtocol,
    UserRepositoryProtocol,
)
from planned.core.exceptions import NotFoundError
from planned.domain.entities.base import BaseEntityObject
from planned.domain.value_objects.query import BaseQuery, DateQuery


class InMemoryBaseRepository:
    """Base class for in-memory repositories."""

    def __init__(self) -> None:
        """Initialize the in-memory store."""
        self._store: dict[UUID, BaseEntityObject] = {}

    async def get(self, key: UUID) -> BaseEntityObject:
        """Get an object by id."""
        if key not in self._store:
            raise NotFoundError(f"Object with id {key} not found")
        return self._store[key]

    async def put(self, obj: BaseEntityObject) -> BaseEntityObject:
        """Save or update an object."""
        self._store[obj.id] = obj
        return obj

    async def all(self) -> list[BaseEntityObject]:
        """Get all objects."""
        return list(self._store.values())

    async def delete(self, key: UUID | BaseEntityObject) -> None:
        """Delete an object by id or by object."""
        if isinstance(key, UUID):
            obj_id = key
        else:
            obj_id = key.id

        if obj_id in self._store:
            del self._store[obj_id]


class InMemoryDayRepository(InMemoryBaseRepository):
    """In-memory implementation of DayRepositoryProtocol."""

    async def search_query(self, query: DateQuery) -> list:
        """Search for days matching the query."""
        all_days = await self.all()
        if query.date:
            return [day for day in all_days if hasattr(day, "date") and day.date == query.date]
        return all_days


class InMemoryTaskRepository(InMemoryBaseRepository):
    """In-memory implementation of TaskRepositoryProtocol."""

    async def search_query(self, query: DateQuery) -> list:
        """Search for tasks matching the query."""
        all_tasks = await self.all()
        if query.date:
            return [
                task
                for task in all_tasks
                if hasattr(task, "scheduled_date") and task.scheduled_date == query.date
            ]
        return all_tasks

    async def delete_many(self, query: DateQuery) -> None:
        """Delete tasks matching the query."""
        tasks_to_delete = await self.search_query(query)
        for task in tasks_to_delete:
            await self.delete(task)


class InMemoryEventRepository(InMemoryBaseRepository):
    """In-memory implementation of EventRepositoryProtocol."""

    async def search_query(self, query: DateQuery) -> list:
        """Search for events matching the query."""
        all_events = await self.all()
        if query.date:
            return [
                event
                for event in all_events
                if hasattr(event, "date") and event.date == query.date
            ]
        return all_events


class InMemoryMessageRepository(InMemoryBaseRepository):
    """In-memory implementation of MessageRepositoryProtocol."""

    async def search_query(self, query: DateQuery) -> list:
        """Search for messages matching the query."""
        all_messages = await self.all()
        if query.date:
            return [
                message
                for message in all_messages
                if hasattr(message, "date") and message.date == query.date
            ]
        return all_messages


class InMemoryDayTemplateRepository(InMemoryBaseRepository):
    """In-memory implementation of DayTemplateRepositoryProtocol."""

    async def get_by_slug(self, slug: str) -> Any:
        """Get a template by slug."""
        all_templates = await self.all()
        for template in all_templates:
            if hasattr(template, "slug") and template.slug == slug:
                return template
        raise NotFoundError(f"Template with slug {slug} not found")


class InMemoryUserRepository(InMemoryBaseRepository):
    """In-memory implementation of UserRepositoryProtocol."""

    async def get_by_email(self, email: str) -> Any | None:
        """Get a user by email."""
        all_users = await self.all()
        for user in all_users:
            if hasattr(user, "email") and user.email == email:
                return user
        return None


# Create type aliases for protocol compatibility
InMemoryAuthTokenRepository = InMemoryBaseRepository
InMemoryCalendarRepository = InMemoryBaseRepository
InMemoryPushSubscriptionRepository = InMemoryBaseRepository
InMemoryRoutineRepository = InMemoryBaseRepository
InMemoryTaskDefinitionRepository = InMemoryBaseRepository

