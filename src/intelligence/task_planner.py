"""
Task Planner — Dynamic role assignment for the swarm.

Assigns roles (SCOUT, GUARD, RELAY) based on:
  - Current threat landscape
  - Drone positions and battery levels
  - Communication mesh quality
  - Area coverage requirements

The planner continuously re-evaluates and can reassign roles
mid-mission as the situation evolves.
"""

from __future__ import annotations

import math
from typing import Optional

from src.core.types import (
    DroneState, ThreatVector, Role, Status, Vec3, ThreatLevel,
)
from src.core.events import EventBus, EVENTS


class TaskPlanner:
    """
    Dynamic role assignment engine.

    Strategy:
      - Minimum relay coverage: ensure mesh connectivity
      - Threat-proportional guard allocation: more threats → more guards
      - Remaining drones default to scout (maximize coverage)
    """

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        min_relays: int = 1,
        guard_per_threat: int = 2,
    ) -> None:
        self.event_bus = event_bus
        self.min_relays = min_relays
        self.guard_per_threat = guard_per_threat

    def assign_roles(
        self,
        drones: list[DroneState],
        threats: list[ThreatVector],
    ) -> dict[str, Role]:
        """
        Compute optimal role assignments for all active drones.

        Args:
            drones: Current state of every drone.
            threats: Currently active threats.

        Returns:
            Mapping of drone_id → assigned Role.
        """
        active = [d for d in drones if d.status == Status.ACTIVE]
        if not active:
            return {}

        assignments: dict[str, Role] = {}
        available = list(active)

        # Phase 1: Assign relays (communication backbone)
        relays_needed = min(self.min_relays, len(available))
        relay_candidates = self._pick_relay_candidates(available, relays_needed)
        for drone in relay_candidates:
            assignments[drone.id] = Role.RELAY
            available.remove(drone)

        # Phase 2: Assign guards (threat response)
        high_threats = [
            t for t in threats
            if t.threat_level.value >= ThreatLevel.MEDIUM.value
        ]
        guards_needed = min(
            len(high_threats) * self.guard_per_threat,
            len(available),
        )
        guard_candidates = self._pick_guard_candidates(
            available, high_threats, guards_needed
        )
        for drone in guard_candidates:
            assignments[drone.id] = Role.GUARD
            available.remove(drone)

        # Phase 3: Remaining drones are scouts
        for drone in available:
            assignments[drone.id] = Role.SCOUT

        # Publish role updates
        if self.event_bus:
            for drone_id, role in assignments.items():
                self.event_bus.publish(
                    EVENTS["role_assigned"],
                    drone_id=drone_id,
                    role=role,
                )

        return assignments

    def _pick_relay_candidates(
        self, drones: list[DroneState], count: int
    ) -> list[DroneState]:
        """
        Pick drones best suited for relay duty.

        Prefers drones with highest battery (they'll hover in place)
        and highest altitude (better line-of-sight).
        """
        scored = sorted(
            drones,
            key=lambda d: (d.battery_pct, d.position.z),
            reverse=True,
        )
        return scored[:count]

    def _pick_guard_candidates(
        self,
        drones: list[DroneState],
        threats: list[ThreatVector],
        count: int,
    ) -> list[DroneState]:
        """
        Pick drones closest to active threats for guard duty.

        Uses a greedy nearest-assignment: for each threat,
        pick the closest available drone.
        """
        if not threats or count == 0:
            return []

        candidates: list[DroneState] = []
        remaining = list(drones)

        for threat in threats:
            for _ in range(self.guard_per_threat):
                if not remaining or len(candidates) >= count:
                    break
                # Find nearest drone to this threat
                nearest = min(
                    remaining,
                    key=lambda d: d.position.distance_to(threat.world_position),
                )
                candidates.append(nearest)
                remaining.remove(nearest)

        return candidates

    def get_patrol_waypoints(
        self,
        drone: DroneState,
        patrol_bounds: tuple[tuple[float, float], tuple[float, float]],
        num_waypoints: int = 4,
    ) -> list[Vec3]:
        """
        Generate patrol waypoints for a scout drone.

        Creates a rectangular patrol pattern within bounds,
        offset by the drone's index to distribute coverage.
        """
        (x_min, x_max), (y_min, y_max) = patrol_bounds
        # Use drone ID hash to offset patrol pattern
        offset = hash(drone.id) % 360
        angle_step = 2 * math.pi / num_waypoints

        cx = (x_min + x_max) / 2
        cy = (y_min + y_max) / 2
        rx = (x_max - x_min) / 3
        ry = (y_max - y_min) / 3

        waypoints = []
        for i in range(num_waypoints):
            angle = offset + i * angle_step
            wx = cx + rx * math.cos(angle)
            wy = cy + ry * math.sin(angle)
            waypoints.append(Vec3(wx, wy, drone.position.z))

        return waypoints
