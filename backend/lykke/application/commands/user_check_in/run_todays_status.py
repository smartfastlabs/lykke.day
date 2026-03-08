"""Command to run the todays_status LLM use case and persist a check-in."""

from dataclasses import dataclass

from lykke.application.commands.base import Command

from .base_llm_user_check_in_handler import BaseLLMUserCheckInHandler, StatusAssessment


@dataclass(frozen=True)
class TodaysStatusCommand(Command):
    """Command to run todays_status use case and persist an LLM-generated check-in."""


TodaysStatusAssessment = StatusAssessment


class TodaysStatusHandler(BaseLLMUserCheckInHandler[TodaysStatusCommand]):
    """Runs todays_status LLM use case and persists a UserCheckIn with source=llm_use_case, source_name=todays_status."""

    name = "todays_status"
    template_usecase = "todays_status"
    recent_checkin_window_days = 3
    recent_checkin_limit = 20
    assessment_model = TodaysStatusAssessment
