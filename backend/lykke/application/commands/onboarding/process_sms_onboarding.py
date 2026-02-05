"""LLM-driven onboarding over SMS (multi-turn)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time as dt_time
from typing import TYPE_CHECKING
from uuid import UUID

from loguru import logger

from lykke.application.commands.base import BaseCommandHandler, Command
from lykke.application.commands.usecase_config.create_usecase_config import (
    CreateUseCaseConfigCommand,
    CreateUseCaseConfigHandler,
)
from lykke.application.commands.user.update_user import UpdateUserCommand, UpdateUserHandler
from lykke.application.commands.user_profile.upsert_user_profile import (
    UpsertUserProfileCommand,
    UpsertUserProfileHandler,
)
from lykke.application.gateways.llm_gateway_factory_protocol import (
    LLMGatewayFactoryProtocol,
)
from lykke.application.gateways.llm_protocol import LLMTool
from lykke.application.gateways.sms_provider_protocol import SMSProviderProtocol
from lykke.application.llm import LLMHandlerMixin, LLMRunResult, UseCasePromptInput
from lykke.application.llm.data_collection import (
    DataCollectionField,
    DataCollectionSchema,
    DataCollectionState,
    DataclassCoercer,
)
from lykke.application.repositories import (
    MessageRepositoryReadOnlyProtocol,
    UserProfileRepositoryReadOnlyProtocol,
)
from lykke.core.config import settings as core_settings
from lykke.core.utils.llm_snapshot import build_referenced_entities
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, MessageEntity, UserEntity
from lykke.domain.events.ai_chat_events import MessageSentEvent

if TYPE_CHECKING:
    from datetime import date as dt_date


@dataclass(frozen=True)
class ProcessSmsOnboardingCommand(Command):
    """Command to process a stored inbound SMS message as onboarding input."""

    message_id: UUID


class ProcessSmsOnboardingHandler(
    LLMHandlerMixin, BaseCommandHandler[ProcessSmsOnboardingCommand, None]
):
    """Multi-turn onboarding via SMS conversation."""

    message_ro_repo: MessageRepositoryReadOnlyProtocol
    user_profile_ro_repo: UserProfileRepositoryReadOnlyProtocol
    llm_gateway_factory: LLMGatewayFactoryProtocol
    sms_gateway: SMSProviderProtocol
    create_usecase_config_handler: CreateUseCaseConfigHandler
    update_user_handler: UpdateUserHandler
    upsert_user_profile_handler: UpsertUserProfileHandler

    name = "process_sms_onboarding"
    template_usecase = "sms_onboarding"

    _inbound_message: MessageEntity | None = None
    _state: DataCollectionState | None = None

    _schema: DataCollectionSchema[value_objects.OnboardingProfile] = DataCollectionSchema(
        dataclass_type=value_objects.OnboardingProfile,
        fields=[
            DataCollectionField(
                name="timezone",
                required=True,
                prompt="What timezone are you in? (e.g. America/Chicago)",
            ),
            DataCollectionField(
                name="preferred_name",
                required=True,
                prompt="What should I call you?",
            ),
            DataCollectionField(
                name="morning_overview_time",
                required=False,
                prompt="What time should I send your morning overview? (e.g. 08:30)",
            ),
            DataCollectionField(
                name="goals",
                required=False,
                prompt="What are a few goals you want to focus on right now?",
            ),
            DataCollectionField(
                name="work_hours",
                required=False,
                prompt="What are your typical work hours and days?",
            ),
        ],
    )

    def resolve_llm_provider(
        self, user: UserEntity
    ) -> value_objects.LLMProvider | None:
        # Prefer explicit per-user setting if present.
        provider = super().resolve_llm_provider(user)
        if provider is not None:
            return provider
        try:
            return value_objects.LLMProvider(core_settings.DEFAULT_LLM_PROVIDER)
        except ValueError:
            return value_objects.LLMProvider.ANTHROPIC

    async def handle(self, command: ProcessSmsOnboardingCommand) -> None:
        try:
            message = await self.message_ro_repo.get(command.message_id)
        except Exception:  # pylint: disable=broad-except
            logger.debug(f"Onboarding inbound message {command.message_id} not found")
            return

        if message.role != value_objects.MessageRole.USER:
            return

        from_number = message.meta.get("from_number")
        if not isinstance(from_number, str) or not from_number.strip():
            logger.debug(
                f"Skipping onboarding message {message.id}: missing from_number metadata"
            )
            return

        self._inbound_message = message
        llm_run_result = await self.run_llm()
        if llm_run_result is not None:
            await self._record_llm_run_result(message_id=message.id, result=llm_run_result)

    async def build_prompt_input(self, date: dt_date) -> UseCasePromptInput:
        if self._inbound_message is None:
            raise RuntimeError("Inbound message context was not initialized")

        state = await self._load_state()
        self._state = state

        # Minimal prompt context: we avoid GetLLMPromptContextHandler because new users
        # may not have a persisted Day yet.
        day = DayEntity(user_id=self.user.id, date=date)

        messages = await self.message_ro_repo.search(
            value_objects.MessageQuery(
                order_by="created_at", order_by_desc=True, limit=20
            )
        )
        messages = list(reversed(messages))

        prompt_context = value_objects.LLMPromptContext(
            day=day,
            tasks=[],
            routines=[],
            calendar_entries=[],
            brain_dumps=[],
            factoids=[],
            messages=messages,
            push_notifications=[],
        )

        user_profile = await self.user_profile_ro_repo.search_one_or_none(
            value_objects.UserProfileQuery(limit=1)
        )

        missing_required = state.missing_required_fields(self._schema)
        return UseCasePromptInput(
            prompt_context=prompt_context,
            extra_template_vars={
                "inbound_message": self._inbound_message,
                "onboarding_state": state.to_dict(),
                "onboarding_missing_required": missing_required,
                "user_profile": user_profile,
                "onboarding_required_fields": sorted(self._schema.required_field_names()),
                "onboarding_all_fields": sorted(self._schema.all_field_names()),
            },
        )

    def build_tools(
        self,
        *,
        current_time: datetime,
        prompt_context: value_objects.LLMPromptContext,
        llm_provider: value_objects.LLMProvider,
    ) -> list[LLMTool]:
        if self._inbound_message is None:
            raise RuntimeError("Inbound message context was not initialized")

        inbound_message = self._inbound_message
        _ = prompt_context
        _ = llm_provider

        from_number = inbound_message.meta.get("from_number")
        if not isinstance(from_number, str) or not from_number.strip():
            raise RuntimeError("Inbound message has no from_number")

        async def _send_sms(message: str) -> None:
            body = message.strip()
            if not body:
                return

            async with self.new_uow() as uow:
                outgoing = MessageEntity(
                    user_id=self.user.id,
                    role=value_objects.MessageRole.ASSISTANT,
                    type=value_objects.MessageType.SMS_OUTBOUND,
                    content=body,
                    meta={
                        "provider": "twilio",
                        "to_number": from_number,
                        "in_reply_to_message_id": str(inbound_message.id),
                    },
                    triggered_by="sms_onboarding",
                )
                outgoing.create()
                outgoing.add_event(
                    MessageSentEvent(
                        user_id=self.user.id,
                        message_id=outgoing.id,
                        role=outgoing.role.value,
                        content_preview=outgoing.get_content_preview(),
                    )
                )
                uow.add(outgoing)

            try:
                await self.sms_gateway.send_message(from_number, body)
            except Exception as exc:  # pylint: disable=broad-except
                logger.error(f"Failed sending onboarding SMS reply to {from_number}: {exc}")

        async def ask_question(message: str, field_name: str | None = None) -> None:
            """Ask the user a single onboarding question via SMS."""
            state = await self._load_state()
            if field_name:
                state = state.record_asked(field_name)
                await self._save_state(state)
            await _send_sms(message)

        async def record_fields(
            fields: dict[str, object],
            message: str | None = None,
        ) -> None:
            """Record structured onboarding fields and persist them.

            Use this whenever the user message provides answers.
            """
            raw = {k: v for k, v in fields.items()}
            coerced = DataclassCoercer.coerce_partial(
                dataclass_type=value_objects.OnboardingProfile,
                raw=raw,
                allowed_fields=self._schema.all_field_names(),
            )

            state = await self._load_state()
            state = state.merge_collected(coerced)
            await self._save_state(state)

            # Persist settings updates.
            settings_updates: dict[str, object] = {}
            if "timezone" in coerced:
                settings_updates["timezone"] = coerced.get("timezone")
            if "morning_overview_time" in coerced:
                mot = coerced.get("morning_overview_time")
                if isinstance(mot, dt_time):
                    settings_updates["morning_overview_time"] = mot.isoformat()
                else:
                    settings_updates["morning_overview_time"] = mot
            if "base_personality_slug" in coerced:
                settings_updates["base_personality_slug"] = coerced.get(
                    "base_personality_slug"
                )
            if "llm_personality_amendments" in coerced:
                settings_updates["llm_personality_amendments"] = coerced.get(
                    "llm_personality_amendments"
                )

            # Ensure an LLM provider is set so future one-shot LLM usecases can run.
            if self.user.settings and self.user.settings.llm_provider is None:
                provider = self.resolve_llm_provider(self.user)
                if provider is not None:
                    settings_updates.setdefault("llm_provider", provider.value)

            if settings_updates:
                await self.update_user_handler.handle(
                    UpdateUserCommand(
                        update_data=value_objects.UserUpdateObject(
                            settings_update=value_objects.UserSettingUpdate.from_dict(
                                settings_updates
                            )
                        )
                    )
                )

            # Persist structured profile updates.
            preferred_name_raw = coerced.get("preferred_name")
            preferred_name = (
                preferred_name_raw.strip()
                if isinstance(preferred_name_raw, str) and preferred_name_raw.strip()
                else None
            )
            goals_raw = coerced.get("goals")
            goals = goals_raw if isinstance(goals_raw, list) else None
            work_hours_raw = coerced.get("work_hours")
            work_hours = (
                work_hours_raw
                if isinstance(work_hours_raw, value_objects.WorkHours)
                else None
            )
            profile_update = value_objects.UserProfileUpdateObject(
                preferred_name=preferred_name if "preferred_name" in coerced else None,
                goals=goals if "goals" in coerced else None,
                work_hours=work_hours if "work_hours" in coerced else None,
            )
            if any(
                [
                    profile_update.preferred_name is not None,
                    profile_update.goals is not None,
                    profile_update.work_hours is not None,
                ]
            ):
                await self.upsert_user_profile_handler.handle(
                    UpsertUserProfileCommand(update_data=profile_update)
                )

            if message and message.strip():
                await _send_sms(message)

        async def complete(message: str) -> None:
            """Mark onboarding as complete and activate user."""
            now = datetime.now(UTC)
            state = await self._load_state()
            state = state.mark_completed()
            await self._save_state(state)

            await self.update_user_handler.handle(
                UpdateUserCommand(
                    update_data=value_objects.UserUpdateObject(
                        status=value_objects.UserStatus.ACTIVE
                    )
                )
            )

            await self.upsert_user_profile_handler.handle(
                UpsertUserProfileCommand(
                    update_data=value_objects.UserProfileUpdateObject(
                        onboarding_completed_at=now
                    )
                )
            )

            await _send_sms(message)

        async def abort(message: str) -> None:
            """Abort onboarding and stop asking questions."""
            state = await self._load_state()
            state = state.abort()
            await self._save_state(state)
            await _send_sms(message)

        return [
            LLMTool(callback=ask_question),
            LLMTool(callback=record_fields),
            LLMTool(callback=complete),
            LLMTool(callback=abort),
        ]

    def _build_llm_run_result_snapshot(
        self, result: LLMRunResult
    ) -> value_objects.LLMRunResultSnapshot:
        referenced_entities = build_referenced_entities(result.prompt_context)
        payload = result.request_payload or {}
        return value_objects.LLMRunResultSnapshot(
            current_time=result.current_time,
            llm_provider=result.llm_provider,
            system_prompt=result.system_prompt,
            referenced_entities=referenced_entities,
            messages=payload.get("request_messages"),
            tools=payload.get("request_tools"),
            tool_choice=payload.get("request_tool_choice"),
            model_params=payload.get("request_model_params"),
        )

    async def _record_llm_run_result(
        self, *, message_id: UUID, result: LLMRunResult
    ) -> None:
        snapshot = self._build_llm_run_result_snapshot(result)
        async with self.new_uow() as uow:
            try:
                message = await self.message_ro_repo.get(message_id)
            except Exception:  # pylint: disable=broad-except
                return
            updated = message.update_llm_run_result(snapshot)
            if updated is message:
                return
            uow.add(updated)

    async def _load_state(self) -> DataCollectionState:
        if self._state is not None:
            return self._state

        configs = await self.usecase_config_ro_repo.search(
            value_objects.UseCaseConfigQuery(usecase=self.template_usecase)
        )
        if not configs:
            state = DataCollectionState()
            self._state = state
            return state

        raw_state = configs[0].config.get("collection_state")
        if isinstance(raw_state, dict):
            state = DataCollectionState.from_dict(raw_state)
        else:
            state = DataCollectionState()
        self._state = state
        return state

    async def _save_state(self, state: DataCollectionState) -> None:
        configs = await self.usecase_config_ro_repo.search(
            value_objects.UseCaseConfigQuery(usecase=self.template_usecase)
        )
        current = configs[0].config if configs else {}
        updated = dict(current)
        updated["collection_state"] = state.to_dict()

        await self.create_usecase_config_handler.handle(
            CreateUseCaseConfigCommand(
                user=self.user,
                usecase=self.template_usecase,
                config=updated,
            )
        )
        self._state = state

