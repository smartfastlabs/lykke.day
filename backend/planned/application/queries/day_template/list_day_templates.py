"""Query to list day templates with optional pagination."""

from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain import value_objects
from planned.domain.entities import DayTemplateEntity


class ListDayTemplatesHandler:
    """Lists day templates with optional pagination."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def run(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        paginate: bool = True,
    ) -> list[DayTemplateEntity] | value_objects.PagedQueryResponse[DayTemplateEntity]:
        """List day templates with optional pagination.

        Args:
            user_id: The user making the request
            limit: Maximum number of items to return
            offset: Number of items to skip
            paginate: Whether to return paginated response

        Returns:
            List of day templates or PagedQueryResponse
        """
        async with self._uow_factory.create(user_id) as uow:
            items = await uow.day_template_ro_repo.all()

            if not paginate:
                return items

            # Apply pagination
            total = len(items)
            start = offset
            end = start + limit
            paginated_items = items[start:end]

            return value_objects.PagedQueryResponse(
                items=paginated_items,
                total=total,
                limit=limit,
                offset=offset,
                has_next=end < total,
                has_previous=start > 0,
            )

