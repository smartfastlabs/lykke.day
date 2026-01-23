"""Router for Routine CRUD operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from lykke.application.commands import RecordRoutineActionCommand, RecordRoutineActionHandler
from lykke.application.commands.routine import (
    AddRoutineTaskCommand,
    AddRoutineTaskHandler,
    CreateRoutineCommand,
    CreateRoutineHandler,
    DeleteRoutineCommand,
    DeleteRoutineHandler,
    RemoveRoutineTaskCommand,
    RemoveRoutineTaskHandler,
    UpdateRoutineCommand,
    UpdateRoutineHandler,
    UpdateRoutineTaskCommand,
    UpdateRoutineTaskHandler,
)
from lykke.application.queries.routine import (
    GetRoutineHandler,
    GetRoutineQuery,
    SearchRoutinesHandler,
    SearchRoutinesQuery,
)
from lykke.domain import value_objects
from lykke.domain.entities import RoutineEntity, UserEntity
from lykke.domain.value_objects import RoutineUpdateObject
from lykke.domain.value_objects.routine import RoutineTask
from lykke.presentation.api.schemas import (
    PagedResponseSchema,
    QuerySchema,
    RoutineCreateSchema,
    RoutineSchema,
    RoutineTaskCreateSchema,
    RoutineTaskUpdateSchema,
    RoutineUpdateSchema,
    TaskSchema,
)
from lykke.presentation.api.schemas.mappers import map_routine_to_schema
from lykke.presentation.handler_factory import CommandHandlerFactory, QueryHandlerFactory

from .dependencies.factories import command_handler_factory, query_handler_factory
from .dependencies.user import get_current_user
from .utils import build_search_query, create_paged_response

router = APIRouter()


@router.get("/{uuid}", response_model=RoutineSchema)
async def get_routine(
    uuid: UUID,
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
) -> RoutineSchema:
    """Get a single routine by ID."""
    get_routine_handler = query_factory.create(GetRoutineHandler)
    routine = await get_routine_handler.handle(GetRoutineQuery(routine_id=uuid))
    return map_routine_to_schema(routine)


@router.post("/", response_model=PagedResponseSchema[RoutineSchema])
async def search_routines(
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
    query: QuerySchema[value_objects.RoutineQuery],
) -> PagedResponseSchema[RoutineSchema]:
    """Search routines with pagination and optional filters."""
    list_routines_handler = query_factory.create(SearchRoutinesHandler)
    search_query = build_search_query(query, value_objects.RoutineQuery)
    result = await list_routines_handler.handle(SearchRoutinesQuery(search_query=search_query))
    return create_paged_response(result, map_routine_to_schema)


@router.post(
    "/create",
    response_model=RoutineSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_routine(
    routine_data: RoutineCreateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    command_factory: Annotated[
        CommandHandlerFactory, Depends(command_handler_factory)
    ],
) -> RoutineSchema:
    """Create a new routine."""
    create_routine_handler = command_factory.create(CreateRoutineHandler)
    # Convert schema to domain dataclasses
    from lykke.domain.value_objects.routine import RecurrenceSchedule, RoutineTask
    from lykke.domain.value_objects.task import TaskSchedule

    routine_schedule = RecurrenceSchedule(
        frequency=routine_data.routine_schedule.frequency,
        weekdays=routine_data.routine_schedule.weekdays,
        day_number=routine_data.routine_schedule.day_number,
    )

    tasks = []
    for task_schema in routine_data.tasks or []:
        task_schedule = None
        if task_schema.schedule:
            task_schedule = TaskSchedule(
                available_time=task_schema.schedule.available_time,
                start_time=task_schema.schedule.start_time,
                end_time=task_schema.schedule.end_time,
                timing_type=task_schema.schedule.timing_type,
            )

        task_recurrence_schedule = None
        if task_schema.task_schedule:
            task_recurrence_schedule = RecurrenceSchedule(
                frequency=task_schema.task_schedule.frequency,
                weekdays=task_schema.task_schedule.weekdays,
                day_number=task_schema.task_schedule.day_number,
            )

        if task_schema.id:
            routine_task = RoutineTask(
                id=task_schema.id,
                task_definition_id=task_schema.task_definition_id,
                name=task_schema.name,
                schedule=task_schedule,
                task_schedule=task_recurrence_schedule,
            )
        else:
            routine_task = RoutineTask(
                task_definition_id=task_schema.task_definition_id,
                name=task_schema.name,
                schedule=task_schedule,
                task_schedule=task_recurrence_schedule,
            )
        tasks.append(routine_task)

    routine = RoutineEntity(
        user_id=user.id,
        name=routine_data.name,
        category=routine_data.category,
        routine_schedule=routine_schedule,
        description=routine_data.description,
        tasks=tasks,
    )
    created = await create_routine_handler.handle(CreateRoutineCommand(routine=routine))
    return map_routine_to_schema(created)


@router.put("/{uuid}", response_model=RoutineSchema)
async def update_routine(
    uuid: UUID,
    update_data: RoutineUpdateSchema,
    command_factory: Annotated[
        CommandHandlerFactory, Depends(command_handler_factory)
    ],
) -> RoutineSchema:
    """Update an existing routine."""
    update_routine_handler = command_factory.create(UpdateRoutineHandler)
    # Convert schema to domain dataclasses
    from lykke.domain.value_objects.routine import RecurrenceSchedule, RoutineTask
    from lykke.domain.value_objects.task import TaskSchedule

    routine_schedule = None
    if update_data.routine_schedule:
        routine_schedule = RecurrenceSchedule(
            frequency=update_data.routine_schedule.frequency,
            weekdays=update_data.routine_schedule.weekdays,
            day_number=update_data.routine_schedule.day_number,
        )

    tasks = None
    if update_data.tasks is not None:
        tasks = []
        for task_schema in update_data.tasks:
            task_schedule = None
            if task_schema.schedule:
                task_schedule = TaskSchedule(
                    available_time=task_schema.schedule.available_time,
                    start_time=task_schema.schedule.start_time,
                    end_time=task_schema.schedule.end_time,
                    timing_type=task_schema.schedule.timing_type,
                )

            task_recurrence_schedule = None
            if task_schema.task_schedule:
                task_recurrence_schedule = RecurrenceSchedule(
                    frequency=task_schema.task_schedule.frequency,
                    weekdays=task_schema.task_schedule.weekdays,
                    day_number=task_schema.task_schedule.day_number,
                )

            if task_schema.id:
                routine_task = RoutineTask(
                    id=task_schema.id,
                    task_definition_id=task_schema.task_definition_id,
                    name=task_schema.name,
                    schedule=task_schedule,
                    task_schedule=task_recurrence_schedule,
                )
            else:
                routine_task = RoutineTask(
                    task_definition_id=task_schema.task_definition_id,
                    name=task_schema.name,
                    schedule=task_schedule,
                    task_schedule=task_recurrence_schedule,
                )
            tasks.append(routine_task)

    update_object = RoutineUpdateObject(
        name=update_data.name,
        category=update_data.category,
        routine_schedule=routine_schedule,
        description=update_data.description,
        tasks=tasks,
    )
    updated = await update_routine_handler.handle(
        UpdateRoutineCommand(routine_id=uuid, update_data=update_object)
    )
    return map_routine_to_schema(updated)


@router.delete("/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_routine(
    uuid: UUID,
    command_factory: Annotated[
        CommandHandlerFactory, Depends(command_handler_factory)
    ],
) -> None:
    """Delete a routine."""
    delete_routine_handler = command_factory.create(DeleteRoutineHandler)
    await delete_routine_handler.handle(DeleteRoutineCommand(routine_id=uuid))


@router.post(
    "/{uuid}/tasks",
    response_model=RoutineSchema,
    status_code=status.HTTP_201_CREATED,
)
async def add_routine_task(
    uuid: UUID,
    routine_task: RoutineTaskCreateSchema,
    command_factory: Annotated[
        CommandHandlerFactory, Depends(command_handler_factory)
    ],
) -> RoutineSchema:
    """Attach a task definition to a routine."""
    add_routine_task_handler = command_factory.create(AddRoutineTaskHandler)
    from lykke.domain.value_objects.routine import RecurrenceSchedule
    from lykke.domain.value_objects.task import TaskSchedule

    task_schedule = None
    if routine_task.schedule:
        task_schedule = TaskSchedule(
            available_time=routine_task.schedule.available_time,
            start_time=routine_task.schedule.start_time,
            end_time=routine_task.schedule.end_time,
            timing_type=routine_task.schedule.timing_type,
        )

    task_recurrence_schedule = None
    if routine_task.task_schedule:
        task_recurrence_schedule = RecurrenceSchedule(
            frequency=routine_task.task_schedule.frequency,
            weekdays=routine_task.task_schedule.weekdays,
            day_number=routine_task.task_schedule.day_number,
        )

    updated = await add_routine_task_handler.handle(
        AddRoutineTaskCommand(
            routine_id=uuid,
            routine_task=RoutineTask(
                task_definition_id=routine_task.task_definition_id,
                name=routine_task.name,
                schedule=task_schedule,
                task_schedule=task_recurrence_schedule,
            ),
        )
    )
    return map_routine_to_schema(updated)


@router.put(
    "/{uuid}/tasks/{routine_task_id}",
    response_model=RoutineSchema,
)
async def update_routine_task(
    uuid: UUID,
    routine_task_id: UUID,
    routine_task_update: RoutineTaskUpdateSchema,
    command_factory: Annotated[
        CommandHandlerFactory, Depends(command_handler_factory)
    ],
) -> RoutineSchema:
    """Update an attached routine task (name/schedule)."""
    update_routine_task_handler = command_factory.create(
        UpdateRoutineTaskHandler
    )
    from lykke.domain.value_objects.routine import RecurrenceSchedule
    from lykke.domain.value_objects.task import TaskSchedule

    task_schedule = None
    if routine_task_update.schedule:
        task_schedule = TaskSchedule(
            available_time=routine_task_update.schedule.available_time,
            start_time=routine_task_update.schedule.start_time,
            end_time=routine_task_update.schedule.end_time,
            timing_type=routine_task_update.schedule.timing_type,
        )

    task_recurrence_schedule = None
    if routine_task_update.task_schedule:
        task_recurrence_schedule = RecurrenceSchedule(
            frequency=routine_task_update.task_schedule.frequency,
            weekdays=routine_task_update.task_schedule.weekdays,
            day_number=routine_task_update.task_schedule.day_number,
        )

    updated = await update_routine_task_handler.handle(
        UpdateRoutineTaskCommand(
            routine_id=uuid,
            routine_task_id=routine_task_id,
            routine_task=RoutineTask(
                id=routine_task_id,
                task_definition_id=UUID(
                    "00000000-0000-0000-0000-000000000000"
                ),  # Will be preserved from existing task
                name=routine_task_update.name,
                schedule=task_schedule,
                task_schedule=task_recurrence_schedule,
            ),
        )
    )
    return map_routine_to_schema(updated)


@router.delete(
    "/{uuid}/tasks/{routine_task_id}",
    response_model=RoutineSchema,
)
async def remove_routine_task(
    uuid: UUID,
    routine_task_id: UUID,
    command_factory: Annotated[
        CommandHandlerFactory, Depends(command_handler_factory)
    ],
) -> RoutineSchema:
    """Detach a routine task from a routine by RoutineTask.id."""
    remove_routine_task_handler = command_factory.create(
        RemoveRoutineTaskHandler
    )
    updated = await remove_routine_task_handler.handle(
        RemoveRoutineTaskCommand(routine_id=uuid, routine_task_id=routine_task_id)
    )
    return map_routine_to_schema(updated)


@router.post("/{uuid}/actions")
async def record_routine_action(
    uuid: UUID,
    action: value_objects.Action,
    command_factory: Annotated[
        CommandHandlerFactory, Depends(command_handler_factory)
    ],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> list[TaskSchema]:
    """Record an action on all tasks in a routine for today."""
    from datetime import date
    from lykke.core.utils.dates import get_current_date
    from lykke.presentation.api.schemas.mappers import map_task_to_schema

    today: date = get_current_date(user.settings.timezone)
    handler = command_factory.create(RecordRoutineActionHandler)
    updated_tasks = await handler.handle(
        RecordRoutineActionCommand(routine_id=uuid, action=action, date=today)
    )
    return [map_task_to_schema(task) for task in updated_tasks]
