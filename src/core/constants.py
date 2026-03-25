"""
Global constants for the Autonomous Drone Swarm Security System.
"""

import math

# ──────────────────────────────────────────────
# Physics
# ──────────────────────────────────────────────
GRAVITY = 9.81                          # m/s²
DEFAULT_DT = 0.05                       # simulation timestep (s)
AIR_DRAG = 0.1                          # simplified drag coefficient

# ──────────────────────────────────────────────
# Swarm Defaults (overridden by config)
# ──────────────────────────────────────────────
DEFAULT_FLEET_SIZE = 5
DEFAULT_MAX_SPEED = 15.0                # m/s
DEFAULT_MAX_FORCE = 5.0                 # m/s²

# Boids default weights
SEPARATION_WEIGHT = 1.5
ALIGNMENT_WEIGHT = 1.0
COHESION_WEIGHT = 1.0
SEPARATION_RADIUS = 8.0                # meters
ALIGNMENT_RADIUS = 25.0
COHESION_RADIUS = 25.0

# Collision avoidance
HARD_COLLISION_RADIUS = 3.0            # meters — absolute minimum
COLLISION_AVOIDANCE_WEIGHT = 3.0

# ──────────────────────────────────────────────
# World Bounds
# ──────────────────────────────────────────────
WORLD_X_RANGE = (-200.0, 200.0)
WORLD_Y_RANGE = (-200.0, 200.0)
WORLD_Z_RANGE = (0.0, 100.0)
PATROL_X_RANGE = (-150.0, 150.0)
PATROL_Y_RANGE = (-150.0, 150.0)

# ──────────────────────────────────────────────
# Energy
# ──────────────────────────────────────────────
BATTERY_DRAIN_RATE = 0.02              # % per second at cruise
BATTERY_LOW_THRESHOLD = 25.0           # %
BATTERY_CRITICAL_THRESHOLD = 10.0      # %

# ──────────────────────────────────────────────
# Math Helpers
# ──────────────────────────────────────────────
TWO_PI = 2.0 * math.pi
