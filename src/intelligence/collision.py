"""
Collision Avoidance — Emergency obstacle and drone avoidance.

This is a higher-priority layer than Boids. When drones are within
the hard collision radius, this module overrides Boids forces with
strong repulsive steering to prevent physical collisions.

Also handles static obstacle avoidance (buildings, terrain, no-fly zones).
"""

from __future__ import annotations

from src.core.types import Vec3, DroneState
from src.core import constants as C
from .path_planner import Obstacle


class CollisionAvoidance:
    """
    Emergency collision avoidance system.

    Generates override forces when drones or obstacles are within
    the hard collision radius. These forces take priority over
    Boids steering.
    """

    def __init__(
        self,
        hard_radius: float = C.HARD_COLLISION_RADIUS,
        avoidance_weight: float = C.COLLISION_AVOIDANCE_WEIGHT,
        max_speed: float = C.DEFAULT_MAX_SPEED,
        max_force: float = C.DEFAULT_MAX_FORCE,
    ) -> None:
        self.hard_radius = hard_radius
        self.avoidance_weight = avoidance_weight
        self.max_speed = max_speed
        self.max_force = max_force

    def compute_avoidance(
        self,
        drones: list[DroneState],
        obstacles: list[Obstacle] | None = None,
    ) -> dict[str, Vec3]:
        """
        Compute collision avoidance forces for all drones.

        Returns forces only for drones that are in danger.
        If a drone is not within hard_radius of anything,
        it won't appear in the result dict.

        Args:
            drones: All drones in the swarm.
            obstacles: Static obstacles in the environment.

        Returns:
            dict of drone_id → avoidance force (only for endangered drones).
        """
        forces: dict[str, Vec3] = {}

        for drone in drones:
            force = Vec3()

            # Drone-to-drone avoidance
            for other in drones:
                if other.id == drone.id:
                    continue
                dist = drone.position.distance_to(other.position)
                if 0 < dist < self.hard_radius:
                    # Strong repulsive force — inversely proportional to distance²
                    away = drone.position - other.position
                    strength = self.avoidance_weight * (
                        (self.hard_radius - dist) / self.hard_radius
                    ) ** 2
                    force = force + away.normalized() * strength * self.max_speed

            # Drone-to-obstacle avoidance
            if obstacles:
                for obs in obstacles:
                    dist = obs.distance_to(drone.position)
                    if dist < self.hard_radius:
                        away = drone.position - obs.position
                        strength = self.avoidance_weight * (
                            (self.hard_radius - dist) / max(self.hard_radius, 0.01)
                        ) ** 2
                        force = force + away.normalized() * strength * self.max_speed

            # Ground avoidance (don't fly below 2m)
            if drone.position.z < 2.0:
                upforce = (2.0 - drone.position.z) * self.avoidance_weight
                force = force + Vec3(0, 0, upforce * self.max_speed)

            if force.magnitude() > 0:
                force = force.clamp(self.max_force * self.avoidance_weight)
                forces[drone.id] = force

        return forces

    def is_collision_imminent(
        self, drone: DroneState, others: list[DroneState]
    ) -> bool:
        """Check if any drone is within hard collision radius."""
        for other in others:
            if other.id == drone.id:
                continue
            if drone.position.distance_to(other.position) < self.hard_radius:
                return True
        return False
