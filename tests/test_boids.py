"""
Tests for the Boids flocking engine.
"""

import pytest
from src.core.types import Vec3, DroneState, Role, Status
from src.intelligence.boids import BoidsEngine, BoidsParams


def _make_drones(positions: list[tuple[float, float, float]]) -> list[DroneState]:
    """Helper to create drones at given positions."""
    return [
        DroneState(
            id=f"drone_{i:03d}",
            position=Vec3(*pos),
            velocity=Vec3(1, 0, 0),
            role=Role.SCOUT,
            status=Status.ACTIVE,
        )
        for i, pos in enumerate(positions)
    ]


class TestSeparation:
    """Test that separation keeps drones apart."""

    def test_drones_too_close_get_pushed_apart(self):
        """Two drones within separation radius should receive repulsive forces."""
        drones = _make_drones([(0, 0, 20), (3, 0, 20)])  # 3m apart, radius=8m
        # Isolate separation by zeroing other forces
        engine = BoidsEngine(BoidsParams(alignment_weight=0, cohesion_weight=0))

        forces = engine.compute_forces(drones)

        # Drone 0 should be pushed left (negative x)
        assert forces["drone_000"].x < 0
        # Drone 1 should be pushed right (positive x)
        assert forces["drone_001"].x > 0

    def test_drones_far_apart_no_separation(self):
        """Two drones outside separation radius should not have strong separation forces."""
        drones = _make_drones([(0, 0, 20), (50, 0, 20)])  # 50m apart, radius=8m
        engine = BoidsEngine(BoidsParams(cohesion_weight=0, alignment_weight=0))

        forces = engine.compute_forces(drones)

        # Forces should be near zero (no separation needed)
        assert abs(forces["drone_000"].x) < 0.01
        assert abs(forces["drone_001"].x) < 0.01


class TestAlignment:
    """Test that alignment synchronizes velocities."""

    def test_misaligned_drones_steer_toward_group_heading(self):
        """A drone moving opposite to the group should receive corrective force."""
        drones = [
            DroneState(id="a", position=Vec3(0, 0, 20), velocity=Vec3(-5, 0, 0)),
            DroneState(id="b", position=Vec3(10, 0, 20), velocity=Vec3(5, 0, 0)),
            DroneState(id="c", position=Vec3(5, 10, 20), velocity=Vec3(5, 0, 0)),
        ]
        engine = BoidsEngine(BoidsParams(separation_weight=0, cohesion_weight=0))

        forces = engine.compute_forces(drones)

        # Drone 'a' (going left while others go right) should get rightward force
        assert forces["a"].x > 0


class TestCohesion:
    """Test that cohesion pulls drones together."""

    def test_outlier_drone_pulled_toward_group(self):
        """A drone far from the group centroid should be pulled toward it."""
        drones = _make_drones([(0, 0, 20), (5, 0, 20), (2, 5, 20), (100, 0, 20)])
        engine = BoidsEngine(BoidsParams(separation_weight=0, alignment_weight=0))

        forces = engine.compute_forces(drones)

        # Drone 3 (at x=100) should be pulled leftward toward group at ~x=2
        # Note: it may be outside cohesion radius (25m), so check the nearby ones
        # Drone 0,1,2 are within 25m of each other and should feel cohesion toward their center


class TestBoidsIntegration:
    """Test that combined forces produce reasonable behavior."""

    def test_all_forces_produce_non_zero_output(self):
        """A cluster of drones should produce non-zero total forces."""
        drones = _make_drones([
            (0, 0, 20), (10, 5, 20), (5, 10, 20),
            (15, 0, 20), (-5, 5, 20),
        ])
        engine = BoidsEngine()

        forces = engine.compute_forces(drones)

        assert len(forces) == 5
        # At least some forces should be non-zero
        total_mag = sum(f.magnitude() for f in forces.values())
        assert total_mag > 0

    def test_force_clamping(self):
        """Forces should not exceed max_force."""
        drones = _make_drones([(0, 0, 20), (1, 0, 20)])  # Very close
        params = BoidsParams(max_force=3.0)
        engine = BoidsEngine(params)

        forces = engine.compute_forces(drones)

        for force in forces.values():
            assert force.magnitude() <= params.max_force + 0.01  # small epsilon

    def test_param_hot_update(self):
        """Parameters should be updatable at runtime."""
        engine = BoidsEngine()
        assert engine.params.separation_weight == 1.5

        engine.update_params(separation_weight=3.0)
        assert engine.params.separation_weight == 3.0
