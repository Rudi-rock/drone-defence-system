"""
Boids Engine — Bio-inspired swarm behavior.

Implements Craig Reynolds' three rules:
  1. Separation — avoid crowding neighbors
  2. Alignment — steer toward average heading of neighbors
  3. Cohesion — steer toward average position of neighbors

The biological precedent: starling murmurations and fish schooling.
Key robustness property: loss of 30% of agents causes <5% coverage degradation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.core.types import Vec3, DroneState
from src.core import constants as C


@dataclass
class BoidsParams:
    """Tunable parameters for the Boids engine.

    These are the primary targets for the adaptive feedback loop
    (Layer 5) — the RL agent adjusts these weights to optimize
    swarm behavior over time.
    """
    separation_weight: float = C.SEPARATION_WEIGHT
    alignment_weight: float = C.ALIGNMENT_WEIGHT
    cohesion_weight: float = C.COHESION_WEIGHT
    separation_radius: float = C.SEPARATION_RADIUS
    alignment_radius: float = C.ALIGNMENT_RADIUS
    cohesion_radius: float = C.COHESION_RADIUS
    max_speed: float = C.DEFAULT_MAX_SPEED
    max_force: float = C.DEFAULT_MAX_FORCE


class BoidsEngine:
    """
    Core Boids flocking engine.

    Computes steering forces for each drone based on its neighbors.
    The engine is stateless — it takes a list of DroneStates and returns
    a list of steering Vec3 forces. The caller is responsible for
    integrating these forces into velocity/position updates.
    """

    def __init__(self, params: Optional[BoidsParams] = None) -> None:
        self.params = params or BoidsParams()

    def compute_forces(self, drones: list[DroneState]) -> dict[str, Vec3]:
        """
        Compute Boids steering forces for all drones.

        Args:
            drones: Current state of every drone in the swarm.

        Returns:
            Dictionary mapping drone_id → steering force Vec3.
        """
        forces: dict[str, Vec3] = {}

        for drone in drones:
            sep = self._separation(drone, drones)
            ali = self._alignment(drone, drones)
            coh = self._cohesion(drone, drones)

            total = (
                sep * self.params.separation_weight
                + ali * self.params.alignment_weight
                + coh * self.params.cohesion_weight
            )

            # Clamp to max steering force
            total = total.clamp(self.params.max_force)
            forces[drone.id] = total

        return forces

    def _separation(self, drone: DroneState, others: list[DroneState]) -> Vec3:
        """
        Separation: steer to avoid crowding local flockmates.

        Each nearby neighbor contributes a repulsive force inversely
        proportional to distance — closer neighbors push harder.
        """
        steer = Vec3()
        count = 0

        for other in others:
            if other.id == drone.id:
                continue
            dist = drone.position.distance_to(other.position)
            if 0 < dist < self.params.separation_radius:
                # Vector pointing away from neighbor, weighted by inverse distance
                diff = drone.position - other.position
                diff = diff.normalized() / max(dist, 0.1)
                steer = steer + diff
                count += 1

        if count > 0:
            steer = steer / count
            # Implement Reynolds: steering = desired - velocity
            if steer.magnitude() > 0:
                steer = steer.normalized() * self.params.max_speed
                steer = steer - drone.velocity
                steer = steer.clamp(self.params.max_force)

        return steer

    def _alignment(self, drone: DroneState, others: list[DroneState]) -> Vec3:
        """
        Alignment: steer toward average heading of local flockmates.

        Produces synchronized movement — the swarm moves as one.
        """
        avg_velocity = Vec3()
        count = 0

        for other in others:
            if other.id == drone.id:
                continue
            dist = drone.position.distance_to(other.position)
            if 0 < dist < self.params.alignment_radius:
                avg_velocity = avg_velocity + other.velocity
                count += 1

        if count > 0:
            avg_velocity = avg_velocity / count
            avg_velocity = avg_velocity.normalized() * self.params.max_speed
            steer = avg_velocity - drone.velocity
            return steer.clamp(self.params.max_force)

        return Vec3()

    def _cohesion(self, drone: DroneState, others: list[DroneState]) -> Vec3:
        """
        Cohesion: steer toward center of mass of local flockmates.

        Keeps the swarm together — no gaps in the perimeter.
        """
        center = Vec3()
        count = 0

        for other in others:
            if other.id == drone.id:
                continue
            dist = drone.position.distance_to(other.position)
            if 0 < dist < self.params.cohesion_radius:
                center = center + other.position
                count += 1

        if count > 0:
            center = center / count
            desired = center - drone.position
            desired = desired.normalized() * self.params.max_speed
            steer = desired - drone.velocity
            return steer.clamp(self.params.max_force)

        return Vec3()

    def update_params(self, **kwargs: float) -> None:
        """
        Hot-update Boids parameters (called by feedback loop).

        This is the entry point the adaptive feedback layer uses
        to tune swarm behavior without restarting the mission.
        """
        for key, value in kwargs.items():
            if hasattr(self.params, key):
                setattr(self.params, key, value)
