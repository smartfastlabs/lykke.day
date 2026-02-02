"""Command to sync calendar entries from external calendar providers."""

from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from googleapiclient.errors import HttpError
from loguru import logger

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.gateways.google_protocol import GoogleCalendarGatewayProtocol
from lykke.application.unit_of_work import (
    ReadOnlyRepositories,
    UnitOfWorkFactory,
    UnitOfWorkProtocol,
)
from lykke.core.constants import CALENDAR_DEFAULT_LOOKBACK, CALENDAR_SYNC_LOOKBACK
from lykke.core.exceptions import NotFoundError, TokenExpiredError
from lykke.domain import value_objects
from lykke.domain.entities import (
    AuthTokenEntity,
    CalendarEntity,
    CalendarEntryEntity,
    CalendarEntrySeriesEntity,
)
from lykke.domain.events.calendar_entry_series_events import (
    CalendarEntrySeriesUpdatedEvent,
)
from lykke.domain.events.calendar_events import CalendarUpdatedEvent
from lykke.domain.value_objects import CalendarUpdateObject
from lykke.domain.value_objects.update import (
    CalendarEntrySeriesUpdateObject,
    CalendarEntryUpdateObject,
)

# Max lookahead for calendar events (1 year)
MAX_EVENT_LOOKAHEAD = timedelta(days=365)


@dataclass(frozen=True)
class SyncCalendarCommand(Command):
    """Command to sync a calendar."""

    calendar_id: UUID | None = None
    calendar: CalendarEntity | None = None


