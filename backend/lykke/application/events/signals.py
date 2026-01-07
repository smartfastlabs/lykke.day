"""Domain event signals using blinker.

Provides a central signal for domain events that services can subscribe to.
"""

from blinker import Signal
from loguru import logger

from lykke.domain.events.base import DomainEvent

# Central signal for all domain events
# Handlers receive the event as a keyword argument
domain_event_signal: Signal = Signal("domain-event")


async def send_domain_events(events: list[DomainEvent]) -> None:
    """Dispatch domain events to all registered handlers.

    Args:
        events: List of domain events to dispatch.
    """
    if not events:
        return

    for event in events:
        event_name = event.__class__.__name__
        logger.debug(f"Dispatching event: {event_name} at {event.occurred_at}")

        # Send the event asynchronously to all connected handlers
        # Using send_async to support async handlers
        results = await domain_event_signal.send_async(
            sender=event.__class__,
            event=event,
        )

        # Log any exceptions from handlers (they're returned as (receiver, result) tuples)
        for receiver, result in results:
            if isinstance(result, Exception):
                logger.exception(
                    f"Error in event handler {receiver} for {event_name}: {result}"
                )
        logger.debug("Finished dispatch for %s", event_name)

