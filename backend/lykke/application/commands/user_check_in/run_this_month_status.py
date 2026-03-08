"""Command to run the this_month_status LLM use case and persist a check-in."""

from dataclasses import dataclass

from lykke.application.commands.base import Command

from .base_llm_user_check_in_handler import BaseLLMUserCheckInHandler, StatusAssessment


@dataclass(frozen=True)
class ThisMonthsStatusCommand(Command):
    """Command to run this_month_status use case and persist an LLM-generated check-in."""


ThisMonthsStatusAssessment = StatusAssessment


class ThisMonthsStatusHandler(BaseLLMUserCheckInHandler[ThisMonthsStatusCommand]):
    """Runs this_month_status LLM use case and persists a UserCheckIn with source=llm_use_case, source_name=this_month_status."""

    name = "this_month_status"
    template_usecase = "this_month_status"
    recent_checkin_window_days = 30
    recent_checkin_limit = 200
    assessment_model = ThisMonthsStatusAssessment
