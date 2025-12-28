import pytest

from planned.application.services import DayService, PlanningService
from planned.infrastructure.repositories import (
    DayRepository,
    DayTemplateRepository,
    EventRepository,
    MessageRepository,
    RoutineRepository,
    TaskDefinitionRepository,
    TaskRepository,
)


@pytest.mark.asyncio
@pytest.mark.skip
async def test_schedule_today(test_date):
    # Create repository instances
    day_repo = DayRepository()
    day_template_repo = DayTemplateRepository()
    event_repo = EventRepository()
    message_repo = MessageRepository()
    routine_repo = RoutineRepository()
    task_definition_repo = TaskDefinitionRepository()
    task_repo = TaskRepository()

    # Create planning service with repositories
    planning_svc = PlanningService(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        routine_repo=routine_repo,
        task_definition_repo=task_definition_repo,
        task_repo=task_repo,
    )

    result = await planning_svc.schedule(test_date)
    assert len(result.events) == 1

    assert result.events[0].name == "Sifleet Family Thanksgiving"

    assert len(result.tasks) == 2

    day_svc = await DayService.for_date(
        test_date,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        task_repo=task_repo,
    )

    def sort_tasks(tasks):
        return sorted(tasks, key=lambda t: t.name)

    assert sort_tasks(day_svc.ctx.tasks) == sort_tasks(result.tasks)
    assert day_svc.ctx.day == result.day


@pytest.mark.asyncio
@pytest.mark.skip
async def test_schedule_tomorrow(test_date_tomorrow):
    # Create repository instances
    day_repo = DayRepository()
    day_template_repo = DayTemplateRepository()
    event_repo = EventRepository()
    message_repo = MessageRepository()
    routine_repo = RoutineRepository()
    task_definition_repo = TaskDefinitionRepository()
    task_repo = TaskRepository()

    # Create planning service with repositories
    planning_svc = PlanningService(
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        routine_repo=routine_repo,
        task_definition_repo=task_definition_repo,
        task_repo=task_repo,
    )

    result = await planning_svc.schedule(test_date_tomorrow)

    assert result.day.template_id == "weekend"
    assert len(result.events) == 0
    assert len(result.tasks) == 2
