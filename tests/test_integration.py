"""
Integration test for Drone Swarm Web System

Tests that the backend and simulation can work together.
"""

import unittest
import json
import sys
import os

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestBackendIntegration(unittest.TestCase):
    """Test backend API functionality."""

    @classmethod
    def setUpClass(cls):
        """Import backend AFTER path is set."""
        from backend.app import app
        cls.app = app
        cls.client = app.test_client()

    def test_health_check(self):
        """Test API health endpoint."""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'ok')

    def test_get_config(self):
        """Test getting configuration."""
        response = self.client.get('/api/config')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('num_drones', data)
        self.assertIn('num_threats', data)

    def test_update_config(self):
        """Test updating configuration."""
        new_config = {
            'num_drones': 10,
            'num_threats': 3,
            'duration': 120.0,
        }
        response = self.client.post(
            '/api/config',
            data=json.dumps(new_config),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

    def test_simulation_status(self):
        """Test getting simulation status."""
        response = self.client.get('/api/simulation/status')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('running', data)
        self.assertIn('params', data)


class TestSimulationIntegration(unittest.TestCase):
    """Test simulation engine integration."""

    def test_import_core_types(self):
        """Test that core types are importable."""
        from src.core.types import DroneState, Vec3, Role, Status
        drone = DroneState(id="test", position=Vec3(0, 0, 0))
        self.assertEqual(drone.id, "test")
        self.assertEqual(drone.role, Role.SCOUT)
        self.assertEqual(drone.status, Status.ACTIVE)

    def test_import_boids(self):
        """Test Boids engine import."""
        from src.intelligence.boids import BoidsEngine
        engine = BoidsEngine()
        self.assertIsNotNone(engine.params)

    def test_import_simulation(self):
        """Test simulation world import."""
        from simulation.world import SimWorld
        world = SimWorld()
        self.assertIsNotNone(world)

    def test_spawn_drones(self):
        """Test spawning drones."""
        from simulation.world import SimWorld
        world = SimWorld()
        drones = world.spawn_drones(count=5)
        self.assertEqual(len(drones), 5)
        self.assertTrue(all(d.id for d in drones))

    def test_task_planner(self):
        """Test task planner."""
        from src.intelligence.task_planner import TaskPlanner
        from src.core.types import DroneState, Vec3, Status
        
        planner = TaskPlanner()
        drones = [
            DroneState(id=f"d{i}", position=Vec3(i*10, 0, 20))
            for i in range(5)
        ]
        roles = planner.assign_roles(drones, [])
        self.assertEqual(len(roles), 5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
