"""
Drone Simulator — Simplified drone physics for the digital twin.

Models:
  - Position/velocity integration
  - Battery drain (speed-dependent)
  - Altitude constraints
  - Force application from Boids + collision avoidance
"""

from __future__ import annotations

import math

from src.core.types import Vec3, DroneState, Status
from src.core import constants as C


class DroneSim:
    """
    Simplified drone physics simulator.

    Each tick: apply forces → update velocity → update position → drain battery.
    """

    def __init__(
        self,
        dt: float = C.DEFAULT_DT,
        max_speed: float = C.DEFAULT_MAX_SPEED,
        drag: float = C.AIR_DRAG,
        battery_drain_rate: float = C.BATTERY_DRAIN_RATE,
    ) -> None:
        self.dt = dt
        self.max_speed = max_speed
        self.drag = drag
        self.battery_drain_rate = battery_drain_rate

    def step(
        self,
        drone: DroneState,
        force: Vec3,
        world_bounds: tuple[tuple[float, float], tuple[float, float], tuple[float, float]] | None = None,
    ) -> DroneState:
        """
        Advance a single drone by one timestep.

        Args:
            drone: Current state.
            force: Combined steering force (Boids + collision avoidance).
            world_bounds: Optional ((x_min, x_max), (y_min, y_max), (z_min, z_max)).

        Returns:
            Updated DroneState (new object, does not mutate input).
        """
        if drone.status != Status.ACTIVE:
            return drone

        # Apply force as acceleration (F = ma, assume m = 1)
        new_vel = drone.velocity + force * self.dt

        # Apply drag
        new_vel = new_vel * (1.0 - self.drag * self.dt)

        # Clamp to max speed
        new_vel = new_vel.clamp(self.max_speed)

        # Integrate position
        new_pos = drone.position + new_vel * self.dt

        # Enforce world bounds
        if world_bounds:
            (xmin, xmax), (ymin, ymax), (zmin, zmax) = world_bounds
            new_pos = Vec3(
                max(xmin, min(xmax, new_pos.x)),
                max(ymin, min(ymax, new_pos.y)),
                max(max(2.0, zmin), min(zmax, new_pos.z)),  # min altitude 2m
            )
            # Reflect velocity on boundary contact
            if new_pos.x <= xmin or new_pos.x >= xmax:
                new_vel = Vec3(-new_vel.x * 0.5, new_vel.y, new_vel.z)
            if new_pos.y <= ymin or new_pos.y >= ymax:
                new_vel = Vec3(new_vel.x, -new_vel.y * 0.5, new_vel.z)

        # Update heading from velocity
        new_heading = math.atan2(new_vel.y, new_vel.x)

        # Drain battery (proportional to speed)
        speed = new_vel.magnitude()
        drain = self.battery_drain_rate * (0.5 + 0.5 * speed / self.max_speed) * self.dt
        new_battery = max(0.0, drone.battery_pct - drain)

        # Check battery status
        new_status = drone.status
        if new_battery <= C.BATTERY_CRITICAL_THRESHOLD:
            new_status = Status.RETURNING
        elif new_battery <= 0:
            new_status = Status.OFFLINE

        return DroneState(
            id=drone.id,
            position=new_pos,
            velocity=new_vel,
            heading=new_heading,
            battery_pct=new_battery,
            role=drone.role,
            status=new_status,
        )

    def step_swarm(
        self,
        drones: list[DroneState],
        forces: dict[str, Vec3],
        world_bounds: tuple[tuple[float, float], tuple[float, float], tuple[float, float]] | None = None,
    ) -> list[DroneState]:
        """
        Advance the entire swarm by one timestep.

        Args:
            drones: List of all drone states.
            forces: Combined forces per drone_id.
            world_bounds: World boundary constraints.

        Returns:
            New list of updated DroneStates.
        """
        return [
            self.step(drone, forces.get(drone.id, Vec3()), world_bounds)
            for drone in drones
        ]
