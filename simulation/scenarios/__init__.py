"""
Adversarial Scenarios — Stress-test the swarm in the digital twin.

These scenarios are critical for validating robustness before real deployment.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable

from src.core.types import DroneState, Vec3, Status


@dataclass
class ScenarioResult:
    """Result of running an adversarial scenario."""
    name: str
    passed: bool
    metric_name: str
    metric_value: float
    threshold: float
    details: str = ""


# ──────────────────────────────────────────────
# Scenario: Node Loss (30% drone failure)
# ──────────────────────────────────────────────

def apply_node_loss(
    drones: list[DroneState],
    loss_pct: float = 0.3,
) -> list[DroneState]:
    """
    Simulate sudden loss of a percentage of drones.

    Sets their status to OFFLINE and zeros velocity.
    Validates the Boids robustness claim: <5% coverage loss at 30% attrition.
    """
    num_to_kill = int(len(drones) * loss_pct)
    victims = random.sample(range(len(drones)), num_to_kill)

    result = []
    for i, drone in enumerate(drones):
        if i in victims:
            result.append(DroneState(
                id=drone.id,
                position=drone.position,
                velocity=Vec3(0, 0, 0),
                heading=drone.heading,
                battery_pct=0.0,
                role=drone.role,
                status=Status.OFFLINE,
            ))
        else:
            result.append(drone)

    return result


def evaluate_node_loss(
    drones_before: list[DroneState],
    drones_after: list[DroneState],
    coverage_before: float,
    coverage_after: float,
) -> ScenarioResult:
    """Evaluate whether swarm maintained coverage after node loss."""
    degradation = 1.0 - (coverage_after / max(coverage_before, 0.01))
    threshold = 0.05  # <5% degradation

    return ScenarioResult(
        name="Node Loss (30%)",
        passed=degradation < threshold,
        metric_name="Coverage Degradation",
        metric_value=degradation,
        threshold=threshold,
        details=(
            f"Active before: {sum(1 for d in drones_before if d.status == Status.ACTIVE)}, "
            f"Active after: {sum(1 for d in drones_after if d.status == Status.ACTIVE)}, "
            f"Coverage change: {coverage_before:.2f} → {coverage_after:.2f}"
        ),
    )


# ──────────────────────────────────────────────
# Scenario: GPS Spoofing
# ──────────────────────────────────────────────

def apply_gps_spoofing(
    drones: list[DroneState],
    target_indices: list[int] | None = None,
    offset: Vec3 | None = None,
) -> list[DroneState]:
    """
    Inject false GPS data into selected drones.

    Shifts their reported position by a large offset,
    simulating a spoofing attack. The swarm should detect
    and reject outlier positions.
    """
    if offset is None:
        offset = Vec3(500, 500, 0)  # Huge offset = obvious spoof

    if target_indices is None:
        # Spoof 1-2 drones randomly
        count = min(2, len(drones))
        target_indices = random.sample(range(len(drones)), count)

    result = []
    for i, drone in enumerate(drones):
        if i in target_indices:
            spoofed_pos = drone.position + offset
            result.append(DroneState(
                id=drone.id,
                position=spoofed_pos,
                velocity=drone.velocity,
                heading=drone.heading,
                battery_pct=drone.battery_pct,
                role=drone.role,
                status=drone.status,
            ))
        else:
            result.append(drone)

    return result


def detect_gps_spoof(
    drones: list[DroneState],
    max_neighbor_distance: float = 100.0,
) -> list[str]:
    """
    Simple GPS spoof detection: flag any drone whose position
    is far from ALL other drones (outlier detection).

    Returns list of drone IDs suspected of spoofing.
    """
    suspects = []
    for drone in drones:
        if drone.status != Status.ACTIVE:
            continue
        others = [d for d in drones if d.id != drone.id and d.status == Status.ACTIVE]
        if not others:
            continue
        min_dist = min(drone.position.distance_to(d.position) for d in others)
        if min_dist > max_neighbor_distance:
            suspects.append(drone.id)
    return suspects


# ──────────────────────────────────────────────
# Scenario: Communication Jamming
# ──────────────────────────────────────────────

def simulate_comm_jamming(
    drones: list[DroneState],
    jam_probability: float = 0.3,
) -> dict[str, float]:
    """
    Simulate communication quality degradation.

    Returns a dict of drone_id → network_quality (0.0 = fully jammed, 1.0 = perfect).
    Drones with quality < 0.3 should fall back to autonomous behavior.
    """
    quality: dict[str, float] = {}
    for drone in drones:
        if random.random() < jam_probability:
            quality[drone.id] = random.uniform(0.0, 0.3)  # Jammed
        else:
            quality[drone.id] = random.uniform(0.7, 1.0)  # Normal
    return quality
