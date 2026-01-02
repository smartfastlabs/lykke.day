"""Query handlers for read-only operations.

Queries are immutable request objects that describe what data to fetch.
Query handlers execute the query and return data without side effects.
"""

from .base import Query, QueryHandler
from .get_day_context import GetDayContextHandler, GetDayContextQuery
from .preview_day import PreviewDayHandler, PreviewDayQuery

__all__ = [
    "GetDayContextHandler",
    "GetDayContextQuery",
    "PreviewDayHandler",
    "PreviewDayQuery",
    "Query",
    "QueryHandler",
]

