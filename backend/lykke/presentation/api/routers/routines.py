"""Router for RoutineDefinition CRUD operations."""

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from lykke.application.commands import (
    RecordRoutineDefinitionActionCommand,
    RecordRoutineDefinitionActionHandler,
)
from lykke.application.commands.routine import (
    AddRoutineDefinitionTaskCommand,
    AddRoutineDefinitionTaskHandler,
    CreateRoutineDefinitionCommand,
    CreateRoutineDefinitionHandler,
    DeleteRoutineDefinitionCommand,
    DeleteRoutineDefinitionHandler,
    RemoveRoutineDefinitionTaskCommand,
    RemoveRoutineDefinitionTaskHandler,
    UpdateRoutineDefinitionCommand,
    UpdateRoutineDefinitionHandler,
    UpdateRoutineDefinitionTaskCommand,
    UpdateRoutineDefinitionTaskHandler,
)
from lykke.application.queries.routine import (
    GetRoutineDefinitionHandler,
    GetRoutineDefinitionQuery,
    SearchRoutineDefinitionsHandler,
    SearchRoutineDefinitionsQuery,
)
from lykke.domain import value_objects
from lykke.domain.entities import RoutineDefinitionEntity, UserEntity
from lykke.domain.value_objects import RoutineDefinitionUpdateObject
from lykke.domain.value_objects.routine import (
    RecurrenceSchedule,
    RoutineDefinitionTask,
    TimeWindow,
)
from lykke.presentation.api.schemas import (
    PagedResponseSchema,
    QuerySchema,
    RoutineDefinitionCreateSchema,
    RoutineDefinitionSchema,
    RoutineDefinitionTaskCreateSchema,
    RoutineDefinitionTaskUpdateSchema,
    RoutineDefinitionUpdateSchema,
    TaskSchema,
)
from lykke.presentation.api.schemas.mappers import map_routine_definition_to_schema
from lykke.presentation.handler_factory import (
    CommandHandlerFactory,
    QueryHandlerFactory,
)

from .dependencies.factories import command_handler_factory, query_handler_factory
from .dependencies.user import get_current_user
from .utils import build_search_query, create_paged_response

if TYPE_CHECKING:
    from datetime import date

router = APIRouter()


@router.get("/{uuid}", response_model=RoutineDefinitionSchema)
async def get_routine_definition(
    uuid: UUID,
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
) -> RoutineDefinitionSchema:
    """Get a single routine definition by ID."""
    get_routine_definition_handler = query_factory.create(
        GetRoutineDefinitionHandler
    )
    routine_definition = await get_routine_definition_handler.handle(
        GetRoutineDefinitionQuery(routine_definition_id=uuid)
    )
    return map_routine_definition_to_schema(routine_definition)


@router.post("/", response_model=PagedResponseSchema[RoutineDefinitionSchema])
async def search_routine_definitions(
    query_factory: Annotated[QueryHandlerFactory, Depends(query_handler_factory)],
    query: QuerySchema[value_objects.RoutineDefinitionQuery],
) -> PagedResponseSchema[RoutineDefinitionSchema]:
    """Search routine definitions with pagination and optional filters."""
    list_routine_definitions_handler = query_factory.create(
        SearchRoutineDefinitionsHandler
    )
    search_query = build_search_query(query, value_objects.RoutineDefinitionQuery)
    result = await list_routine_definitions_handler.handle(
        SearchRoutineDefinitionsQuery(search_query=search_query)
    )
    return create_paged_response(result, map_routine_definition_to_schema)


