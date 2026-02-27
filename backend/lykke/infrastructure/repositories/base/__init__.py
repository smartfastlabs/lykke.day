from lykke.domain import value_objects

from .repository import UserScopedBaseRepository

# Re-export query types for convenience
AuthTokenQuery = value_objects.AuthTokenQuery
BaseQuery = value_objects.BaseQuery
CalendarEntryQuery = value_objects.CalendarEntryQuery
CalendarEntrySeriesQuery = value_objects.CalendarEntrySeriesQuery
DateQuery = value_objects.DateQuery
DayTemplateQuery = value_objects.DayTemplateQuery
TaskQuery = value_objects.TaskQuery
UseCaseConfigQuery = value_objects.UseCaseConfigQuery
UserQuery = value_objects.UserQuery

__all__ = [
    "AuthTokenQuery",
    "BaseQuery",
    "CalendarEntryQuery",
    "CalendarEntrySeriesQuery",
    "DateQuery",
    "DayTemplateQuery",
    "TaskQuery",
    "UseCaseConfigQuery",
    "UserQuery",
    "UserScopedBaseRepository",
]
