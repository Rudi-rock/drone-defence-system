"""Interceptor subsystem – launches counter-drone measures."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import uuid

from .drone import Drone, DroneStatus, Position


class InterceptorStatus(Enum):
    """Lifecycle states of an interceptor."""

    READY = "ready"
    LAUNCHED = "launched"
    ENGAGED = "engaged"
    EXPENDED = "expended"


@dataclass
class Interceptor:
    """
    Represents a counter-drone interceptor (e.g. a jamming unit or a
    kinetic neutraliser).

    Parameters
    ----------
    position:
        Launch / base position of this interceptor.
    max_range_metres:
        Maximum engagement range in metres.
    name:
        Human-readable identifier.
    """

    position: Position
    max_range_metres: float = 2_000.0
    name: str = field(default_factory=lambda: f"INT-{str(uuid.uuid4())[:4].upper()}")
    status: InterceptorStatus = InterceptorStatus.READY
    target: Optional[Drone] = field(default=None, repr=False)

    def can_engage(self, drone: Drone) -> bool:
        """Return *True* if *drone* is within engagement range and interceptor is ready."""
        if self.status != InterceptorStatus.READY:
            return False
        distance = self.position.distance_to(drone.position)
        return distance <= self.max_range_metres

    def engage(self, drone: Drone) -> bool:
        """
        Attempt to engage (neutralise) *drone*.

        Returns *True* on success, *False* if out of range or not ready.
        The interceptor transitions to EXPENDED after a successful engagement.
        """
        if not self.can_engage(drone):
            return False

        self.status = InterceptorStatus.LAUNCHED
        self.target = drone

        # Simplified deterministic model: if in range, engagement succeeds.
        drone.status = DroneStatus.NEUTRALISED
        self.status = InterceptorStatus.EXPENDED
        return True

    def reset(self) -> None:
        """Return interceptor to READY state (reload / recycle)."""
        self.status = InterceptorStatus.READY
        self.target = None

    def distance_to_target(self) -> Optional[float]:
        """Distance to the assigned target, or *None* if no target."""
        if self.target is None:
            return None
        return self.position.distance_to(self.target.position)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"Interceptor(name={self.name}, status={self.status.value}, "
            f"range={self.max_range_metres}m)"
        )
