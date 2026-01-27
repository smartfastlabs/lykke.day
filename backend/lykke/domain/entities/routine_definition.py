from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003

from lykke.core.exceptions import NotFoundError
from lykke.domain import value_objects
from lykke.domain.entities.auditable import AuditableEntity
from lykke.domain.entities.base import BaseEntityObject
from lykke.domain.events.routine_definition import (
    RoutineDefinitionTaskAddedEvent,
    RoutineDefinitionTaskRemovedEvent,
    RoutineDefinitionTaskUpdatedEvent,
)

if TYPE_CHECKING:
    from lykke.domain.events.base import DomainEvent


@dataclass(kw_only=True)
class RoutineDefinitionEntity(BaseEntityObject, AuditableEntity):
    user_id: UUID
    name: str

    category: value_objects.TaskCategory
    routine_definition_schedule: value_objects.RecurrenceSchedule
    description: str = ""
    time_window: value_objects.TimeWindow | None = None
    tasks: list[value_objects.RoutineDefinitionTask] = field(default_factory=list)

    def _copy_with_tasks(
        self, tasks: list[value_objects.RoutineDefinitionTask]
    ) -> RoutineDefinitionEntity:
        """Return a copy of this routine definition with updated tasks."""
        return RoutineDefinitionEntity(
            id=self.id,
            user_id=self.user_id,
            name=self.name,
            category=self.category,
            routine_definition_schedule=self.routine_definition_schedule,
            description=self.description,
            time_window=self.time_window,
            tasks=tasks,
        )

    def record_event(self, event: DomainEvent) -> None:
        """Record a domain event on this aggregate."""
        super()._add_event(event)

    def add_task(
        self, task: value_objects.RoutineDefinitionTask
    ) -> RoutineDefinitionEntity:
        """Attach a task to the routine definition."""
        updated = self._copy_with_tasks([*self.tasks, task])
        updated.record_event(
            RoutineDefinitionTaskAddedEvent(
                user_id=self.user_id,
                routine_definition_id=updated.id,
                task=task,
            )
        )
        return updated

    def update_task(
        self, task_update: value_objects.RoutineDefinitionTask
    ) -> RoutineDefinitionEntity:
        """Update an attached task by task ID."""
        updated_tasks: list[value_objects.RoutineDefinitionTask] = []
        found = False

        for task in self.tasks:
            if task.id == task_update.id:
                updated_tasks.append(
                    value_objects.RoutineDefinitionTask(
                        id=task.id,
                        task_definition_id=task.task_definition_id,
                        name=task_update.name
                        if task_update.name is not None
                        else task.name,
                        task_schedule=(
                            task_update.task_schedule
                            if task_update.task_schedule is not None
                            else task.task_schedule
                        ),
                        time_window=(
                            task_update.time_window
                            if task_update.time_window is not None
                            else task.time_window
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
            RoutineDefinitionTaskUpdatedEvent(
                user_id=self.user_id,
                routine_definition_id=updated.id,
                task=task_update,
            )
        )
        return updated

    def remove_task(self, routine_definition_task_id: UUID) -> RoutineDefinitionEntity:
        """Detach a task from the routine definition by RoutineDefinitionTask.id."""
        filtered_tasks = [
            task for task in self.tasks if task.id != routine_definition_task_id
        ]

        if len(filtered_tasks) == len(self.tasks):
            raise NotFoundError("Routine task not found")

        removed_task = next(
            (task for task in self.tasks if task.id == routine_definition_task_id),
            None,
        )
        updated = self._copy_with_tasks(filtered_tasks)
        updated.record_event(
            RoutineDefinitionTaskRemovedEvent(
                user_id=self.user_id,
                routine_definition_id=updated.id,
                routine_definition_task_id=routine_definition_task_id,
                task_definition_id=removed_task.task_definition_id,
            )
        )
        return updated
