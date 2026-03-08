"""Command to run the this_weeks_status LLM use case and persist a check-in."""

from dataclasses import dataclass

from lykke.application.commands.base import Command

from .base_llm_user_check_in_handler import BaseLLMUserCheckInHandler, StatusAssessment


@dataclass(frozen=True)
class ThisWeeksStatusCommand(Command):
    """Command to run this_weeks_status use case and persist an LLM-generated check-in."""


ThisWeeksStatusAssessment = StatusAssessment


class ThisWeeksStatusHandler(BaseLLMUserCheckInHandler[ThisWeeksStatusCommand]):
    """Runs this_weeks_status LLM use case and persists a UserCheckIn with source=llm_use_case, source_name=this_weeks_status."""

    name = "this_weeks_status"
    template_usecase = "this_weeks_status"
    recent_checkin_window_days = 7
    recent_checkin_limit = 50
    assessment_model = ThisWeeksStatusAssessment
