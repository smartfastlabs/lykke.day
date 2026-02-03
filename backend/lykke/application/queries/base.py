"""Base classes for CQRS queries."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

from lykke.application.base_handler import BaseHandler
from lykke.domain.entities import UserEntity

if TYPE_CHECKING:
    from lykke.application.unit_of_work import (
        ReadOnlyRepositories,
        ReadOnlyRepositoryFactory,
        ReadWriteRepositoryFactory,
    )
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

            async def run(self, user: UserEntity, template_id: UUID) -> "DayTemplateEntity":
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


class BaseQueryHandler(
    BaseHandler, QueryHandler[QueryT, ResultT], Generic[QueryT, ResultT]
):
    """Base class for query handlers with explicit dependency wiring.

    Subclasses must:
    - Specify QueryT and ResultT type parameters
    - Implement async def handle(self, query: QueryT) -> ResultT
    """

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories | None,
        user: UserEntity,
        *,
        repository_factory: ReadOnlyRepositoryFactory | None = None,
        readwrite_repository_factory: ReadWriteRepositoryFactory | None = None,
    ) -> None:
        """Initialize the query handler with its dependencies."""
        super().__init__(
            ro_repos,
            user,
            repository_factory=repository_factory,
            readwrite_repository_factory=readwrite_repository_factory,
        )
