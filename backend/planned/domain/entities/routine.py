from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from planned.core.exceptions import DomainError, NotFoundError
from planned.domain import value_objects
from planned.domain.entities.base import BaseConfigObject
from planned.domain.events.routine import (
    RoutineTaskAddedEvent,
    RoutineTaskRemovedEvent,
    RoutineTaskUpdatedEvent,
)

if TYPE_CHECKING:
    from uuid import UUID

    from planned.domain.events.base import DomainEvent


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
        """Attach a task to the routine, enforcing uniqueness."""
        if any(t.task_definition_id == task.task_definition_id for t in self.tasks):
            raise DomainError("Task definition already attached to routine")

        updated = self._copy_with_tasks([*self.tasks, task])
        updated.record_event(RoutineTaskAddedEvent(routine_id=updated.id, task=task))
        return updated

    def update_task(self, task_update: value_objects.RoutineTask) -> RoutineEntity:
        """Update an attached task by task_definition_id."""
        updated_tasks: list[value_objects.RoutineTask] = []
        found = False

        for task in self.tasks:
            if task.task_definition_id == task_update.task_definition_id:
                updated_tasks.append(
                    value_objects.RoutineTask(
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

    def remove_task(self, task_definition_id: UUID) -> RoutineEntity:
        """Detach a task from the routine."""
        filtered_tasks = [
            task for task in self.tasks if task.task_definition_id != task_definition_id
        ]

        if len(filtered_tasks) == len(self.tasks):
            raise NotFoundError("Routine task not found")

        updated = self._copy_with_tasks(filtered_tasks)
        updated.record_event(
            RoutineTaskRemovedEvent(
                routine_id=updated.id,
                task_definition_id=task_definition_id,
            )
        )
        return updated