class SyncCalendarHandler(BaseCommandHandler[SyncCalendarCommand, CalendarEntity]):
    """Syncs calendar entries from external provider."""

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
        google_gateway: GoogleCalendarGatewayProtocol,
    ) -> None:
        """Initialize SyncCalendarHandler.

        Args:
            ro_repos: Read-only repositories (from BaseCommandHandler)
            uow_factory: UnitOfWork factory (from BaseCommandHandler)
            user_id: User ID (from BaseCommandHandler)
            google_gateway: Google Calendar gateway
        """
        super().__init__(ro_repos, uow_factory, user_id)
        self._google_gateway = google_gateway

    async def handle(self, command: SyncCalendarCommand) -> CalendarEntity:
        """Handle sync calendar command."""
        if command.calendar:
            return await self.sync_calendar_entity(command.calendar)
        elif command.calendar_id:
            return await self.sync_calendar(command.calendar_id)
        else:
            raise ValueError("Either calendar_id or calendar must be provided")

    async def sync_calendar(self, calendar_id: UUID) -> CalendarEntity:
        """Sync a calendar by ID using a fresh unit of work."""
        uow = self.new_uow()
        async with uow:
            calendar = await uow.calendar_ro_repo.get(calendar_id)
            token = await uow.auth_token_ro_repo.get(calendar.auth_token_id)
            return await self.sync_calendar_with_uow(calendar, token, uow)

    async def sync_calendar_entity(self, calendar: CalendarEntity) -> CalendarEntity:
        """Sync a provided calendar entity using a fresh unit of work."""
        uow = self.new_uow()
        async with uow:
            token = await uow.auth_token_ro_repo.get(calendar.auth_token_id)
            return await self.sync_calendar_with_uow(calendar, token, uow)

    async def sync_calendar_with_uow(
        self,
        calendar: CalendarEntity,
        token: AuthTokenEntity,
        uow: UnitOfWorkProtocol,
    ) -> CalendarEntity:
        """Perform the sync using an existing unit of work."""
        lookback: datetime = datetime.now(UTC) - CALENDAR_DEFAULT_LOOKBACK
        if calendar.last_sync_at:
            lookback = calendar.last_sync_at - CALENDAR_SYNC_LOOKBACK

        sync_token = (
            calendar.sync_subscription.sync_token
            if calendar.sync_subscription
            else None
        )
        user = await uow.user_ro_repo.get(self.user_id)
        user_timezone = user.settings.timezone if user.settings else None

        (
            fetched_entries,
            fetched_deleted_entries,
            fetched_series,
            cancelled_series_ids,
            next_sync_token,
        ) = await self._load_calendar_events(
            calendar, lookback, sync_token, token, user_timezone=user_timezone
        )

        max_date = datetime.now(UTC) + MAX_EVENT_LOOKAHEAD
        filtered_entries = [
            entry for entry in fetched_entries if entry.starts_at <= max_date
        ]

        cancelled_platform_ids = [
            entry.platform_id
            for entry in filtered_entries
            if entry.status == "cancelled"
        ]
        entries_to_upsert = [
            entry for entry in filtered_entries if entry.status != "cancelled"
        ]
        current_time = datetime.now(UTC)

        # Classify series-level vs instance-level: multiple entries for same series
        # in this batch = series-level change (notify once); single entry or standalone = instance-level.
        entries_by_series: dict[UUID | None, list[CalendarEntryEntity]] = (
            defaultdict(list)
        )
        for entry in entries_to_upsert:
            entries_by_series[entry.calendar_entry_series_id].append(entry)
        series_level_series_ids: set[UUID] = {
            sid
            for sid, entries in entries_by_series.items()
            if sid is not None and len(entries) > 1
        }
        # One representative entry per series-level series (earliest by starts_at) gets the notification.
        representative_entry_platform_ids: set[str] = set()
        for sid in series_level_series_ids:
            group = entries_by_series[sid]
            if group:
                rep = min(group, key=lambda e: e.starts_at)
                representative_entry_platform_ids.add(rep.platform_id)

        def should_emit_entry_notification(entry: CalendarEntryEntity) -> bool:
            """Emit one notification per series-level change; per-instance for instance-level."""
            if entry.calendar_entry_series_id is None:
                return True
            if entry.calendar_entry_series_id not in series_level_series_ids:
                return True
            return entry.platform_id in representative_entry_platform_ids

        # One notification per series when deleting (used in both delete loops).
        series_delete_notification_emitted: set[UUID] = set()

        # Process series
        series_by_id: dict[UUID, CalendarEntrySeriesEntity] = {}
        series_changed_ids: set[UUID] = set()
        for series in fetched_series:
            try:
                existing_series = await uow.calendar_entry_series_ro_repo.get(series.id)
            except NotFoundError:
                series.create()
                uow.add(series)
                series_by_id[series.id] = series
                series_changed_ids.add(series.id)
            else:
                series_update_fields: dict[str, Any] = {}
                if existing_series.name != series.name:
                    series_update_fields["name"] = series.name
                if existing_series.event_category != series.event_category:
                    series_update_fields["event_category"] = series.event_category
                if existing_series.frequency != series.frequency:
                    series_update_fields["frequency"] = series.frequency
                if existing_series.recurrence != series.recurrence:
                    series_update_fields["recurrence"] = series.recurrence
                if existing_series.starts_at != series.starts_at:
                    series_update_fields["starts_at"] = series.starts_at
                if existing_series.ends_at != series.ends_at:
                    series_update_fields["ends_at"] = series.ends_at

                if series_update_fields:
                    series_update_object = CalendarEntrySeriesUpdateObject(
                        **series_update_fields
                    )
                    updated_series = existing_series.apply_update(
                        series_update_object, CalendarEntrySeriesUpdatedEvent
                    )
                    uow.add(updated_series)
                    series_by_id[series.id] = updated_series
                    series_changed_ids.add(series.id)
                else:
                    series_by_id[series.id] = existing_series

        # Preload existing entries to determine create vs update
        platform_ids_to_check = [entry.platform_id for entry in entries_to_upsert]
        existing_entries_map: dict[str, CalendarEntryEntity] = {}
        if platform_ids_to_check:
            existing_entries = await uow.calendar_entry_ro_repo.search(
                value_objects.CalendarEntryQuery(platform_ids=platform_ids_to_check)
            )
            existing_entries_map = {
                entry.platform_id: entry for entry in existing_entries
            }

        # Process entries - create new or update existing
        upsert_platform_ids_by_series: dict[UUID, set[str]] = {}
        for entry in entries_to_upsert:
            if entry.calendar_entry_series_id:
                upsert_platform_ids_by_series.setdefault(
                    entry.calendar_entry_series_id, set()
                ).add(entry.platform_id)
            existing_entry = existing_entries_map.get(entry.platform_id)
            if existing_entry is None:
                # New entry - create it
                if should_emit_entry_notification(entry):
                    entry.create()
                else:
                    entry.create_silently()
                uow.add(entry)
            else:
                # Existing entry - check if changed and update if needed
                # Build update object with changed fields
                entry_update_fields: dict[str, Any] = {}
                if existing_entry.name != entry.name:
                    entry_update_fields["name"] = entry.name
                if existing_entry.status != entry.status:
                    entry_update_fields["status"] = entry.status
                if existing_entry.starts_at != entry.starts_at:
                    entry_update_fields["starts_at"] = entry.starts_at
                if existing_entry.ends_at != entry.ends_at:
                    entry_update_fields["ends_at"] = entry.ends_at
                if existing_entry.frequency != entry.frequency:
                    entry_update_fields["frequency"] = entry.frequency
                if existing_entry.category != entry.category:
                    entry_update_fields["category"] = entry.category
                if (
                    existing_entry.calendar_entry_series_id
                    != entry.calendar_entry_series_id
                ):
                    entry_update_fields["calendar_entry_series_id"] = (
                        entry.calendar_entry_series_id
                    )

                # Only update if there are changes
                if entry_update_fields:
                    entry_update_object = CalendarEntryUpdateObject(
                        **entry_update_fields
                    )
                    if should_emit_entry_notification(entry):
                        updated_entry = existing_entry.apply_calendar_entry_update(
                            entry_update_object
                        )
                    else:
                        updated_entry = (
                            existing_entry.apply_calendar_entry_update_silently(
                                entry_update_object
                            )
                        )
                    uow.add(updated_entry)
                # If no changes, skip (entry already exists and is up to date)

        # Apply series updates to all associated entries (one notification per series when cascading).
        cascade_notification_emitted: set[UUID] = set()
        if series_changed_ids:
            for series_id in series_changed_ids:
                series_for_update = series_by_id.get(series_id)
                if series_for_update is None:
                    continue
                series_entries = await uow.calendar_entry_ro_repo.search(
                    value_objects.CalendarEntryQuery(calendar_entry_series_id=series_id)
                )
                # Sort so we have a deterministic representative (earliest by starts_at)
                series_entries_sorted = sorted(
                    series_entries, key=lambda e: (e.starts_at, e.platform_id)
                )
                for entry in series_entries_sorted:
                    cascade_update_fields: dict[str, Any] = {}
                    if entry.name != series_for_update.name:
                        cascade_update_fields["name"] = series_for_update.name
                    if entry.category != series_for_update.event_category:
                        cascade_update_fields["category"] = (
                            series_for_update.event_category
                        )
                    if entry.frequency != series_for_update.frequency:
                        cascade_update_fields["frequency"] = series_for_update.frequency

                    if cascade_update_fields:
                        cascade_update_object = CalendarEntryUpdateObject(
                            **cascade_update_fields
                        )
                        # Emit only when no entries for this series were in the batch (so we did not already emit in Process entries).
                        had_entries_in_batch = len(
                            entries_by_series.get(series_id, [])
                        ) > 0
                        emit_cascade = (
                            series_id not in cascade_notification_emitted
                            and not had_entries_in_batch
                        )
                        if emit_cascade:
                            cascade_notification_emitted.add(series_id)
                        if emit_cascade:
                            updated_entry = entry.apply_calendar_entry_update(
                                cascade_update_object
                            )
                        else:
                            updated_entry = (
                                entry.apply_calendar_entry_update_silently(
                                    cascade_update_object
                                )
                            )
                        uow.add(updated_entry)

        # Delete entries - use per-entry delete() instead of bulk delete
        # to ensure delete events are emitted
        deleted_platform_ids: set[str] = set()
        deleted_entry_ids: set[UUID] = set()
        series_ids_with_deletions: set[UUID] = set(cancelled_series_ids)
        deleted_series_ids = {
            entry.calendar_entry_series_id
            for entry in fetched_deleted_entries
            if entry.calendar_entry_series_id
        }
        series_ids_with_deletions.update(deleted_series_ids)
        platform_ids_to_delete = [
            pid
            for pid in (
                cancelled_platform_ids
                + [entry.platform_id for entry in fetched_deleted_entries]
            )
            if pid
        ]
        if platform_ids_to_delete:
            unique_platform_ids = list(dict.fromkeys(platform_ids_to_delete))
            # Fetch entries to delete so we can call delete() on them
            entries_to_delete = await uow.calendar_entry_ro_repo.search(
                value_objects.CalendarEntryQuery(platform_ids=unique_platform_ids)
            )
            deleted_platform_ids = {entry.platform_id for entry in entries_to_delete}
            deleted_entry_ids = {entry.id for entry in entries_to_delete}
            for entry in entries_to_delete:
                if entry.starts_at < current_time:
                    continue
                entry_series_id = entry.calendar_entry_series_id
                if entry_series_id is not None:
                    series_ids_with_deletions.add(entry_series_id)
                emit = entry_series_id is None or (
                    entry_series_id not in series_delete_notification_emitted
                )
                if emit and entry_series_id is not None:
                    series_delete_notification_emitted.add(entry_series_id)
                if emit:
                    entry.delete()
                else:
                    entry.delete_silently()
                uow.add(entry)

        # If an entire series was removed, delete future entries and end the series
        if series_ids_with_deletions:
            for series_id in series_ids_with_deletions:
                existing_series_entries = await uow.calendar_entry_ro_repo.search(
                    value_objects.CalendarEntryQuery(calendar_entry_series_id=series_id)
                )
                future_entries = [
                    entry
                    for entry in existing_series_entries
                    if entry.starts_at >= current_time
                    and entry.platform_id not in deleted_platform_ids
                    and entry.platform_id
                    not in upsert_platform_ids_by_series.get(series_id, set())
                ]

                # Delete any future entries for the series not already marked (one notification per series).
                for entry in future_entries:
                    if entry.id in deleted_entry_ids:
                        continue
                    emit = series_id not in series_delete_notification_emitted
                    if emit:
                        series_delete_notification_emitted.add(series_id)
                    if emit:
                        entry.delete()
                    else:
                        entry.delete_silently()
                    uow.add(entry)

                # End the series itself to avoid FK violations
                series_for_delete = series_by_id.get(series_id)
                if series_for_delete is None:
                    try:
                        series_for_delete = await uow.calendar_entry_series_ro_repo.get(
                            series_id
                        )
                    except NotFoundError:
                        series_for_delete = None
                if series_for_delete is not None:
                    series_end_update_fields: dict[str, Any] = {}
                    if series_for_delete.ends_at is None or (
                        series_for_delete.ends_at > current_time
                    ):
                        series_end_update_fields["ends_at"] = current_time
                    if series_for_delete.recurrence:
                        series_end_update_fields["recurrence"] = []

                    if series_end_update_fields:
                        series_update_object = CalendarEntrySeriesUpdateObject(
                            **series_end_update_fields
                        )
                        updated_series = series_for_delete.apply_update(
                            series_update_object, CalendarEntrySeriesUpdatedEvent
                        )
                        uow.add(updated_series)

        updated_calendar = self._apply_calendar_update(calendar, next_sync_token)
        return uow.add(updated_calendar)

    async def _load_calendar_events(
        self,
        calendar: CalendarEntity,
        lookback: datetime,
        sync_token: str | None,
        token: AuthTokenEntity,
        *,
        user_timezone: str | None,
    ) -> tuple[
        list[CalendarEntryEntity],
        list[CalendarEntryEntity],
        list[CalendarEntrySeriesEntity],
        list[UUID],
        str | None,
    ]:
        """Load events from the provider, handling sync token expiration."""
        if calendar.platform != "google":
            raise NotImplementedError(
                f"Sync not implemented for platform {calendar.platform}"
            )

        try:
            return await self._google_gateway.load_calendar_events(
                calendar=calendar,
                lookback=lookback,
                token=token,
                user_timezone=user_timezone,
                sync_token=sync_token,
            )
        except HttpError as exc:
            if exc.resp.status == 410:
                logger.info("Sync token expired, performing full sync")
                return await self._google_gateway.load_calendar_events(
                    calendar=calendar,
                    lookback=lookback,
                    token=token,
                    user_timezone=user_timezone,
                    sync_token=None,
                )
            raise

    def _apply_calendar_update(
        self, calendar: CalendarEntity, next_sync_token: str | None
    ) -> CalendarEntity:
        """Apply sync metadata updates and emit domain events."""
        updated_subscription = (
            replace(calendar.sync_subscription, sync_token=next_sync_token)
            if calendar.sync_subscription
            else None
        )
        update_data = CalendarUpdateObject(
            last_sync_at=datetime.now(UTC),
            sync_subscription=updated_subscription,
            sync_subscription_id=calendar.sync_subscription_id,
        )
        return calendar.apply_update(update_data, CalendarUpdatedEvent)


