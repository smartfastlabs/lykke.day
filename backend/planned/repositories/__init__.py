from .auth_token import AuthTokenRepository
from .calendar import CalendarRepository
from .event import EventRepository
from .push_subscription import PushSubscriptionRepository
from .routine import RoutineRepository
from .routine_instance import RoutineInstanceRepository

auth_token_repo = AuthTokenRepository()
calendar_repo = CalendarRepository()
event_repo = EventRepository()
push_subscription_repo = PushSubscriptionRepository()
routine_repo = RoutineRepository()
routine_instance_repo = RoutineInstanceRepository()
