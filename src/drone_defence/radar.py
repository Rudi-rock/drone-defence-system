"""Radar subsystem – detects drones within a configurable range."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .drone import Drone, DroneStatus, Position


@dataclass
class RadarContact:
    """A drone contact returned by a radar scan."""

    drone: Drone
    distance: float
    bearing_degrees: float

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RadarContact(drone_id={self.drone.drone_id}, "
            f"distance={self.distance:.1f}m, bearing={self.bearing_degrees:.1f}°)"
        )


class Radar:
    """
    Models a ground-based radar unit.

    Parameters
    ----------
    position:
        Location of the radar installation.
    range_metres:
        Maximum detection range in metres (default 5 000 m).
    name:
        Human-readable identifier for this radar unit.
    """

    def __init__(
        self,
        position: Position,
        range_metres: float = 5_000.0,
        name: str = "RADAR-1",
    ) -> None:
        self.position = position
        self.range_metres = range_metres
        self.name = name
        self._contacts: List[RadarContact] = []

    @property
    def contacts(self) -> List[RadarContact]:
        """Most recent scan contacts (read-only copy)."""
        return list(self._contacts)

    def scan(self, drones: List[Drone]) -> List[RadarContact]:
        """
        Scan the airspace and return contacts for every drone within range.

        Drones that have already been neutralised are ignored.

        Parameters
        ----------
        drones:
            Full list of drones in the simulation.

        Returns
        -------
        List[RadarContact]
            Contacts detected in this scan.
        """
        contacts: List[RadarContact] = []
        for drone in drones:
            if drone.status == DroneStatus.NEUTRALISED:
                continue
            distance = self.position.distance_to(drone.position)
            if distance <= self.range_metres:
                bearing = self._bearing(drone.position)
                contact = RadarContact(
                    drone=drone,
                    distance=distance,
                    bearing_degrees=bearing,
                )
                contacts.append(contact)
                if drone.status == DroneStatus.AIRBORNE:
                    drone.status = DroneStatus.TRACKED

        self._contacts = contacts
        return contacts

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _bearing(self, target: Position) -> float:
        """
        Calculate the bearing from the radar to *target* in degrees (0–360).
        0° = North (+Y direction), clockwise positive.
        """
        import math

        dx = target.x - self.position.x
        dy = target.y - self.position.y
        angle = math.degrees(math.atan2(dx, dy)) % 360
        return angle

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"Radar(name={self.name}, range={self.range_metres}m, "
            f"contacts={len(self._contacts)})"
        )
