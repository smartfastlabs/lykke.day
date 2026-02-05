"""Command to upsert the current user's structured profile."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.repositories import UserProfileRepositoryReadOnlyProtocol
from lykke.domain import value_objects
from lykke.domain.entities.user_profile import UserProfileEntity
from lykke.domain.value_objects.update import UserProfileUpdateObject


@dataclass(frozen=True)
class UpsertUserProfileCommand(Command):
    """Upsert the current user's profile (create if missing, else update)."""

    update_data: UserProfileUpdateObject


class UpsertUserProfileHandler(
    BaseCommandHandler[UpsertUserProfileCommand, UserProfileEntity]
):
    """Creates or updates the structured user profile."""

    user_profile_ro_repo: UserProfileRepositoryReadOnlyProtocol

    async def handle(self, command: UpsertUserProfileCommand) -> UserProfileEntity:
        user_id = self.user.id
        profile_id = UserProfileEntity.id_from_user_id(user_id)

        existing = await self.user_profile_ro_repo.search_one_or_none(
            value_objects.UserProfileQuery(limit=1)
        )
        # If the repo is empty but a row exists (rare), fall back to get-by-id
        if existing is None:
            try:
                existing = await self.user_profile_ro_repo.get(profile_id)
            except Exception:  # pylint: disable=broad-except
                existing = None

        async with self.new_uow() as uow:
            if existing is None:
                now = datetime.now(UTC)
                created = UserProfileEntity(
                    user_id=user_id,
                    preferred_name=command.update_data.preferred_name,
                    goals=list(command.update_data.goals or []),
                    work_hours=command.update_data.work_hours,
                    onboarding_completed_at=command.update_data.onboarding_completed_at,
                    created_at=now,
                    updated_at=now,
                )
                await uow.create(created)
                return created

            updated = existing.update(command.update_data)
            uow.add(updated)
            return updated