@router.post(
    "/create",
    response_model=RoutineDefinitionSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_routine_definition(
    routine_definition_data: RoutineDefinitionCreateSchema,
    user: Annotated[UserEntity, Depends(get_current_user)],
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> RoutineDefinitionSchema:
    """Create a new routine definition."""
    create_routine_definition_handler = command_factory.create(
        CreateRoutineDefinitionHandler
    )
    # Convert schema to domain dataclasses
    from lykke.domain.value_objects.task import TaskSchedule

    routine_definition_schedule = RecurrenceSchedule(
        frequency=routine_definition_data.routine_definition_schedule.frequency,
        weekdays=routine_definition_data.routine_definition_schedule.weekdays,
        day_number=routine_definition_data.routine_definition_schedule.day_number,
    )

    routine_time_window = None
    if routine_definition_data.time_window:
        routine_time_window = TimeWindow(
            available_time=routine_definition_data.time_window.available_time,
            start_time=routine_definition_data.time_window.start_time,
            end_time=routine_definition_data.time_window.end_time,
            cutoff_time=routine_definition_data.time_window.cutoff_time,
        )

    tasks = []
    for task_schema in routine_definition_data.tasks or []:
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

        time_window = None
        if task_schema.time_window:
            time_window = TimeWindow(
                available_time=task_schema.time_window.available_time,
                start_time=task_schema.time_window.start_time,
                end_time=task_schema.time_window.end_time,
                cutoff_time=task_schema.time_window.cutoff_time,
            )

        if task_schema.id:
            routine_task = RoutineDefinitionTask(
                id=task_schema.id,
                task_definition_id=task_schema.task_definition_id,
                name=task_schema.name,
                schedule=task_schedule,
                task_schedule=task_recurrence_schedule,
                time_window=time_window,
            )
        else:
            routine_task = RoutineDefinitionTask(
                task_definition_id=task_schema.task_definition_id,
                name=task_schema.name,
                schedule=task_schedule,
                task_schedule=task_recurrence_schedule,
                time_window=time_window,
            )
        tasks.append(routine_task)

    routine_definition = RoutineDefinitionEntity(
        user_id=user.id,
        name=routine_definition_data.name,
        category=routine_definition_data.category,
        routine_definition_schedule=routine_definition_schedule,
        description=routine_definition_data.description,
        time_window=routine_time_window,
        tasks=tasks,
    )
    created = await create_routine_definition_handler.handle(
        CreateRoutineDefinitionCommand(routine_definition=routine_definition)
    )
    return map_routine_definition_to_schema(created)


@router.put("/{uuid}", response_model=RoutineDefinitionSchema)
async def update_routine_definition(
    uuid: UUID,
    update_data: RoutineDefinitionUpdateSchema,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> RoutineDefinitionSchema:
    """Update an existing routine definition."""
    update_routine_definition_handler = command_factory.create(
        UpdateRoutineDefinitionHandler
    )
    # Convert schema to domain dataclasses
    from lykke.domain.value_objects.task import TaskSchedule

    routine_definition_schedule = None
    if update_data.routine_definition_schedule:
        routine_definition_schedule = RecurrenceSchedule(
            frequency=update_data.routine_definition_schedule.frequency,
            weekdays=update_data.routine_definition_schedule.weekdays,
            day_number=update_data.routine_definition_schedule.day_number,
        )

    routine_time_window = None
    if update_data.time_window:
        routine_time_window = TimeWindow(
            available_time=update_data.time_window.available_time,
            start_time=update_data.time_window.start_time,
            end_time=update_data.time_window.end_time,
            cutoff_time=update_data.time_window.cutoff_time,
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

            time_window = None
            if task_schema.time_window:
                time_window = TimeWindow(
                    available_time=task_schema.time_window.available_time,
                    start_time=task_schema.time_window.start_time,
                    end_time=task_schema.time_window.end_time,
                    cutoff_time=task_schema.time_window.cutoff_time,
                )

            if task_schema.id:
                routine_task = RoutineDefinitionTask(
                    id=task_schema.id,
                    task_definition_id=task_schema.task_definition_id,
                    name=task_schema.name,
                    schedule=task_schedule,
                    task_schedule=task_recurrence_schedule,
                    time_window=time_window,
                )
            else:
                routine_task = RoutineDefinitionTask(
                    task_definition_id=task_schema.task_definition_id,
                    name=task_schema.name,
                    schedule=task_schedule,
                    task_schedule=task_recurrence_schedule,
                    time_window=time_window,
                )
            tasks.append(routine_task)

    update_object = RoutineDefinitionUpdateObject(
        name=update_data.name,
        category=update_data.category,
        routine_definition_schedule=routine_definition_schedule,
        description=update_data.description,
        time_window=routine_time_window,
        tasks=tasks,
    )
    updated = await update_routine_definition_handler.handle(
        UpdateRoutineDefinitionCommand(
            routine_definition_id=uuid,
            update_data=update_object,
        )
    )
    return map_routine_definition_to_schema(updated)


@router.delete("/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_routine_definition(
    uuid: UUID,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> None:
    """Delete a routine definition."""
    delete_routine_definition_handler = command_factory.create(
        DeleteRoutineDefinitionHandler
    )
    await delete_routine_definition_handler.handle(
        DeleteRoutineDefinitionCommand(routine_definition_id=uuid)
    )


@router.post(
    "/{uuid}/tasks",
    response_model=RoutineDefinitionSchema,
    status_code=status.HTTP_201_CREATED,
)
async def add_routine_definition_task(
    uuid: UUID,
    routine_task: RoutineDefinitionTaskCreateSchema,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> RoutineDefinitionSchema:
    """Attach a task definition to a routine definition."""
    add_routine_definition_task_handler = command_factory.create(
        AddRoutineDefinitionTaskHandler
    )
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

    time_window = None
    if routine_task.time_window:
        time_window = TimeWindow(
            available_time=routine_task.time_window.available_time,
            start_time=routine_task.time_window.start_time,
            end_time=routine_task.time_window.end_time,
            cutoff_time=routine_task.time_window.cutoff_time,
        )

    updated = await add_routine_definition_task_handler.handle(
        AddRoutineDefinitionTaskCommand(
            routine_definition_id=uuid,
            routine_definition_task=RoutineDefinitionTask(
                task_definition_id=routine_task.task_definition_id,
                name=routine_task.name,
                schedule=task_schedule,
                task_schedule=task_recurrence_schedule,
                time_window=time_window,
            ),
        )
    )
    return map_routine_definition_to_schema(updated)


@router.put(
    "/{uuid}/tasks/{routine_definition_task_id}",
    response_model=RoutineDefinitionSchema,
)
async def update_routine_definition_task(
    uuid: UUID,
    routine_definition_task_id: UUID,
    routine_task_update: RoutineDefinitionTaskUpdateSchema,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> RoutineDefinitionSchema:
    """Update an attached routine definition task (name/schedule)."""
    update_routine_definition_task_handler = command_factory.create(
        UpdateRoutineDefinitionTaskHandler
    )
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

    time_window = None
    if routine_task_update.time_window:
        time_window = TimeWindow(
            available_time=routine_task_update.time_window.available_time,
            start_time=routine_task_update.time_window.start_time,
            end_time=routine_task_update.time_window.end_time,
            cutoff_time=routine_task_update.time_window.cutoff_time,
        )

    updated = await update_routine_definition_task_handler.handle(
        UpdateRoutineDefinitionTaskCommand(
            routine_definition_id=uuid,
            routine_definition_task_id=routine_definition_task_id,
            routine_definition_task=RoutineDefinitionTask(
                id=routine_definition_task_id,
                task_definition_id=UUID(
                    "00000000-0000-0000-0000-000000000000"
                ),  # Will be preserved from existing task
                name=routine_task_update.name,
                schedule=task_schedule,
                task_schedule=task_recurrence_schedule,
                time_window=time_window,
            ),
        )
    )
    return map_routine_definition_to_schema(updated)


@router.delete(
    "/{uuid}/tasks/{routine_definition_task_id}",
    response_model=RoutineDefinitionSchema,
)
async def remove_routine_definition_task(
    uuid: UUID,
    routine_definition_task_id: UUID,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
) -> RoutineDefinitionSchema:
    """Detach a routine definition task from a routine definition by RoutineDefinitionTask.id."""
    remove_routine_definition_task_handler = command_factory.create(
        RemoveRoutineDefinitionTaskHandler
    )
    updated = await remove_routine_definition_task_handler.handle(
        RemoveRoutineDefinitionTaskCommand(
            routine_definition_id=uuid,
            routine_definition_task_id=routine_definition_task_id,
        )
    )
    return map_routine_definition_to_schema(updated)


@router.post("/{uuid}/actions")
async def record_routine_definition_action(
    uuid: UUID,
    action: value_objects.Action,
    command_factory: Annotated[CommandHandlerFactory, Depends(command_handler_factory)],
    user: Annotated[UserEntity, Depends(get_current_user)],
) -> list[TaskSchema]:
    """Record an action on all tasks in a routine definition for today."""
    from lykke.core.utils.dates import get_current_date
    from lykke.presentation.api.schemas.mappers import map_task_to_schema

    today: date = get_current_date(user.settings.timezone)
    handler = command_factory.create(RecordRoutineDefinitionActionHandler)
    updated_tasks = await handler.handle(
        RecordRoutineDefinitionActionCommand(
            routine_definition_id=uuid, action=action, date=today
        )
    )
    return [map_task_to_schema(task) for task in updated_tasks]
