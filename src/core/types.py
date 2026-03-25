"""
Autonomous Drone Swarm Security System — Core Types

Typed data contracts for inter-layer communication.
Every layer communicates exclusively through these structures.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


# ──────────────────────────────────────────────
# Enumerations
# ──────────────────────────────────────────────

class Role(Enum):
    """Drone operational role within the swarm."""
    SCOUT = auto()   # Patrol and detect
    GUARD = auto()   # Engage / escort targets
    RELAY = auto()   # Maintain communication mesh


class Status(Enum):
    """Drone operational status."""
    ACTIVE = auto()
    RETURNING = auto()
    DOCKED = auto()
    OFFLINE = auto()


class ActionType(Enum):
    """High-level action commands issued by the intelligence layer."""
    PATROL = auto()
    TRACK = auto()
    ESCORT = auto()
    ENCIRCLE = auto()
    RETURN = auto()
    HOLD = auto()


class ThreatLevel(Enum):
    """Classified threat severity."""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


# ──────────────────────────────────────────────
# Geometric Primitives
# ──────────────────────────────────────────────

@dataclass
class Vec3:
    """3D vector / point."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, other: Vec3) -> Vec3:
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Vec3) -> Vec3:
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> Vec3:
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float) -> Vec3:
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> Vec3:
        return Vec3(self.x / scalar, self.y / scalar, self.z / scalar)

    def magnitude(self) -> float:
        return (self.x ** 2 + self.y ** 2 + self.z ** 2) ** 0.5

    def normalized(self) -> Vec3:
        mag = self.magnitude()
        if mag < 1e-8:
            return Vec3(0, 0, 0)
        return self / mag

    def distance_to(self, other: Vec3) -> float:
        return (self - other).magnitude()

    def clamp(self, max_magnitude: float) -> Vec3:
        mag = self.magnitude()
        if mag > max_magnitude and mag > 1e-8:
            return self.normalized() * max_magnitude
        return Vec3(self.x, self.y, self.z)

    def to_tuple(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)


@dataclass
class BBox:
    """Bounding box in image / world space."""
    x_min: float
    y_min: float
    x_max: float
    y_max: float


# ──────────────────────────────────────────────
# Layer Data Contracts
# ──────────────────────────────────────────────

@dataclass
class DroneState:
    """Complete state snapshot for a single drone."""
    id: str
    position: Vec3 = field(default_factory=Vec3)
    velocity: Vec3 = field(default_factory=Vec3)
    heading: float = 0.0              # radians
    battery_pct: float = 100.0
    role: Role = Role.SCOUT
    status: Status = Status.ACTIVE


@dataclass
class ThreatVector:
    """A detected threat from the perception layer."""
    source_drone_id: str
    timestamp: float = field(default_factory=time.time)
    bbox: Optional[BBox] = None
    world_position: Vec3 = field(default_factory=Vec3)
    classification: str = "unknown"
    confidence: float = 0.0
    threat_level: ThreatLevel = ThreatLevel.NONE


@dataclass
class SwarmCommand:
    """Command issued from intelligence → communication → action."""
    target_drones: list[str] = field(default_factory=list)
    action: ActionType = ActionType.PATROL
    waypoints: list[Vec3] = field(default_factory=list)
    priority: int = 0
    ttl: float = 30.0                 # seconds


@dataclass
class Telemetry:
    """Feedback data flowing from action → feedback layer."""
    drone_id: str = ""
    timestamp: float = field(default_factory=time.time)
    state: Optional[DroneState] = None
    detections: list[ThreatVector] = field(default_factory=list)
    network_quality: float = 1.0      # 0.0 – 1.0
    mission_metrics: dict = field(default_factory=dict)
