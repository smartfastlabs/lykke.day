"""Base classes for CQRS queries."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar
from uuid import UUID

from lykke.application.unit_of_work import ReadOnlyRepositories

if TYPE_CHECKING:
    from lykke.domain.entities.day_template import DayTemplateEntity

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
    """Base class for query handlers with explicit dependency wiring."""

    def __init__(self, ro_repos: ReadOnlyRepositories, user_id: UUID) -> None:
        """Initialize the query handler with its dependencies."""
        self.user_id = user_id
        # Explicitly expose read-only repositories
        self.auth_token_ro_repo = ro_repos.auth_token_ro_repo
        self.calendar_entry_ro_repo = ro_repos.calendar_entry_ro_repo
        self.calendar_ro_repo = ro_repos.calendar_ro_repo
        self.day_ro_repo = ro_repos.day_ro_repo
        self.day_template_ro_repo = ro_repos.day_template_ro_repo
        self.push_subscription_ro_repo = ro_repos.push_subscription_ro_repo
        self.routine_ro_repo = ro_repos.routine_ro_repo
        self.task_definition_ro_repo = ro_repos.task_definition_ro_repo
        self.task_ro_repo = ro_repos.task_ro_repo
        self.user_ro_repo = ro_repos.user_ro_repo


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

            async def run(self, user_id: UUID, template_id: UUID) -> "DayTemplateEntity":
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
