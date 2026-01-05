"""Base classes for CQRS queries."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar, get_type_hints
from uuid import UUID

from planned.application.unit_of_work import ReadOnlyRepositories

# Query type and result type
QueryT = TypeVar("QueryT", bound="Query")
ResultT = TypeVar("ResultT")


@dataclass(frozen=True)
class Query:
    """Base class for queries.

    Queries are immutable data objects representing a request for data.
    They should contain all parameters needed to execute the query.
    Queries must not cause any side effects.
    """


class BaseQueryHandler:
    """Base class for query handlers that automatically injects requested repositories.

    Subclasses should declare which repositories they need as class attributes
    with type annotations. Only the declared repositories will be extracted from
    ReadOnlyRepositories and made available as instance attributes.

    Example:
        class SearchCalendarsHandler(BaseQueryHandler):
            calendar_ro_repo: CalendarRepositoryReadOnlyProtocol

            async def run(self, query: CalendarQuery) -> list[CalendarEntity]:
                return await self.calendar_ro_repo.search_query(query)
    """

    def __init__(self, ro_repos: ReadOnlyRepositories, user_id: UUID) -> None:
        """Initialize the query handler with requested repositories.

        Args:
            ro_repos: All available read-only repositories
            user_id: The user ID for this query context
        """
        self.user_id = user_id

        # Get type hints from the class (including from base classes)
        annotations = get_type_hints(self.__class__, include_extras=True)

        # Extract only the repositories that this handler has declared
        for attr_name, _attr_type in annotations.items():
            # Check if this is a repository attribute (not a method or other attribute)
            if not attr_name.startswith("_") and hasattr(ro_repos, attr_name):
                # Extract the repository from ro_repos and set it as an instance attribute
                setattr(self, attr_name, getattr(ro_repos, attr_name))


class QueryHandler(ABC, Generic[QueryT, ResultT]):
    """Base class for query handlers.

    Each handler processes exactly one type of query and returns data.
    Query handlers must be side-effect free - they only read data.
    Query handlers receive read-only repositories directly and do not have
    access to write operations or unit of work.

    Example:
        class GetDayTemplateHandler:
            def __init__(self, ro_repos: ReadOnlyRepositories) -> None:
                self._ro_repos = ro_repos

            async def run(self, user_id: UUID, template_id: UUID) -> DayTemplateEntity:
                return await self._ro_repos.day_template_ro_repo.get(template_id)
    """

    @abstractmethod
    async def handle(self, query: QueryT) -> ResultT:
        """Execute the query and return the result.

        Args:
            query: The query to execute

        Returns:
            The query result
        """
