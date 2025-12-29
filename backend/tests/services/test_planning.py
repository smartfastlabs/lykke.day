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
async def test_schedule_today(test_date, test_user):
    from uuid import UUID

    from planned.infrastructure.repositories import UserRepository

    user_uuid = test_user.uuid
    # Create repository instances
    day_repo = DayRepository(user_uuid=user_uuid)
    day_template_repo = DayTemplateRepository(user_uuid=user_uuid)
    event_repo = EventRepository(user_uuid=user_uuid)
    message_repo = MessageRepository(user_uuid=user_uuid)
    routine_repo = RoutineRepository(user_uuid=user_uuid)
    task_definition_repo = TaskDefinitionRepository(user_uuid=user_uuid)
    task_repo = TaskRepository(user_uuid=user_uuid)
    user_repo = UserRepository()

    # Create planning service with repositories
    planning_svc = PlanningService(
        user_uuid=user_uuid,
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

    day_svc = await DayService.for_date(
        test_date,
        user_uuid=user_uuid,
        day_repo=day_repo,
        day_template_repo=day_template_repo,
        event_repo=event_repo,
        message_repo=message_repo,
        task_repo=task_repo,
        user_repo=user_repo,
    )

    def sort_tasks(tasks):
        return sorted(tasks, key=lambda t: t.name)

    assert sort_tasks(day_svc.ctx.tasks) == sort_tasks(result.tasks)
    assert day_svc.ctx.day == result.day


@pytest.mark.asyncio
@pytest.mark.skip
async def test_schedule_tomorrow(test_date_tomorrow, test_user):
    from uuid import UUID

    from planned.infrastructure.repositories import UserRepository

    user_uuid = test_user.uuid
    # Create repository instances
    day_repo = DayRepository(user_uuid=user_uuid)
    day_template_repo = DayTemplateRepository(user_uuid=user_uuid)
    event_repo = EventRepository(user_uuid=user_uuid)
    message_repo = MessageRepository(user_uuid=user_uuid)
    routine_repo = RoutineRepository(user_uuid=user_uuid)
    task_definition_repo = TaskDefinitionRepository(user_uuid=user_uuid)
    task_repo = TaskRepository(user_uuid=user_uuid)
    user_repo = UserRepository()

    # Create planning service with repositories
    planning_svc = PlanningService(
        user_uuid=user_uuid,
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

    assert result.day.template_id == "weekend"
    assert len(result.events) == 0
    assert len(result.tasks) == 2
