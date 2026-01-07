from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003

from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities.base import BaseConfigObject
from lykke.domain.events.routine import (
    RoutineTaskAddedEvent,
    RoutineTaskRemovedEvent,
    RoutineTaskUpdatedEvent,
)

if TYPE_CHECKING:
    from lykke.domain.events.base import DomainEvent


@dataclass(kw_only=True)
class RoutineEntity(BaseConfigObject):
    user_id: UUID
    name: str

    category: value_objects.TaskCategory
    routine_schedule: value_objects.RoutineSchedule
    description: str = ""
    tasks: list[value_objects.RoutineTask] = field(default_factory=list)

    def _copy_with_tasks(self, tasks: list[value_objects.RoutineTask]) -> RoutineEntity:
        """Return a copy of this routine with updated tasks."""
        return RoutineEntity(
            id=self.id,
            user_id=self.user_id,
            name=self.name,
            category=self.category,
            routine_schedule=self.routine_schedule,
            description=self.description,
            tasks=tasks,
        )

    def record_event(self, event: DomainEvent) -> None:
        """Record a domain event on this aggregate."""
        super()._add_event(event)

    def add_task(self, task: value_objects.RoutineTask) -> RoutineEntity:
        """Attach a task to the routine."""
        updated = self._copy_with_tasks([*self.tasks, task])
        updated.record_event(RoutineTaskAddedEvent(routine_id=updated.id, task=task))
        return updated

    def update_task(self, task_update: value_objects.RoutineTask) -> RoutineEntity:
        """Update an attached task by task ID."""
        updated_tasks: list[value_objects.RoutineTask] = []
        found = False

        for task in self.tasks:
            if task.id == task_update.id:
                updated_tasks.append(
                    value_objects.RoutineTask(
                        id=task.id,
                        task_definition_id=task.task_definition_id,
                        name=task_update.name
                        if task_update.name is not None
                        else task.name,
                        schedule=(
                            task_update.schedule
                            if task_update.schedule is not None
                            else task.schedule
                        ),
                    )
                )
                found = True
            else:
                updated_tasks.append(task)

        if not found:
            raise NotFoundError("Routine task not found")

        updated = self._copy_with_tasks(updated_tasks)
        updated.record_event(
            RoutineTaskUpdatedEvent(routine_id=updated.id, task=task_update)
        )
        return updated

    def remove_task(self, routine_task_id: UUID) -> RoutineEntity:
        """Detach a task from the routine by RoutineTask.id."""
        filtered_tasks = [task for task in self.tasks if task.id != routine_task_id]

        if len(filtered_tasks) == len(self.tasks):
            raise NotFoundError("Routine task not found")

        removed_task = next(
            (task for task in self.tasks if task.id == routine_task_id), None
        )
        if removed_task is None:
            raise NotFoundError("Routine task not found")
        updated = self._copy_with_tasks(filtered_tasks)
        updated.record_event(
            RoutineTaskRemovedEvent(
                routine_id=updated.id,
                routine_task_id=routine_task_id,
                task_definition_id=removed_task.task_definition_id,
            )
        )
        return updated
