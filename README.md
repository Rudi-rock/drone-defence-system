# Autonomous Drone Swarm Security System

A **system-of-systems architecture** for autonomous drone swarm security, modeled after biological nervous systems. Six layers flow from **perception → intelligence → communication → action → feedback**, with energy management as a cross-cutting substrate.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   DIGITAL TWIN / SIM                     │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────────┐ │
│  │  World    │  │ Drone    │  │  Adversarial Scenarios │ │
│  │  Engine   │  │ Physics  │  │  (GPS Spoof, Jamming)  │ │
│  └──────────┘  └──────────┘  └────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
        ↕                ↕                ↕
┌───────────┐  ┌──────────────┐  ┌──────────────┐
│ Perception│→ │  Swarm       │→ │Communication │
│ (CV/AI)   │  │  Intelligence│  │  Mesh        │
└───────────┘  │  (Boids)     │  └──────────────┘
               └──────────────┘          ↓
                    ↑            ┌──────────────┐
                    │            │   Action /    │
               ┌────────────┐   │   Response    │
               │  Adaptive  │←──└──────────────┘
               │  Feedback  │
               │  (RL Loop) │   ┌──────────────┐
               └────────────┘   │   Energy      │
                                │   Management  │
                                └──────────────┘
```

## Key Innovation

The **closed adaptive feedback loop** — the swarm improves its behavior every cycle via reinforcement learning. This transitions the system from a programmed machine to a **learning agent**.

## Bio-Inspiration: Boids

Uses Craig Reynolds' three rules from starling murmurations:
- **Separation** — avoid crowding neighbors
- **Alignment** — match average heading of local flockmates
- **Cohesion** — steer toward center of mass

**Robustness claim:** Loss of 30% of agents causes <5% coverage degradation. A centralized controller collapses entirely.

## Quick Start

### 🌐 Web Control Center (Recommended)

```bash
# Run with one command (Windows)
start.bat

# Or Linux/Mac
./start.sh

# Or manually with Docker
docker-compose up
```

Then open: **http://localhost:3000**

→ See [WEB_SETUP.md](WEB_SETUP.md) for full web interface documentation

### 💻 Command Line Interface

```bash
# Install dependencies
pip install -r requirements.txt

# Run the swarm simulation (with Pygame visualization)
python tools/run_sim.py --drones 5 --threats 2

# Run headless (no GUI)
python tools/run_sim.py --drones 8 --threats 3 --duration 120 --headless

# Run tests
pytest tests/ -v
```

## Project Structure

```
drone-swarm-security/
├── config/              # YAML configuration files
├── src/
│   ├── core/            # Shared types, events, constants
│   ├── intelligence/    # ★ Boids engine, task planner, path planning
│   ├── perception/      # CV/AI detection (Phase 3)
│   ├── communication/   # Mesh networking (Phase 4)
│   ├── action/          # Target tracking, formations (Phase 5)
│   ├── feedback/        # RL adaptive loop (Phase 6)
│   └── energy/          # Battery management (Phase 7)
├── simulation/          # ★ Digital twin: world, physics, visualizer
├── backend/             # ★ Flask API server + WebSocket
├── frontend/            # ★ Web dashboard (React via CDN)
├── tests/               # Unit & integration tests
├── tools/               # Simulation runner, benchmarking
├── docker-compose.yml   # ★ Container orchestration
├── start.sh / start.bat # ★ Quick start scripts
└── WEB_SETUP.md         # ★ Web interface documentation
```

★ = Fully implemented

## Build Sequencing

| Phase | Layer | Status |
|-------|-------|--------|
| 0 | **Web Control Center** | ✅ **Complete** |
| 1 | Swarm Intelligence | ✅ Complete |
| 2 | Digital Twin / Sim | ✅ Complete |
| 3 | Perception AI | 🔲 Stub |
| 4 | Communication Mesh | 🔲 Stub |
| 5 | Action / Response | 🔲 Stub |
| 6 | Adaptive Feedback | 🔲 Stub |
| 7 | Energy Management | 🔲 Stub |

## License

MIT
