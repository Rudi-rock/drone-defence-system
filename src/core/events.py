"""
Event Bus — Pub/Sub backbone for inter-layer communication.

Layers publish events; other layers subscribe to event types.
This decouples layers so they can be developed and tested independently.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable


# Type alias for event handlers
EventHandler = Callable[..., None]


class EventBus:
    """
    Lightweight publish/subscribe event bus.

    Usage:
        bus = EventBus()
        bus.subscribe("threat_detected", handler_fn)
        bus.publish("threat_detected", threat_vector=tv)
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self._history: list[tuple[str, dict[str, Any]]] = []
        self._max_history: int = 1000

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Register a handler for an event type."""
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Remove a handler for an event type."""
        handlers = self._subscribers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def publish(self, event_type: str, **payload: Any) -> None:
        """
        Publish an event to all subscribers.

        Args:
            event_type: The event key (e.g. "threat_detected", "drone_state_updated").
            **payload: Arbitrary keyword data passed to handlers.
        """
        # Record history
        if len(self._history) < self._max_history:
            self._history.append((event_type, payload))

        for handler in self._subscribers.get(event_type, []):
            handler(**payload)

    def clear(self) -> None:
        """Remove all subscribers and history."""
        self._subscribers.clear()
        self._history.clear()

    @property
    def history(self) -> list[tuple[str, dict[str, Any]]]:
        """Read-only access to event history (for debugging / logging)."""
        return list(self._history)


# ──────────────────────────────────────────────
# Standard Event Types
# ──────────────────────────────────────────────
# These string constants prevent typo-based bugs.

EVENTS = {
    # Perception → Intelligence
    "threat_detected": "threat_detected",
    "threat_cleared": "threat_cleared",

    # Intelligence → Communication
    "command_issued": "command_issued",
    "role_assigned": "role_assigned",

    # Communication → Action
    "directive_received": "directive_received",

    # Action → Feedback
    "telemetry_update": "telemetry_update",
    "mission_event": "mission_event",

    # Feedback → Intelligence (the loop!)
    "params_updated": "params_updated",
    "retrain_triggered": "retrain_triggered",

    # Energy (cross-cutting)
    "battery_low": "battery_low",
    "battery_critical": "battery_critical",
    "drone_docked": "drone_docked",

    # System
    "drone_state_updated": "drone_state_updated",
    "simulation_tick": "simulation_tick",
}
