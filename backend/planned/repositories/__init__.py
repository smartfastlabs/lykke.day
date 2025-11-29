from .auth_token import AuthTokenRepository
from .calendar import CalendarRepository
from .event import EventRepository
from .push_subscription import PushSubscriptionRepository
from .routine import RoutineRepository
from .task import TaskRepository
from .task_definition import TaskDefinitionRepository

auth_token_repo = AuthTokenRepository()
calendar_repo = CalendarRepository()
event_repo = EventRepository()
push_subscription_repo = PushSubscriptionRepository()
routine_repo = RoutineRepository()
task_repo = TaskRepository()
task_definition_repo = TaskDefinitionRepository()
