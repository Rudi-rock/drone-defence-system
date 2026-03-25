"""
Drone Swarm Security System — Web API Backend

Flask application with WebSocket support for real-time simulation streaming.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
import threading
import json
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.run_sim import run_simulation
from src.core.types import DroneState, Status, Role
from simulation.world import SimWorld, WorldConfig

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
simulation_state = {
    "running": False,
    "thread": None,
    "metrics": None,
    "drone_data": [],
    "current_params": {
        "num_drones": 5,
        "num_threats": 2,
        "duration": 60.0,
        "dt": 0.05,
        "headless": True,
    }
}


def serialize_drone(drone: DroneState) -> dict:
    """Convert DroneState to JSON-serializable dict."""
    return {
        "id": drone.id,
        "position": {"x": drone.position.x, "y": drone.position.y, "z": drone.position.z},
        "velocity": {"x": drone.velocity.x, "y": drone.velocity.y, "z": drone.velocity.z},
        "heading": float(drone.heading),
        "battery_pct": float(drone.battery_pct),
        "role": drone.role.name,
        "status": drone.status.name,
    }


def run_sim_thread(params: dict):
    """Run simulation in a separate thread and emit updates via WebSocket."""
    try:
        socketio.emit("simulation_started", {"timestamp": datetime.now().isoformat()})

        # Initialize systems
        from src.core.events import EventBus
        from src.intelligence.boids import BoidsEngine
        from src.intelligence.collision import CollisionAvoidance
        from src.intelligence.task_planner import TaskPlanner
        from simulation.drone_sim import DroneSim

        event_bus = EventBus()
        boids = BoidsEngine()
        collision_avoid = CollisionAvoidance()
        task_planner = TaskPlanner(event_bus=event_bus)
        drone_sim = DroneSim(dt=params["dt"])
        world = SimWorld()
        world.add_default_obstacles()

        drones = world.spawn_drones(count=params["num_drones"])
        socketio.emit("drones_spawned", {
            "count": len(drones),
            "drones": [serialize_drone(d) for d in drones]
        })

        if params["num_threats"] > 0:
            world.spawn_threats(count=params["num_threats"], speed=3.0)

        wb = (
            world.config.x_bounds,
            world.config.y_bounds,
            world.config.z_bounds,
        )

        # Metrics
        metrics = {
            "total_ticks": 0,
            "avg_battery": 0.0,
            "threats_spawned": params["num_threats"],
        }

        sim_time = 0.0
        tick = 0
        duration = params["duration"]

        # Main simulation loop
        while sim_time < duration and simulation_state["running"]:
            # 1. Assign roles
            threat_vectors = world.threats_to_vectors()
            roles = task_planner.assign_roles(drones, threat_vectors)
            for drone in drones:
                if drone.id in roles:
                    idx = next(i for i, d in enumerate(drones) if d.id == drone.id)
                    drones[idx] = DroneState(
                        id=drone.id,
                        position=drone.position,
                        velocity=drone.velocity,
                        heading=drone.heading,
                        battery_pct=drone.battery_pct,
                        role=roles[drone.id],
                        status=drone.status,
                    )

            # 2. Compute forces
            boids_forces = boids.compute_forces(drones)
            avoid_forces = collision_avoid.compute_avoidance(drones, world.obstacles)

            # 3. Combine forces
            combined_forces = {}
            for drone in drones:
                bf = boids_forces.get(drone.id, __import__('src.core.types', fromlist=['Vec3']).Vec3())
                af = avoid_forces.get(drone.id, __import__('src.core.types', fromlist=['Vec3']).Vec3())
                if af.magnitude() > 0:
                    combined_forces[drone.id] = af + bf * 0.3
                else:
                    combined_forces[drone.id] = bf

            # 4. Step physics
            drones = drone_sim.step_swarm(drones, combined_forces, wb)

            # 5. Update threats
            world.update_threats(params["dt"])

            # 6. Emit updates every 5 sim-seconds or ~100 ticks
            sim_time += params["dt"]
            tick += 1

            if tick % max(1, int(5.0 / params["dt"])) == 0:
                avg_bat = sum(d.battery_pct for d in drones) / len(drones)
                active = sum(1 for d in drones if d.status == Status.ACTIVE)
                threat_count = len([t for t in world.threats if t.active])

                socketio.emit("simulation_update", {
                    "time": float(sim_time),
                    "tick": tick,
                    "drones": [serialize_drone(d) for d in drones],
                    "threats": [
                        {
                            "id": t.id,
                            "position": {"x": t.position.x, "y": t.position.y, "z": t.position.z},
                            "classification": t.classification,
                            "active": t.active,
                        }
                        for t in world.threats
                    ],
                    "stats": {
                        "active_drones": active,
                        "total_drones": len(drones),
                        "avg_battery": float(avg_bat),
                        "threats": threat_count,
                    }
                })

        # Finalize
        metrics["total_ticks"] = tick
        metrics["avg_battery"] = sum(d.battery_pct for d in drones) / max(len(drones), 1)

        socketio.emit("simulation_complete", {
            "metrics": metrics,
            "final_drones": [serialize_drone(d) for d in drones],
            "duration": float(sim_time),
        })

    except Exception as e:
        socketio.emit("simulation_error", {"error": str(e)})
    finally:
        simulation_state["running"] = False


# ──────────────────────────────────────
# HTTP Routes
# ──────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "simulation_running": simulation_state["running"],
    })


@app.route("/api/config", methods=["GET"])
def get_config():
    """Get current simulation parameters."""
    return jsonify(simulation_state["current_params"])


@app.route("/api/config", methods=["POST"])
def update_config():
    """Update simulation parameters."""
    if simulation_state["running"]:
        return jsonify({"error": "Cannot update config while simulation is running"}), 400

    data = request.json
    simulation_state["current_params"].update(data)
    return jsonify({"config": simulation_state["current_params"]})


@app.route("/api/simulation/start", methods=["POST"])
def start_simulation():
    """Start a new simulation."""
    if simulation_state["running"]:
        return jsonify({"error": "Simulation already running"}), 400

    params = request.json or simulation_state["current_params"]
    simulation_state["current_params"] = params
    simulation_state["running"] = True

    # Start simulation in background thread
    thread = threading.Thread(target=run_sim_thread, args=(params,))
    thread.daemon = True
    thread.start()
    simulation_state["thread"] = thread

    return jsonify({"status": "started", "params": params})


@app.route("/api/simulation/stop", methods=["POST"])
def stop_simulation():
    """Stop the running simulation."""
    if not simulation_state["running"]:
        return jsonify({"error": "No simulation running"}), 400

    simulation_state["running"] = False
    return jsonify({"status": "stopped"})


@app.route("/api/simulation/status", methods=["GET"])
def sim_status():
    """Get simulation status."""
    return jsonify({
        "running": simulation_state["running"],
        "params": simulation_state["current_params"],
    })


# ──────────────────────────────────────
# WebSocket Events
# ──────────────────────────────────────

@socketio.on("connect")
def handle_connect():
    """Handle client connection."""
    emit("connected", {"data": "Connected to Drone Swarm Server"})


@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnection."""
    print("Client disconnected")


@socketio.on("request_status")
def handle_status_request():
    """Send current simulation status to client."""
    emit("status", {
        "running": simulation_state["running"],
        "params": simulation_state["current_params"],
    })


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
