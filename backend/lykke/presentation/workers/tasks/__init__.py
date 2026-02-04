"""Background task definitions using Taskiq."""

from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource

from lykke.infrastructure.workers.config import broker

from .alarms import trigger_alarms_for_all_users_task, trigger_alarms_for_user_task
from .brain_dump import process_brain_dump_item_task
from .calendar import (
    resubscribe_calendar_task,
    sync_calendar_task,
    sync_single_calendar_task,
)
from .common import (
    get_calendar_entry_notification_handler,
    get_google_gateway,
    get_morning_overview_handler,
    get_process_brain_dump_handler,
    get_process_inbound_sms_handler,
    get_read_only_repository_factory,
    get_schedule_day_handler,
    get_smart_notification_handler,
    get_subscribe_calendar_handler,
    get_sync_all_calendars_handler,
    get_sync_calendar_handler,
    get_unit_of_work_factory,
    get_user_repository,
)
from .inbound_sms import process_inbound_sms_message_task
from .misc import example_triggered_task, heartbeat_task
from .new_day import (
    emit_new_day_event_for_all_users_task,
    emit_new_day_event_for_user_task,
)
from .notifications import (
    evaluate_calendar_entry_notifications_for_all_users_task,
    evaluate_calendar_entry_notifications_task,
    evaluate_morning_overview_task,
    evaluate_morning_overviews_for_all_users_task,
    evaluate_smart_notification_task,
    evaluate_smart_notifications_for_all_users_task,
)
from .registration import register_worker_event_handlers
from .registry import (
    WorkerRegistry,
    clear_worker_overrides,
    get_worker,
    set_worker_override,
)
from .scheduling import schedule_all_users_day_task, schedule_user_day_task

# Create a scheduler for periodic tasks
scheduler = TaskiqScheduler(broker=broker, sources=[LabelScheduleSource(broker)])

# Ensure handlers are registered when the worker tasks module is imported
register_worker_event_handlers()

from .post_commit_workers import WorkersToSchedule

__all__ = [
    "WorkerRegistry",
    "WorkersToSchedule",
    "clear_worker_overrides",
    "emit_new_day_event_for_all_users_task",
    "emit_new_day_event_for_user_task",
    "evaluate_calendar_entry_notifications_for_all_users_task",
    "evaluate_calendar_entry_notifications_task",
    "evaluate_morning_overview_task",
    "evaluate_morning_overviews_for_all_users_task",
    "evaluate_smart_notification_task",
    "evaluate_smart_notifications_for_all_users_task",
    "example_triggered_task",
    "get_calendar_entry_notification_handler",
    "get_google_gateway",
    "get_morning_overview_handler",
    "get_process_brain_dump_handler",
    "get_process_inbound_sms_handler",
    "get_read_only_repository_factory",
    "get_schedule_day_handler",
    "get_smart_notification_handler",
    "get_subscribe_calendar_handler",
    "get_sync_all_calendars_handler",
    "get_sync_calendar_handler",
    "get_unit_of_work_factory",
    "get_user_repository",
    "get_worker",
    "heartbeat_task",
    "process_brain_dump_item_task",
    "process_inbound_sms_message_task",
    "register_worker_event_handlers",
    "resubscribe_calendar_task",
    "schedule_all_users_day_task",
    "schedule_user_day_task",
    "scheduler",
    "set_worker_override",
    "sync_calendar_task",
    "sync_single_calendar_task",
    "trigger_alarms_for_all_users_task",
    "trigger_alarms_for_user_task",
]
