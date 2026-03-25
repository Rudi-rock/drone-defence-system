# drone-defence-system

A Python simulation of a ground-based drone defence system.  The system
detects hostile unmanned aerial vehicles (UAVs) using configurable radar
installations, assesses their threat level, and dispatches interceptors to
neutralise them.

---

## Features

| Component | Description |
|-----------|-------------|
| **Drone** | Models a UAV with position, velocity, threat level, and lifecycle status |
| **Radar** | Detects and tracks drones within a configurable range; computes bearing |
| **Interceptor** | Engages and neutralises drones within its engagement envelope |
| **DroneDefenceSystem** | Orchestrator that runs the tick-based simulation, prioritises by threat, and logs every engagement |

---

## Installation

```bash
pip install -e .
```

---

## Quick Start

```python
from drone_defence import DroneDefenceSystem, Drone, Position, Velocity
from drone_defence import Radar, Interceptor

# Create the system
system = DroneDefenceSystem()
system.add_radar(Radar(Position(0, 0), range_metres=5_000, name="RADAR-1"))
system.add_interceptor(Interceptor(Position(0, 0), max_range_metres=3_000, name="INT-1"))

# Introduce a hostile drone flying at 30 m/s
drone = Drone(
    position=Position(1_000, 0, 200),
    velocity=Velocity(vx=-30, vy=0, vz=0),
)
system.add_drone(drone)

# Run for 10 ticks (2 simulated seconds each)
system.run(ticks=10, tick_seconds=2.0)

print(system.status_report())
```

---

## CLI

```
drone-defence [--ticks N] [--tick-seconds S] [--drones D] [--seed SEED] [--verbose]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--ticks` | 30 | Number of simulation ticks |
| `--tick-seconds` | 2.0 | Simulated seconds per tick |
| `--drones` | 8 | Number of hostile drones to spawn |
| `--seed` | 42 | Random seed for reproducibility |
| `--verbose` | off | Print per-tick engagement events |

Example:

```bash
drone-defence --ticks 30 --drones 10 --verbose
```

---

## Running Tests

```bash
pip install pytest
pytest
```

---

## Threat Level Model

Threat is assessed from the drone's scalar speed:

| Speed (m/s) | Threat Level |
|-------------|--------------|
| > 40        | CRITICAL     |
| > 25        | HIGH         |
| > 15        | MEDIUM       |
| > 5         | LOW          |
| ≤ 5         | UNKNOWN      |

The system always engages the highest-threat drone first.