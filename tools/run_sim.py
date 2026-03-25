"""
Simulation Runner — Main entry point for running the digital twin.

Wires together:
  - SimWorld (environment)
  - BoidsEngine (swarm intelligence)
  - CollisionAvoidance (safety)
  - TaskPlanner (role assignment)
  - DroneSim (physics)
  - SwarmVisualizer (rendering)

Usage:
    python tools/run_sim.py
    python tools/run_sim.py --drones 8 --threats 3 --duration 120 --headless
"""

from __future__ import annotations

import argparse
import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.types import Vec3, DroneState, Role
from src.core.events import EventBus
from src.intelligence.boids import BoidsEngine, BoidsParams
from src.intelligence.collision import CollisionAvoidance
from src.intelligence.task_planner import TaskPlanner
from simulation.world import SimWorld, WorldConfig
from simulation.drone_sim import DroneSim


def run_simulation(
    num_drones: int = 5,
    num_threats: int = 0,
    duration: float = 60.0,
    dt: float = 0.05,
    headless: bool = False,
    threat_spawn_interval: float = 30.0,
) -> dict:
    """
    Run a complete swarm simulation.

    Args:
        num_drones: Number of drones in the swarm.
        num_threats: Number of threat actors to spawn.
        duration: Simulation duration in seconds.
        dt: Physics timestep.
        headless: If True, skip visualization.
        threat_spawn_interval: Seconds between threat spawns.

    Returns:
        Dictionary of simulation metrics.
    """
    # ── Initialize systems ──
    event_bus = EventBus()
    boids = BoidsEngine()
    collision_avoid = CollisionAvoidance()
    task_planner = TaskPlanner(event_bus=event_bus)
    drone_sim = DroneSim(dt=dt)
    world = SimWorld()
    world.add_default_obstacles()

    # Spawn swarm
    drones = world.spawn_drones(count=num_drones)
    print(f"[SIM] Spawned {len(drones)} drones")

    # Spawn initial threats
    if num_threats > 0:
        world.spawn_threats(count=num_threats, speed=3.0)
        print(f"[SIM] Spawned {num_threats} threat(s)")

    # World bounds for physics
    wb = (
        world.config.x_bounds,
        world.config.y_bounds,
        world.config.z_bounds,
    )

    # ── Initialize visualizer ──
    visualizer = None
    if not headless:
        try:
            from simulation.visualizer import SwarmVisualizer
            visualizer = SwarmVisualizer(
                world_bounds=(world.config.x_bounds, world.config.y_bounds)
            )
            visualizer.init()
            print("[SIM] Visualizer initialized")
        except ImportError:
            print("[SIM] Pygame not available, running headless")

    # ── Metrics ──
    metrics = {
        "total_ticks": 0,
        "avg_battery": 0.0,
        "threats_spawned": num_threats,
        "coverage_estimate": 0.0,
    }

    # ── Simulation loop ──
    sim_time = 0.0
    tick = 0
    next_threat_spawn = threat_spawn_interval if threat_spawn_interval > 0 else float("inf")
    threat_budget = num_threats  # already spawned

    print(f"[SIM] Starting simulation for {duration}s (dt={dt})")
    print(f"[SIM] Press ESC or close window to stop early\n")

    try:
        while sim_time < duration:
            # 1. Assign roles based on current threats
            threat_vectors = world.threats_to_vectors()
            roles = task_planner.assign_roles(drones, threat_vectors)
            for drone in drones:
                if drone.id in roles:
                    drone = DroneState(
                        id=drone.id,
                        position=drone.position,
                        velocity=drone.velocity,
                        heading=drone.heading,
                        battery_pct=drone.battery_pct,
                        role=roles[drone.id],
                        status=drone.status,
                    )
                    # Update in list
                    for idx, d in enumerate(drones):
                        if d.id == drone.id:
                            drones[idx] = drone
                            break

            # 2. Compute Boids forces
            boids_forces = boids.compute_forces(drones)

            # 3. Compute collision avoidance forces
            avoid_forces = collision_avoid.compute_avoidance(drones, world.obstacles)

            # 4. Combine forces (collision avoidance overrides boids)
            combined_forces: dict[str, Vec3] = {}
            for drone in drones:
                bf = boids_forces.get(drone.id, Vec3())
                af = avoid_forces.get(drone.id, Vec3())
                if af.magnitude() > 0:
                    # Collision avoidance takes priority
                    combined_forces[drone.id] = af + bf * 0.3
                else:
                    combined_forces[drone.id] = bf

            # 5. Step physics
            drones = drone_sim.step_swarm(drones, combined_forces, wb)

            # 6. Update threats
            world.update_threats(dt)

            # 7. Render
            if visualizer:
                alive = visualizer.render(
                    drones, world.obstacles, world.threats, sim_time
                )
                if not alive:
                    print("\n[SIM] Window closed by user")
                    break

            # 8. Periodic status
            sim_time += dt
            tick += 1
            if tick % int(5.0 / dt) == 0:  # Every 5 sim-seconds
                avg_bat = sum(d.battery_pct for d in drones) / len(drones)
                active = sum(1 for d in drones if d.status.name == "ACTIVE")
                print(
                    f"  [t={sim_time:6.1f}s] Active: {active}/{len(drones)} | "
                    f"Avg Battery: {avg_bat:.1f}% | Threats: {len([t for t in world.threats if t.active])}"
                )

    except KeyboardInterrupt:
        print("\n[SIM] Interrupted by user")

    finally:
        if visualizer:
            visualizer.close()

    # ── Final metrics ──
    metrics["total_ticks"] = tick
    metrics["avg_battery"] = sum(d.battery_pct for d in drones) / max(len(drones), 1)
    print(f"\n[SIM] Simulation complete: {tick} ticks, {sim_time:.1f}s simulated")
    print(f"[SIM] Final avg battery: {metrics['avg_battery']:.1f}%")

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Drone Swarm Digital Twin Simulator")
    parser.add_argument("--drones", type=int, default=5, help="Number of drones")
    parser.add_argument("--threats", type=int, default=2, help="Number of threat actors")
    parser.add_argument("--duration", type=float, default=60.0, help="Duration in seconds")
    parser.add_argument("--dt", type=float, default=0.05, help="Physics timestep")
    parser.add_argument("--headless", action="store_true", help="Run without visualization")
    args = parser.parse_args()

    run_simulation(
        num_drones=args.drones,
        num_threats=args.threats,
        duration=args.duration,
        dt=args.dt,
        headless=args.headless,
    )


if __name__ == "__main__":
    main()
