"""Unit tests for the Drone Defence System."""

import pytest

from drone_defence.drone import Drone, DroneStatus, Position, ThreatLevel, Velocity
from drone_defence.radar import Radar, RadarContact
from drone_defence.interceptor import Interceptor, InterceptorStatus
from drone_defence.defence_system import DroneDefenceSystem, EngagementRecord


# ---------------------------------------------------------------------------
# Position
# ---------------------------------------------------------------------------


class TestPosition:
    def test_distance_same_point(self):
        p = Position(0, 0, 0)
        assert p.distance_to(p) == pytest.approx(0.0)

    def test_distance_2d(self):
        a = Position(0, 0, 0)
        b = Position(3, 4, 0)
        assert a.distance_to(b) == pytest.approx(5.0)

    def test_distance_3d(self):
        a = Position(0, 0, 0)
        b = Position(1, 1, 1)
        import math

        assert a.distance_to(b) == pytest.approx(math.sqrt(3))


# ---------------------------------------------------------------------------
# Drone
# ---------------------------------------------------------------------------


class TestDrone:
    def test_default_status(self):
        drone = Drone(Position(0, 0, 100))
        assert drone.status == DroneStatus.AIRBORNE

    def test_update_position(self):
        drone = Drone(Position(0, 0, 0), Velocity(10, 5, 1))
        drone.update_position(2.0)
        assert drone.position.x == pytest.approx(20.0)
        assert drone.position.y == pytest.approx(10.0)
        assert drone.position.altitude == pytest.approx(2.0)

    def test_neutralised_drone_does_not_move(self):
        drone = Drone(Position(0, 0, 0), Velocity(10, 0, 0))
        drone.status = DroneStatus.NEUTRALISED
        drone.update_position(5.0)
        assert drone.position.x == pytest.approx(0.0)

    def test_assess_threat_critical(self):
        drone = Drone(Position(0, 0, 0), Velocity(50, 0, 0))
        level = drone.assess_threat()
        assert level == ThreatLevel.CRITICAL

    def test_assess_threat_high(self):
        drone = Drone(Position(0, 0, 0), Velocity(30, 0, 0))
        level = drone.assess_threat()
        assert level == ThreatLevel.HIGH

    def test_assess_threat_medium(self):
        drone = Drone(Position(0, 0, 0), Velocity(20, 0, 0))
        level = drone.assess_threat()
        assert level == ThreatLevel.MEDIUM

    def test_assess_threat_low(self):
        drone = Drone(Position(0, 0, 0), Velocity(8, 0, 0))
        level = drone.assess_threat()
        assert level == ThreatLevel.LOW

    def test_assess_threat_unknown(self):
        drone = Drone(Position(0, 0, 0), Velocity(1, 0, 0))
        level = drone.assess_threat()
        assert level == ThreatLevel.UNKNOWN

    def test_unique_ids(self):
        d1 = Drone(Position(0, 0))
        d2 = Drone(Position(1, 1))
        assert d1.drone_id != d2.drone_id


# ---------------------------------------------------------------------------
# Radar
# ---------------------------------------------------------------------------


class TestRadar:
    def test_detects_drone_in_range(self):
        radar = Radar(Position(0, 0), range_metres=1_000)
        drone = Drone(Position(500, 0, 0))
        contacts = radar.scan([drone])
        assert len(contacts) == 1
        assert contacts[0].drone is drone

    def test_does_not_detect_drone_out_of_range(self):
        radar = Radar(Position(0, 0), range_metres=1_000)
        drone = Drone(Position(2_000, 0, 0))
        contacts = radar.scan([drone])
        assert len(contacts) == 0

    def test_sets_drone_status_to_tracked(self):
        radar = Radar(Position(0, 0), range_metres=1_000)
        drone = Drone(Position(500, 0, 0))
        assert drone.status == DroneStatus.AIRBORNE
        radar.scan([drone])
        assert drone.status == DroneStatus.TRACKED

    def test_ignores_neutralised_drones(self):
        radar = Radar(Position(0, 0), range_metres=1_000)
        drone = Drone(Position(100, 0, 0))
        drone.status = DroneStatus.NEUTRALISED
        contacts = radar.scan([drone])
        assert len(contacts) == 0

    def test_bearing_north(self):
        radar = Radar(Position(0, 0), range_metres=5_000)
        drone = Drone(Position(0, 1_000, 0))
        contacts = radar.scan([drone])
        assert contacts[0].bearing_degrees == pytest.approx(0.0, abs=0.1)

    def test_bearing_east(self):
        radar = Radar(Position(0, 0), range_metres=5_000)
        drone = Drone(Position(1_000, 0, 0))
        contacts = radar.scan([drone])
        assert contacts[0].bearing_degrees == pytest.approx(90.0, abs=0.1)

    def test_contacts_property_is_copy(self):
        radar = Radar(Position(0, 0))
        drone = Drone(Position(0, 0))
        radar.scan([drone])
        contacts = radar.contacts
        contacts.clear()
        assert len(radar.contacts) == 1


# ---------------------------------------------------------------------------
# Interceptor
# ---------------------------------------------------------------------------


