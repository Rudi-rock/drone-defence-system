"""
World — Virtual environment for the digital twin.

Defines the simulation world: boundaries, obstacles, patrol zones,
and threat spawning. This is where all other layers are stress-tested
before touching real hardware.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from src.core.types import Vec3, DroneState, ThreatVector, Role, Status, ThreatLevel
from src.intelligence.path_planner import Obstacle


@dataclass
class ThreatActor:
    """Simulated threat moving through the environment."""
    id: str
    position: Vec3
    velocity: Vec3
    classification: str = "person"
    active: bool = True


@dataclass
class WorldConfig:
    """World configuration (mirrors sim_config.yaml)."""
    x_bounds: tuple[float, float] = (-200, 200)
    y_bounds: tuple[float, float] = (-200, 200)
    z_bounds: tuple[float, float] = (0, 100)
    patrol_x: tuple[float, float] = (-150, 150)
    patrol_y: tuple[float, float] = (-150, 150)


class SimWorld:
    """
    The virtual world for swarm simulation.

    Contains:
      - World boundaries and patrol zones
      - Static obstacles (buildings)
      - Dynamic threat actors
      - Drone spawn logic
    """

    def __init__(self, config: WorldConfig | None = None) -> None:
        self.config = config or WorldConfig()
        self.obstacles: list[Obstacle] = []
        self.threats: list[ThreatActor] = []
        self.time: float = 0.0

    def add_obstacle(
        self, position: Vec3, size: Vec3
    ) -> None:
        """Add a static obstacle (building/structure)."""
        self.obstacles.append(Obstacle(position=position, size=size))

    def add_default_obstacles(self) -> None:
        """Add the default buildings from sim_config."""
        self.add_obstacle(Vec3(30, 40, 12.5), Vec3(10, 7.5, 12.5))
        self.add_obstacle(Vec3(-50, -20, 20), Vec3(5, 15, 20))

    def spawn_drones(
        self,
        count: int = 5,
        altitude_range: tuple[float, float] = (10, 30),
    ) -> list[DroneState]:
        """Spawn drones in random positions within the patrol zone."""
        drones = []
        for i in range(count):
            pos = Vec3(
                random.uniform(*self.config.patrol_x) * 0.3,
                random.uniform(*self.config.patrol_y) * 0.3,
                random.uniform(*altitude_range),
            )
            drones.append(DroneState(
                id=f"drone_{i:03d}",
                position=pos,
                velocity=Vec3(
                    random.uniform(-2, 2),
                    random.uniform(-2, 2),
                    0,
                ),
                role=Role.SCOUT,
                status=Status.ACTIVE,
                battery_pct=100.0,
            ))
        return drones

    def spawn_threats(
        self,
        count: int = 1,
        speed: float = 3.0,
    ) -> list[ThreatActor]:
        """Spawn simulated threat actors at random edge positions."""
        new_threats = []
        for i in range(count):
            # Spawn on a random edge
            edge = random.choice(["N", "S", "E", "W"])
            px, py = self.config.patrol_x, self.config.patrol_y

            if edge == "N":
                pos = Vec3(random.uniform(*px), py[1], 0)
                vel = Vec3(random.uniform(-1, 1) * speed, -speed, 0)
            elif edge == "S":
                pos = Vec3(random.uniform(*px), py[0], 0)
                vel = Vec3(random.uniform(-1, 1) * speed, speed, 0)
            elif edge == "E":
                pos = Vec3(px[1], random.uniform(*py), 0)
                vel = Vec3(-speed, random.uniform(-1, 1) * speed, 0)
            else:
                pos = Vec3(px[0], random.uniform(*py), 0)
                vel = Vec3(speed, random.uniform(-1, 1) * speed, 0)

            threat = ThreatActor(
                id=f"threat_{len(self.threats) + i:03d}",
                position=pos,
                velocity=vel,
                classification=random.choice(["person", "vehicle"]),
            )
            new_threats.append(threat)
            self.threats.append(threat)

        return new_threats

    def update_threats(self, dt: float) -> None:
        """Advance threat positions by one timestep."""
        for threat in self.threats:
            if not threat.active:
                continue
            threat.position = threat.position + threat.velocity * dt

            # Bounce off world boundaries
            if not (self.config.x_bounds[0] < threat.position.x < self.config.x_bounds[1]):
                threat.velocity = Vec3(-threat.velocity.x, threat.velocity.y, threat.velocity.z)
            if not (self.config.y_bounds[0] < threat.position.y < self.config.y_bounds[1]):
                threat.velocity = Vec3(threat.velocity.x, -threat.velocity.y, threat.velocity.z)

    def threats_to_vectors(self) -> list[ThreatVector]:
        """Convert active ThreatActors to ThreatVector data contracts."""
        return [
            ThreatVector(
                source_drone_id="simulation",
                world_position=t.position,
                classification=t.classification,
                confidence=0.95,
                threat_level=ThreatLevel.HIGH if t.classification == "vehicle" else ThreatLevel.MEDIUM,
            )
            for t in self.threats if t.active
        ]

    def is_in_bounds(self, pos: Vec3) -> bool:
        """Check if a position is within world boundaries."""
        return (
            self.config.x_bounds[0] <= pos.x <= self.config.x_bounds[1]
            and self.config.y_bounds[0] <= pos.y <= self.config.y_bounds[1]
            and self.config.z_bounds[0] <= pos.z <= self.config.z_bounds[1]
        )
