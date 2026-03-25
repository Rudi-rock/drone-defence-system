"""
Tests for the Task Planner — role assignment logic.
"""

import pytest
from src.core.types import (
    Vec3, DroneState, ThreatVector, Role, Status, ThreatLevel,
)
from src.intelligence.task_planner import TaskPlanner


def _make_drones(count: int) -> list[DroneState]:
    """Create a set of active drones."""
    return [
        DroneState(
            id=f"drone_{i:03d}",
            position=Vec3(i * 20, 0, 20),
            velocity=Vec3(1, 0, 0),
            battery_pct=100.0 - i * 5,
            role=Role.SCOUT,
            status=Status.ACTIVE,
        )
        for i in range(count)
    ]


def _make_threats(positions: list[tuple[float, float, float]]) -> list[ThreatVector]:
    """Create threat vectors at given positions."""
    return [
        ThreatVector(
            source_drone_id="sim",
            world_position=Vec3(*pos),
            classification="person",
            confidence=0.9,
            threat_level=ThreatLevel.HIGH,
        )
        for pos in positions
    ]


class TestRoleAssignment:
    def test_no_threats_all_scouts_and_relays(self):
        """Without threats, drones should be scouts (plus minimum relays)."""
        drones = _make_drones(5)
        planner = TaskPlanner(min_relays=1)

        roles = planner.assign_roles(drones, threats=[])

        assert len(roles) == 5
        relay_count = sum(1 for r in roles.values() if r == Role.RELAY)
        scout_count = sum(1 for r in roles.values() if r == Role.SCOUT)
        assert relay_count >= 1
        assert scout_count == 5 - relay_count

    def test_threats_trigger_guard_assignment(self):
        """Active threats should cause guard role assignments."""
        drones = _make_drones(5)
        threats = _make_threats([(50, 50, 0)])
        planner = TaskPlanner(min_relays=1, guard_per_threat=2)

        roles = planner.assign_roles(drones, threats)

        guard_count = sum(1 for r in roles.values() if r == Role.GUARD)
        assert guard_count >= 1  # At least some guards assigned

    def test_empty_swarm_returns_empty(self):
        """No active drones should return empty assignments."""
        planner = TaskPlanner()
        roles = planner.assign_roles([], [])
        assert roles == {}

    def test_all_offline_returns_empty(self):
        """All offline drones should return empty assignments."""
        drones = [
            DroneState(id=f"d{i}", position=Vec3(), status=Status.OFFLINE)
            for i in range(3)
        ]
        planner = TaskPlanner()
        roles = planner.assign_roles(drones, [])
        assert roles == {}

    def test_guards_assigned_nearest_to_threat(self):
        """Guards should be the drones closest to the threat."""
        drones = _make_drones(5)  # Spaced at x=0,20,40,60,80
        threats = _make_threats([(75, 0, 0)])  # Near drone_004 (x=80)
        planner = TaskPlanner(min_relays=0, guard_per_threat=1)

        roles = planner.assign_roles(drones, threats)

        guards = [did for did, r in roles.items() if r == Role.GUARD]
        # drone_004 (at x=80) should be the guard — closest to threat at x=75
        assert "drone_004" in guards


class TestPatrolWaypoints:
    def test_generates_correct_number_of_waypoints(self):
        drone = DroneState(id="test", position=Vec3(0, 0, 20))
        planner = TaskPlanner()

        waypoints = planner.get_patrol_waypoints(
            drone, ((-100, 100), (-100, 100)), num_waypoints=6
        )
        assert len(waypoints) == 6

    def test_waypoints_maintain_altitude(self):
        drone = DroneState(id="test", position=Vec3(0, 0, 25))
        planner = TaskPlanner()

        waypoints = planner.get_patrol_waypoints(
            drone, ((-100, 100), (-100, 100))
        )
        for wp in waypoints:
            assert wp.z == 25  # Should maintain drone's altitude
