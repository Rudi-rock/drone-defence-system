"""Drone model – represents a hostile (or unknown) unmanned aerial vehicle."""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from enum import Enum


class ThreatLevel(Enum):
    """Assessed threat posed by a drone."""

    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DroneStatus(Enum):
    """Current operational status of a drone."""

    AIRBORNE = "airborne"
    TRACKED = "tracked"
    INTERCEPTED = "intercepted"
    NEUTRALISED = "neutralised"
    ESCAPED = "escaped"


@dataclass
class Position:
    """Three-dimensional position in metres relative to the defence origin."""

    x: float
    y: float
    altitude: float = 0.0

    def distance_to(self, other: "Position") -> float:
        """Euclidean distance between two positions."""
        return math.sqrt(
            (self.x - other.x) ** 2
            + (self.y - other.y) ** 2
            + (self.altitude - other.altitude) ** 2
        )

    def __repr__(self) -> str:  # pragma: no cover
        return f"Position(x={self.x:.1f}, y={self.y:.1f}, alt={self.altitude:.1f})"


@dataclass
class Velocity:
    """Velocity vector in metres per second."""

    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0

    @property
    def speed(self) -> float:
        """Scalar speed in m/s."""
        return math.sqrt(self.vx**2 + self.vy**2 + self.vz**2)


@dataclass
class Drone:
    """
    Represents a drone operating in the monitored airspace.

    Parameters
    ----------
    position:
        Current position of the drone.
    velocity:
        Current velocity of the drone.
    threat_level:
        Assessed threat level.
    drone_id:
        Unique identifier (auto-generated if not supplied).
    """

    position: Position
    velocity: Velocity = field(default_factory=Velocity)
    threat_level: ThreatLevel = ThreatLevel.UNKNOWN
    status: DroneStatus = DroneStatus.AIRBORNE
    drone_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def update_position(self, elapsed_seconds: float) -> None:
        """Advance the drone's position by *elapsed_seconds* of flight."""
        if self.status in (DroneStatus.NEUTRALISED, DroneStatus.INTERCEPTED):
            return
        self.position.x += self.velocity.vx * elapsed_seconds
        self.position.y += self.velocity.vy * elapsed_seconds
        self.position.altitude += self.velocity.vz * elapsed_seconds

    def assess_threat(self) -> ThreatLevel:
        """
        Re-assess threat level based on speed and altitude.

        Rules (simplified model):
        - Speed > 40 m/s  → CRITICAL
        - Speed > 25 m/s  → HIGH
        - Speed > 15 m/s  → MEDIUM
        - Speed > 5 m/s   → LOW
        - Otherwise       → UNKNOWN
        """
        speed = self.velocity.speed
        if speed > 40:
            self.threat_level = ThreatLevel.CRITICAL
        elif speed > 25:
            self.threat_level = ThreatLevel.HIGH
        elif speed > 15:
            self.threat_level = ThreatLevel.MEDIUM
        elif speed > 5:
            self.threat_level = ThreatLevel.LOW
        else:
            self.threat_level = ThreatLevel.UNKNOWN
        return self.threat_level

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"Drone(id={self.drone_id}, status={self.status.value}, "
            f"threat={self.threat_level.value}, pos={self.position})"
        )
