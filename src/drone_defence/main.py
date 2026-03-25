"""
Command-line interface for the Drone Defence System simulation.

Usage
-----
    drone-defence [--ticks N] [--tick-seconds S] [--drones D]
"""

from __future__ import annotations

import argparse
import random
import sys

from .defence_system import DroneDefenceSystem
from .drone import Drone, Position, Velocity
from .interceptor import Interceptor
from .radar import Radar


def _build_scenario(
    num_drones: int,
    seed: int = 42,
) -> DroneDefenceSystem:
    """
    Construct a simple demo scenario with randomly placed drones.

    The defence perimeter is centred at (0, 0).  Two radar sites cover
    different quadrants and two interceptors guard the core zone.
    """
    rng = random.Random(seed)
    system = DroneDefenceSystem()

    # Two overlapping radar installations
    system.add_radar(Radar(Position(-1000, 0), range_metres=5_000, name="RADAR-NORTH"))
    system.add_radar(Radar(Position(1000, 0), range_metres=5_000, name="RADAR-SOUTH"))

    # Two interceptor batteries
    system.add_interceptor(
        Interceptor(Position(-500, 0), max_range_metres=3_000, name="INT-ALPHA")
    )
    system.add_interceptor(
        Interceptor(Position(500, 0), max_range_metres=3_000, name="INT-BETA")
    )

    # Spawn drones approaching from random directions
    for i in range(num_drones):
        angle = rng.uniform(0, 360)
        import math

        rad = math.radians(angle)
        start_x = rng.uniform(3_000, 4_500) * math.cos(rad)
        start_y = rng.uniform(3_000, 4_500) * math.sin(rad)
        alt = rng.uniform(50, 500)

        speed = rng.uniform(5, 50)
        # Head roughly towards the origin with some drift
        vx = -start_x / max(abs(start_x), 1) * speed * rng.uniform(0.8, 1.0)
        vy = -start_y / max(abs(start_y), 1) * speed * rng.uniform(0.8, 1.0)

        drone = Drone(
            position=Position(start_x, start_y, alt),
            velocity=Velocity(vx, vy, 0),
        )
        system.add_drone(drone)

    return system


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    parser = argparse.ArgumentParser(
        prog="drone-defence",
        description="Drone Defence System – simulation runner",
    )
    parser.add_argument(
        "--ticks",
        type=int,
        default=30,
        help="Number of simulation ticks to run (default: 30)",
    )
    parser.add_argument(
        "--tick-seconds",
        type=float,
        default=2.0,
        help="Simulated seconds per tick (default: 2.0)",
    )
    parser.add_argument(
        "--drones",
        type=int,
        default=8,
        help="Number of hostile drones to spawn (default: 8)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-tick engagement events",
    )
    args = parser.parse_args(argv)

    print("Initialising Drone Defence System...")
    system = _build_scenario(num_drones=args.drones, seed=args.seed)
    print(f"Scenario ready: {args.drones} drone(s), running {args.ticks} ticks.\n")

    for t in range(args.ticks):
        records = system.step(args.tick_seconds)
        if args.verbose and records:
            for rec in records:
                status = "✓ NEUTRALISED" if rec.success else "✗ MISSED"
                print(
                    f"  [Tick {rec.tick:03d}] {status} | drone={rec.drone_id} "
                    f"threat={rec.threat_level.value} via {rec.interceptor_name}"
                )

    print()
    print(system.status_report())
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
