"""Sync-related value objects for calendar synchronization."""

from dataclasses import dataclass
from datetime import datetime

from .base import BaseValueObject


@dataclass(kw_only=True)
class SyncSubscription(BaseValueObject):
    """Platform-agnostic subscription for calendar sync notifications.

    Stores the channel/subscription information needed to receive
    notifications about calendar changes from various providers.
    """

    subscription_id: str  # Google: channel_id, Microsoft: subscription_id
    resource_id: str | None = None  # Platform's resource identifier
    expiration: datetime  # When the subscription expires
    provider: str  # "google", "microsoft", etc.
    client_state: str | None = None  # Optional validation token
    sync_token: str | None = None  # For incremental sync
    webhook_url: str | None = None  # Webhook URL for debugging purposes
