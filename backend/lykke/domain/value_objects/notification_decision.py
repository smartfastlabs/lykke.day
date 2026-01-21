"""Notification decision value object from LLM evaluation."""

from dataclasses import dataclass

from .base import BaseValueObject


@dataclass(kw_only=True)
class NotificationDecision(BaseValueObject):
    """Decision from LLM about whether to send a notification.

    Returned by LLM gateway when evaluating day context.
    """

    message: str  # The notification text to send
    priority: str  # "high", "medium", "low"
    reason: str | None = None  # Why the LLM decided to notify (for debugging)
