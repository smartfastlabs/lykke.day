import datetime

from planned import objects
from planned.repositories import event_repo

from .base import BaseService
from .routine import routine_svc


class PlanningService(BaseService):
    async def schedule_day(self, date: datetime.date):
        return objects.Day(
            date=date,
            events= await event_repo.search(date),
            routine_instances= await routine_svc.schedule(date),
        )

planning_svc = PlanningService()
