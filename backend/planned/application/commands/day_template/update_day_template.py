"""Command to update an existing day template."""

from dataclasses import asdict, fields, replace
from typing import Any, cast
from uuid import UUID

from planned.application.unit_of_work import UnitOfWorkFactory
from planned.domain.entities import DayTemplateEntity


class UpdateDayTemplateHandler:
    """Updates an existing day template."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def run(
        self,
        user_id: UUID,
        day_template_id: UUID,
        day_template_data: DayTemplateEntity,
    ) -> DayTemplateEntity:
        """Update an existing day template.

        Args:
            user_id: The user making the request
            day_template_id: The ID of the day template to update
            day_template_data: The updated day template data

        Returns:
            The updated day template entity

        Raises:
            NotFoundError: If day template not found
        """
        async with self._uow_factory.create(user_id) as uow:
            # Get existing day template
            existing = await uow.day_template_rw_repo.get(day_template_id)

            # Merge updates - both entities are dataclasses
            # Get all fields from day_template_data that are not None
            day_template_data_dict: dict[str, Any] = asdict(day_template_data)

            # Filter out init=False fields (like _domain_events) - they can't be specified in replace()
            init_false_fields = {f.name for f in fields(existing) if not f.init}
            update_dict = {
                k: v
                for k, v in day_template_data_dict.items()
                if v is not None and k not in init_false_fields
            }
            updated_any: Any = replace(existing, **update_dict)
            updated = cast(DayTemplateEntity, updated_any)

            # Ensure ID matches
            if hasattr(updated, "id"):
                object.__setattr__(updated, "id", day_template_id)

            day_template = await uow.day_template_rw_repo.put(updated)
            await uow.commit()
            return day_template