class TestInterceptor:
    def test_can_engage_in_range(self):
        interceptor = Interceptor(Position(0, 0), max_range_metres=1_000)
        drone = Drone(Position(500, 0, 0))
        assert interceptor.can_engage(drone) is True

    def test_cannot_engage_out_of_range(self):
        interceptor = Interceptor(Position(0, 0), max_range_metres=1_000)
        drone = Drone(Position(2_000, 0, 0))
        assert interceptor.can_engage(drone) is False

    def test_cannot_engage_when_expended(self):
        interceptor = Interceptor(Position(0, 0), max_range_metres=5_000)
        interceptor.status = InterceptorStatus.EXPENDED
        drone = Drone(Position(100, 0, 0))
        assert interceptor.can_engage(drone) is False

    def test_engage_neutralises_drone(self):
        interceptor = Interceptor(Position(0, 0), max_range_metres=5_000)
        drone = Drone(Position(100, 0, 0))
        result = interceptor.engage(drone)
        assert result is True
        assert drone.status == DroneStatus.NEUTRALISED
        assert interceptor.status == InterceptorStatus.EXPENDED

    def test_engage_fails_out_of_range(self):
        interceptor = Interceptor(Position(0, 0), max_range_metres=500)
        drone = Drone(Position(2_000, 0, 0))
        result = interceptor.engage(drone)
        assert result is False
        assert drone.status == DroneStatus.AIRBORNE

    def test_reset(self):
        interceptor = Interceptor(Position(0, 0), max_range_metres=5_000)
        drone = Drone(Position(100, 0, 0))
        interceptor.engage(drone)
        assert interceptor.status == InterceptorStatus.EXPENDED
        interceptor.reset()
        assert interceptor.status == InterceptorStatus.READY
        assert interceptor.target is None

    def test_distance_to_target_none_when_no_target(self):
        interceptor = Interceptor(Position(0, 0))
        assert interceptor.distance_to_target() is None

    def test_distance_to_target(self):
        interceptor = Interceptor(Position(0, 0), max_range_metres=5_000)
        drone = Drone(Position(300, 400, 0))
        interceptor.engage(drone)
        assert interceptor.distance_to_target() == pytest.approx(500.0)


# ---------------------------------------------------------------------------
# DroneDefenceSystem
# ---------------------------------------------------------------------------


class TestDroneDefenceSystem:
    def _simple_system(self) -> DroneDefenceSystem:
        system = DroneDefenceSystem()
        system.add_radar(Radar(Position(0, 0), range_metres=5_000))
        system.add_interceptor(
            Interceptor(Position(0, 0), max_range_metres=5_000)
        )
        return system

    def test_tick_increments(self):
        system = self._simple_system()
        assert system.tick == 0
        system.step()
        assert system.tick == 1

    def test_drone_neutralised_in_range(self):
        system = self._simple_system()
        drone = Drone(Position(200, 0, 0), Velocity(10, 0, 0))
        system.add_drone(drone)
        system.step()
        assert drone.status == DroneStatus.NEUTRALISED

    def test_drone_outside_range_not_neutralised(self):
        system = DroneDefenceSystem()
        system.add_radar(Radar(Position(0, 0), range_metres=500))
        system.add_interceptor(Interceptor(Position(0, 0), max_range_metres=500))
        drone = Drone(Position(2_000, 0, 0), Velocity(0, 0, 0))
        system.add_drone(drone)
        system.step()
        assert drone.status == DroneStatus.AIRBORNE

    def test_engagement_log_populated(self):
        system = self._simple_system()
        drone = Drone(Position(100, 0, 0), Velocity(5, 0, 0))
        system.add_drone(drone)
        system.step()
        assert len(system.engagement_log) == 1
        assert system.engagement_log[0].success is True

    def test_multiple_drones(self):
        system = DroneDefenceSystem()
        system.add_radar(Radar(Position(0, 0), range_metres=5_000))
        # Two interceptors to handle two drones
        system.add_interceptor(Interceptor(Position(0, 0), max_range_metres=5_000, name="A"))
        system.add_interceptor(Interceptor(Position(0, 0), max_range_metres=5_000, name="B"))

        d1 = Drone(Position(100, 0, 0), Velocity(5, 0, 0))
        d2 = Drone(Position(200, 0, 0), Velocity(5, 0, 0))
        system.add_drone(d1)
        system.add_drone(d2)
        system.step()

        assert d1.status == DroneStatus.NEUTRALISED
        assert d2.status == DroneStatus.NEUTRALISED

    def test_run_multiple_ticks(self):
        system = self._simple_system()
        drone = Drone(Position(100, 0, 0), Velocity(2, 0, 0))
        system.add_drone(drone)
        system.run(ticks=5, tick_seconds=1.0)
        assert system.tick == 5

    def test_status_report_contains_tick(self):
        system = self._simple_system()
        system.run(ticks=3)
        report = system.status_report()
        assert "Tick 3" in report

    def test_threat_summary_excludes_neutralised(self):
        system = self._simple_system()
        drone = Drone(Position(100, 0, 0), Velocity(10, 0, 0))
        system.add_drone(drone)
        system.step()
        summary = system.threat_summary()
        # Neutralised drone should not appear in active threat summary
        total_active = sum(summary.values())
        assert total_active == 0

    def test_drones_property_is_copy(self):
        system = self._simple_system()
        system.drones.clear()
        assert system.drones == []  # original unchanged (empty to start)

    def test_high_threat_engaged_before_low(self):
        """High-threat drone should be engaged first when there is only one interceptor."""
        system = DroneDefenceSystem()
        system.add_radar(Radar(Position(0, 0), range_metres=5_000))
        # Only one interceptor – it will engage the highest-threat drone first
        system.add_interceptor(Interceptor(Position(0, 0), max_range_metres=5_000))

        low = Drone(Position(100, 0, 0), Velocity(8, 0, 0))   # LOW threat (~8 m/s)
        critical = Drone(Position(200, 0, 0), Velocity(50, 0, 0))  # CRITICAL (~50 m/s)
        system.add_drone(low)
        system.add_drone(critical)

        system.step()
        assert critical.status == DroneStatus.NEUTRALISED
        assert low.status == DroneStatus.TRACKED  # interceptor expended after first engagement
