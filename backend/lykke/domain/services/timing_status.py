from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date as dt_date, datetime, time, timedelta, tzinfo

from lykke.core.utils.dates import ensure_utc, resolve_timezone
from lykke.domain.entities import RoutineEntity, TaskEntity
from lykke.domain.value_objects import (
    TaskStatus,
    TimeWindow,
    TimingStatus,
    TimingStatusInfo,
)

UPCOMING_WINDOW_TASK = timedelta(minutes=30)
UPCOMING_WINDOW_ROUTINE = timedelta(hours=2)


@dataclass(frozen=True)
class EffectiveWindow:
    availability_start: datetime | None
    availability_end: datetime | None
    active_start: datetime | None
    active_end: datetime | None


class TimingStatusService:
    """Pure timing status computations for tasks and routines."""

    @staticmethod
    def task_status(
        task: TaskEntity,
        now: datetime,
        *,
        timezone: str | None = None,
        routine_time_window: TimeWindow | None = None,
        routine_snoozed_until: datetime | None = None,
        upcoming_window: timedelta = UPCOMING_WINDOW_TASK,
    ) -> TimingStatusInfo:
        if task.status in (TaskStatus.COMPLETE, TaskStatus.PUNT):
            return TimingStatusInfo(status=TimingStatus.HIDDEN)

        tzinfo = TimingStatusService._resolve_tzinfo(now, timezone)
        window = TimingStatusService._build_effective_window(
            task_date=task.scheduled_date,
            task_time_window=task.time_window,
            routine_time_window=routine_time_window,
            tzinfo=tzinfo,
        )

        snoozed_until = TimingStatusService._resolve_snoozed_until(
            task.snoozed_until, routine_snoozed_until
        )

        return TimingStatusService._status_from_window(
            now=now,
            window=window,
            snoozed_until=snoozed_until,
            upcoming_window=upcoming_window,
        )

    @staticmethod
    def routine_status(
        routine: RoutineEntity,
        tasks: Iterable[TaskEntity],
        now: datetime,
        *,
        timezone: str | None = None,
        upcoming_window: timedelta = UPCOMING_WINDOW_ROUTINE,
    ) -> TimingStatusInfo:
        relevant_tasks = [
            task
            for task in tasks
            if task.routine_definition_id == routine.routine_definition_id
        ]
        if not relevant_tasks:
            return TimingStatusInfo(status=TimingStatus.HIDDEN)

        task_infos = [
            TimingStatusService.task_status(
                task,
                now,
                timezone=timezone,
                routine_time_window=routine.time_window,
                routine_snoozed_until=routine.snoozed_until,
                upcoming_window=upcoming_window,
            )
            for task in relevant_tasks
        ]

        has_past_due = any(info.status == TimingStatus.PAST_DUE for info in task_infos)
        has_active = any(info.status == TimingStatus.ACTIVE for info in task_infos)
        has_available = any(
            info.status == TimingStatus.AVAILABLE for info in task_infos
        )
        has_inactive = any(info.status == TimingStatus.INACTIVE for info in task_infos)

        next_available = TimingStatusService._earliest_time(
            [info.next_available_time for info in task_infos]
        )
        if routine.snoozed_until and routine.snoozed_until > now:
            snoozed_until = ensure_utc(routine.snoozed_until) or routine.snoozed_until
            next_available = TimingStatusService._latest_time(
                next_available, snoozed_until
            )
            return TimingStatusInfo(
                status=TimingStatus.HIDDEN, next_available_time=next_available
            )

        if has_past_due:
            return TimingStatusInfo(status=TimingStatus.PAST_DUE)
        if has_active:
            return TimingStatusInfo(status=TimingStatus.ACTIVE)
        if has_available:
            return TimingStatusInfo(status=TimingStatus.AVAILABLE)
        if has_inactive:
            return TimingStatusInfo(
                status=TimingStatus.INACTIVE, next_available_time=next_available
            )
        return TimingStatusInfo(
            status=TimingStatus.HIDDEN, next_available_time=next_available
        )

    @staticmethod
    def _resolve_tzinfo(now: datetime, timezone: str | None) -> tzinfo:
        if timezone is not None:
            return resolve_timezone(timezone)
        if now.tzinfo is not None:
            return now.tzinfo
        return UTC

    @staticmethod
    def _resolve_snoozed_until(
        task_snoozed_until: datetime | None,
        routine_snoozed_until: datetime | None,
    ) -> datetime | None:
        task_value = ensure_utc(task_snoozed_until) if task_snoozed_until else None
        routine_value = (
            ensure_utc(routine_snoozed_until) if routine_snoozed_until else None
        )
        return TimingStatusService._latest_time(task_value, routine_value)

    @staticmethod
    def _build_effective_window(
        *,
        task_date: dt_date,
        task_time_window: TimeWindow | None,
        routine_time_window: TimeWindow | None,
        tzinfo: tzinfo,
    ) -> EffectiveWindow | None:
        task_window = TimingStatusService._window_from_time_window(
            task_time_window, task_date, tzinfo
        )
        routine_window = TimingStatusService._window_from_time_window(
            routine_time_window, task_date, tzinfo
        )
        if task_window is None and routine_window is None:
            return None

        availability_start = TimingStatusService._latest_time(
            task_window.availability_start if task_window else None,
            routine_window.availability_start if routine_window else None,
        )
        availability_end = TimingStatusService._earliest_time(
            [
                task_window.availability_end if task_window else None,
                routine_window.availability_end if routine_window else None,
            ]
        )
        active_start = TimingStatusService._latest_time(
            task_window.active_start if task_window else None,
            routine_window.active_start if routine_window else None,
        )
        active_end = TimingStatusService._earliest_time(
            [
                task_window.active_end if task_window else None,
                routine_window.active_end if routine_window else None,
            ]
        )

        if availability_start and availability_end and availability_end < availability_start:
            return None

        if active_start and active_end and active_end < active_start:
            active_start = None
            active_end = None

        return EffectiveWindow(
            availability_start=availability_start,
            availability_end=availability_end,
            active_start=active_start,
            active_end=active_end,
        )

    @staticmethod
    def _window_from_time_window(
        time_window: TimeWindow | None, task_date: dt_date, tzinfo: tzinfo
    ) -> EffectiveWindow | None:
        if time_window is None:
            return None

        def combine_time(value: time | None) -> datetime | None:
            if value is None:
                return None
            return datetime.combine(task_date, value, tzinfo=tzinfo)

        availability_start_time: time | None = (
            time_window.available_time or time_window.start_time
        )
        if time_window.start_time and not (
            time_window.end_time or time_window.cutoff_time
        ):
            availability_end_time: time | None = time_window.start_time
        else:
            availability_end_time = time_window.cutoff_time or time_window.end_time

        if time_window.start_time and (time_window.end_time or time_window.cutoff_time):
            active_start_time: time | None = time_window.start_time
            active_end_time: time | None = (
                time_window.end_time or time_window.cutoff_time
            )
        else:
            active_start_time = None
            active_end_time = None

        return EffectiveWindow(
            availability_start=combine_time(availability_start_time),
            availability_end=combine_time(availability_end_time),
            active_start=combine_time(active_start_time),
            active_end=combine_time(active_end_time),
        )

    @staticmethod
    def _status_from_window(
        *,
        now: datetime,
        window: EffectiveWindow | None,
        snoozed_until: datetime | None,
        upcoming_window: timedelta,
    ) -> TimingStatusInfo:
        if snoozed_until and snoozed_until > now:
            next_available: datetime | None = snoozed_until
            if window and window.availability_start:
                next_available = TimingStatusService._latest_time(
                    next_available, window.availability_start
                )
            return TimingStatusInfo(
                status=TimingStatus.HIDDEN, next_available_time=next_available
            )

        if window is None or (
            window.availability_start is None
            and window.availability_end is None
            and window.active_start is None
            and window.active_end is None
        ):
            return TimingStatusInfo(status=TimingStatus.AVAILABLE)

        if window.availability_end and now > window.availability_end:
            return TimingStatusInfo(status=TimingStatus.PAST_DUE)

        if window.active_start and now >= window.active_start:
            if window.active_end is None or now <= window.active_end:
                return TimingStatusInfo(status=TimingStatus.ACTIVE)

        if (
            window.availability_start is None or now >= window.availability_start
        ) and (window.availability_end is None or now <= window.availability_end):
            return TimingStatusInfo(status=TimingStatus.AVAILABLE)

        if window.availability_start and now < window.availability_start:
            diff = window.availability_start - now
            if diff <= upcoming_window:
                return TimingStatusInfo(
                    status=TimingStatus.INACTIVE,
                    next_available_time=window.availability_start,
                )
            return TimingStatusInfo(
                status=TimingStatus.HIDDEN,
                next_available_time=window.availability_start,
            )

        return TimingStatusInfo(status=TimingStatus.HIDDEN)

    @staticmethod
    def _latest_time(
        left: datetime | None, right: datetime | None
    ) -> datetime | None:
        if left is None:
            return right
        if right is None:
            return left
        return left if left >= right else right

    @staticmethod
    def _earliest_time(times: Iterable[datetime | None]) -> datetime | None:
        candidates = [value for value in times if value is not None]
        if not candidates:
            return None
        return min(candidates)
