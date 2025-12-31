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
    UserRepository,
)


@pytest.mark.asyncio
@pytest.mark.skip
async def test_schedule_today(test_date, test_user):
    user_id = test_user.id
    # Create repository instances
    day_repo = DayRepository(user_id=user_id)
    day_template_repo = DayTemplateRepository(user_id=user_id)
    event_repo = EventRepository(user_id=user_id)
    message_repo = MessageRepository(user_id=user_id)
    routine_repo = RoutineRepository(user_id=user_id)
    task_definition_repo = TaskDefinitionRepository(user_id=user_id)
    task_repo = TaskRepository(user_id=user_id)
    user_repo = UserRepository()

    # Create planning service with repositories
    planning_svc = PlanningService(
        user=test_user,
        user_repo=user_repo,
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

    # Load context and create service
    ctx = await DayService.load_context_cls(
        test_date,
        user_id=user_id,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        task_repo=task_repo,
        user_repo=user_repo,
    )
    day_svc = DayService(
        user=test_user,
        ctx=ctx,
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
async def test_schedule_tomorrow(test_date_tomorrow, test_user):
    user_id = test_user.id
    # Create repository instances
    day_repo = DayRepository(user_id=user_id)
    day_template_repo = DayTemplateRepository(user_id=user_id)
    event_repo = EventRepository(user_id=user_id)
    message_repo = MessageRepository(user_id=user_id)
    routine_repo = RoutineRepository(user_id=user_id)
    task_definition_repo = TaskDefinitionRepository(user_id=user_id)
    task_repo = TaskRepository(user_id=user_id)
    user_repo = UserRepository()

    # Create planning service with repositories
    planning_svc = PlanningService(
        user=test_user,
        user_repo=user_repo,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        routine_repo=routine_repo,
        task_definition_repo=task_definition_repo,
        task_repo=task_repo,
    )

    result = await planning_svc.schedule(test_date_tomorrow)

    # Check that template is set (we can't check the exact value since it's a UUID)
    assert result.day.template is not None
    assert len(result.events) == 0
    assert len(result.tasks) == 2
