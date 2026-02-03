"""Command to create an adhoc task."""

from dataclasses import dataclass, field
from datetime import date as dt_date

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.repositories import DayRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, TaskEntity


@dataclass(frozen=True)
class CreateAdhocTaskCommand(Command):
    """Command to create an adhoc or reminder task."""

    scheduled_date: dt_date
    name: str
    category: value_objects.TaskCategory
    type: value_objects.TaskType = value_objects.TaskType.ADHOC
    description: str | None = None
    time_window: value_objects.TimeWindow | None = None
    tags: list[value_objects.TaskTag] = field(default_factory=list)


class CreateAdhocTaskHandler(BaseCommandHandler[CreateAdhocTaskCommand, TaskEntity]):
    """Creates an adhoc task."""

    day_ro_repo: DayRepositoryReadOnlyProtocol

    async def handle(self, command: CreateAdhocTaskCommand) -> TaskEntity:
        """Create an adhoc task.

        Args:
            command: The command containing adhoc task data

        Returns:
            The created Task entity
        """
        async with self.new_uow() as uow:
            day_id = DayEntity.id_from_date_and_user(
                command.scheduled_date, self.user.id
            )
            await self.day_ro_repo.get(day_id)

            task = TaskEntity(
                user_id=self.user.id,
                scheduled_date=command.scheduled_date,
                name=command.name,
                status=value_objects.TaskStatus.NOT_STARTED,
                type=command.type,
                description=command.description,
                category=command.category,
                frequency=value_objects.TaskFrequency.ONCE,
                time_window=command.time_window,
                routine_definition_id=None,
                tags=command.tags,
            )
            await uow.create(task)
            return task
