"""
DroneDefenceSystem – orchestrates radar scanning, threat assessment,
and interceptor engagement across a simulation timeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .drone import Drone, DroneStatus, ThreatLevel
from .interceptor import Interceptor, InterceptorStatus
from .radar import Radar, RadarContact


@dataclass
class EngagementRecord:
    """Log entry describing a single interception event."""

    tick: int
    drone_id: str
    interceptor_name: str
    threat_level: ThreatLevel
    success: bool


class DroneDefenceSystem:
    """
    Top-level drone defence system.

    Typical usage
    -------------
    ::

        from drone_defence import DroneDefenceSystem, Drone, Position, Velocity

        system = DroneDefenceSystem()
        system.add_radar(Radar(Position(0, 0), range_metres=5000))
        system.add_interceptor(Interceptor(Position(0, 0), max_range_metres=2000))

        drone = Drone(Position(500, 500, 100), Velocity(10, 0, 0))
        system.add_drone(drone)

        system.run(ticks=10, tick_seconds=1.0)
        print(system.status_report())
    """

    def __init__(self) -> None:
        self._radars: List[Radar] = []
        self._interceptors: List[Interceptor] = []
        self._drones: List[Drone] = []
        self._engagement_log: List[EngagementRecord] = []
        self._tick: int = 0

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def add_radar(self, radar: Radar) -> None:
        """Register a radar unit with the system."""
        self._radars.append(radar)

    def add_interceptor(self, interceptor: Interceptor) -> None:
        """Register an interceptor with the system."""
        self._interceptors.append(interceptor)

    def add_drone(self, drone: Drone) -> None:
        """Inject a drone into the monitored airspace."""
        self._drones.append(drone)

    # ------------------------------------------------------------------
    # Read-only properties
    # ------------------------------------------------------------------

    @property
    def drones(self) -> List[Drone]:
        return list(self._drones)

    @property
    def radars(self) -> List[Radar]:
        return list(self._radars)

    @property
    def interceptors(self) -> List[Interceptor]:
        return list(self._interceptors)

    @property
    def engagement_log(self) -> List[EngagementRecord]:
        return list(self._engagement_log)

    @property
    def tick(self) -> int:
        return self._tick

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------

    def step(self, tick_seconds: float = 1.0) -> List[EngagementRecord]:
        """
        Advance the simulation by one tick.

        Steps performed each tick:
        1. Move all active drones.
        2. Scan with all radars.
        3. Assess threats for every tracked contact.
        4. Attempt to engage threats (highest threat first).

        Returns
        -------
        List[EngagementRecord]
            Engagement records produced in this tick.
        """
        self._tick += 1

        # 1. Move drones
        for drone in self._drones:
            drone.update_position(tick_seconds)

        # 2. Scan
        all_contacts: List[RadarContact] = []
        for radar in self._radars:
            all_contacts.extend(radar.scan(self._drones))

        # Deduplicate contacts by drone id
        seen: Dict[str, RadarContact] = {}
        for contact in all_contacts:
            seen[contact.drone.drone_id] = contact
        unique_contacts = list(seen.values())

        # 3. Assess threats
        for contact in unique_contacts:
            contact.drone.assess_threat()

        # 4. Prioritise: CRITICAL first, then by threat level descending
        threat_order = [
            ThreatLevel.CRITICAL,
            ThreatLevel.HIGH,
            ThreatLevel.MEDIUM,
            ThreatLevel.LOW,
            ThreatLevel.UNKNOWN,
        ]
        unique_contacts.sort(
            key=lambda c: threat_order.index(c.drone.threat_level)
        )

        tick_records: List[EngagementRecord] = []
        for contact in unique_contacts:
            drone = contact.drone
            if drone.status == DroneStatus.NEUTRALISED:
                continue
            record = self._attempt_engagement(drone)
            if record:
                tick_records.append(record)

        self._engagement_log.extend(tick_records)
        return tick_records

    def run(self, ticks: int = 30, tick_seconds: float = 1.0) -> None:
        """Run the simulation for *ticks* steps."""
        for _ in range(ticks):
            self.step(tick_seconds)

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def status_report(self) -> str:
        """Return a human-readable summary of the current state."""
        lines = [
            "=" * 60,
            f"  DRONE DEFENCE SYSTEM  –  Tick {self._tick}",
            "=" * 60,
            f"  Radars     : {len(self._radars)}",
            f"  Interceptors: {len(self._interceptors)}",
            f"  Total drones: {len(self._drones)}",
        ]

        status_counts: Dict[str, int] = {}
        for drone in self._drones:
            key = drone.status.value
            status_counts[key] = status_counts.get(key, 0) + 1
        for status, count in sorted(status_counts.items()):
            lines.append(f"    {status:<14}: {count}")

        lines.append(f"  Engagements : {len(self._engagement_log)}")
        successful = sum(1 for r in self._engagement_log if r.success)
        lines.append(f"    successful : {successful}")
        lines.append(f"    failed     : {len(self._engagement_log) - successful}")

        ready_interceptors = sum(
            1
            for i in self._interceptors
            if i.status == InterceptorStatus.READY
        )
        lines.append(f"  Ready interceptors: {ready_interceptors}/{len(self._interceptors)}")
        lines.append("=" * 60)
        return "\n".join(lines)

    def threat_summary(self) -> Dict[str, int]:
        """Return a count of active drones by threat level."""
        summary: Dict[str, int] = {}
        for drone in self._drones:
            if drone.status not in (DroneStatus.NEUTRALISED, DroneStatus.ESCAPED):
                key = drone.threat_level.value
                summary[key] = summary.get(key, 0) + 1
        return summary

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _attempt_engagement(self, drone: Drone) -> Optional[EngagementRecord]:
        """Try each ready interceptor until one succeeds or all fail."""
        for interceptor in self._interceptors:
            if interceptor.can_engage(drone):
                success = interceptor.engage(drone)
                record = EngagementRecord(
                    tick=self._tick,
                    drone_id=drone.drone_id,
                    interceptor_name=interceptor.name,
                    threat_level=drone.threat_level,
                    success=success,
                )
                return record
        return None