@dataclass(frozen=True)
class SyncAllCalendarsCommand(Command):
    """Command to sync all calendars (takes no args, uses handler's user_id)."""


class SyncAllCalendarsHandler(BaseCommandHandler[SyncAllCalendarsCommand, None]):
    """Syncs all calendars for a user."""

    def __init__(
        self,
        ro_repos: ReadOnlyRepositories,
        uow_factory: UnitOfWorkFactory,
        user_id: UUID,
        sync_calendar_handler: SyncCalendarHandler,
    ) -> None:
        """Initialize SyncAllCalendarsHandler.

        Args:
            ro_repos: Read-only repositories (from BaseCommandHandler)
            uow_factory: UnitOfWork factory (from BaseCommandHandler)
            user_id: User ID (from BaseCommandHandler)
            sync_calendar_handler: Handler for syncing a single calendar
        """
        super().__init__(ro_repos, uow_factory, user_id)
        self._sync_calendar_handler = sync_calendar_handler

    async def handle(self, command: SyncAllCalendarsCommand) -> None:
        """Handle sync all calendars command."""
        await self.sync_all_calendars()

    async def sync_all_calendars(self) -> None:
        """Sync all calendars for the user."""
        uow = self.new_uow()
        async with uow:
            calendars = await uow.calendar_ro_repo.all()
            for calendar in calendars:
                try:
                    token = await uow.auth_token_ro_repo.get(calendar.auth_token_id)
                    await self._sync_calendar_handler.sync_calendar_with_uow(
                        calendar, token, uow
                    )
                except TokenExpiredError:
                    logger.info(f"Token expired for calendar {calendar.name}")
                except Exception as e:  # pylint: disable=broad-except
                    logger.exception(f"Error syncing calendar {calendar.name}: {e}")
                    await uow.rollback()
