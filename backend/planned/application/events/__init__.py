"""Domain event signals using blinker.

This module provides signals for domain events, allowing services
to subscribe to and react to events in a decoupled way.
"""

from .signals import domain_event_signal, send_domain_events

__all__ = [
    "domain_event_signal",
    "send_domain_events",
]
