# Web Control Center Setup Guide

## Quick Start

### Option 1: Direct Python (Development)

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

Then open: http://localhost:3000

### Option 2: Docker (Production)

```bash
docker-compose up
```

Then open: http://localhost:3000

### Option 3: Manual Setup

**Terminal 1 — Backend:**
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt -r backend/requirements.txt
python backend/app.py
```

**Terminal 2 — Frontend:**
```bash
cd frontend
python -m http.server 3000
```

Then open: http://localhost:3000

## Architecture

```
┌─────────────────────────────────────────┐
│     Frontend (React via CDN)             │
│  ┌──────────────────────────────────┐  │
│  │ Dashboard                         │  │
│  │ - Configuration Panel             │  │
│  │ - Live Visualization (Canvas)     │  │
│  │ - Real-time Stats                 │  │
│  │ - Drone Fleet Status              │  │
│  │ - Message Log                     │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
           ↕ HTTP + WebSocket
┌─────────────────────────────────────────┐
│  Backend (Flask + Flask-SocketIO)       │
│  ┌──────────────────────────────────┐  │
│  │ API Routes                        │  │
│  │ - /api/health                     │  │
│  │ - /api/simulation/start           │  │
│  │ - /api/simulation/stop            │  │
│  │ - /api/config                     │  │
│  ├──────────────────────────────────┤  │
│  │ WebSocket Events                  │  │
│  │ - simulation_started              │  │
│  │ - drones_spawned                  │  │
│  │ - simulation_update (real-time)   │  │
│  │ - simulation_complete             │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
           ↕ Python API
┌─────────────────────────────────────────┐
│  Drone Swarm Simulation Engine           │
│  ┌──────────────────────────────────┐  │
│  │ Intelligence: Boids, Task Planner │  │
│  │ Physics: DroneSim                 │  │
│  │ World: Environment, Obstacles     │  │
│  │ Visualization: Pygame (headless)  │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## Features

### Configuration Panel
- **Drones**: 1-50 autonomous agents
- **Threats**: 0-10 adversaries
- **Duration**: Simulation length (10-600s)
- **Physics Timestep**: 0.01-0.1s precision

### Live Dashboard
- **Canvas Visualization**: Real-time drone/threat positions
- **Swarm Statistics**: Active drones, battery %, threat count
- **Drone Fleet List**: Individual drone status, role, battery
- **Message Log**: Event stream and diagnostics

### Real-Time Simulation
- Runs in background thread
- Streams updates via WebSocket every 5 simulated seconds
- Canvas renders drone positions, threats, mesh links
- Role-based coloring: Cyan=Scout, Red=Guard, Green=Relay

## API Endpoints

### GET /api/health
Health check and status.

```bash
curl http://localhost:5000/api/health
```

Response:
```json
{
  "status": "ok",
  "simulation_running": false
}
```

### POST /api/simulation/start
Start a new simulation with parameters.

```bash
curl -X POST http://localhost:5000/api/simulation/start \
  -H "Content-Type: application/json" \
  -d '{
    "num_drones": 5,
    "num_threats": 2,
    "duration": 60.0,
    "dt": 0.05,
    "headless": true
  }'
```

### POST /api/simulation/stop
Stop the running simulation.

```bash
curl -X POST http://localhost:5000/api/simulation/stop
```

### GET /api/config
Get current configuration.

```bash
curl http://localhost:5000/api/config
```

### POST /api/config
Update configuration (only when not running).

```bash
curl -X POST http://localhost:5000/api/config \
  -H "Content-Type: application/json" \
  -d '{"num_drones": 8, "duration": 120}'
```

## WebSocket Events

### Emitted from Backend

**simulation_started**
```json
{"timestamp": "2026-03-25T12:00:00"}
```

**drones_spawned**
```json
{
  "count": 5,
  "drones": [
    {
      "id": "drone_000",
      "position": {"x": 0, "y": 0, "z": 20},
      "velocity": {"x": 1, "y": 0, "z": 0},
      "heading": 0.5,
      "battery_pct": 100,
      "role": "SCOUT",
      "status": "ACTIVE"
    }
  ]
}
```

**simulation_update** (every 5 sim-seconds)
```json
{
  "time": 5.0,
  "tick": 100,
  "drones": [...],
  "threats": [...],
  "stats": {
    "active_drones": 5,
    "total_drones": 5,
    "avg_battery": 99.5,
    "threats": 2
  }
}
```

**simulation_complete**
```json
{
  "metrics": {
    "total_ticks": 1200,
    "avg_battery": 85.3,
    "threats_spawned": 2
  },
  "final_drones": [...],
  "duration": 60.0
}
```

### Sent to Backend

**request_status**
Request current simulation status.

## System Requirements

- Python 3.9+
- Modern web browser (Chrome, Firefox, Safari, Edge)
- 2+ GB RAM (for larger swarms)
- Network access (localhost:3000 + localhost:5000)

## Troubleshooting

### Port Already in Use

If port 3000 or 5000 is in use:

**Windows:**
```powershell
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

**Linux/Mac:**
```bash
lsof -i :3000
kill -9 <PID>
```

### WebSocket Connection Failed

- Ensure backend is running: http://localhost:5000/api/health
- Check browser console (F12) for connection errors
- Verify firewall isn't blocking localhost connections

### Simulation Crashes

- Check browser console and terminal output for error messages
- Increase timestep (dt) to 0.1 for stability
- Reduce drone count to 10-15 if memory limited

### Performance Issues

- Lower simulation timestepped (larger dt)
- Reduce drone count
- Disable browser extensions
- Close other applications

## Development

### Adding Features

1. **Backend**: Add routes/events in `backend/app.py`
2. **Frontend**: Modify JavaScript in `frontend/index.html`
3. **Restart**: Kill and rerun `start.bat` or `start.sh`

### Extending Visualization

The canvas uses 2D rendering. To add features:

```javascript
// In drawVisualization()
// Add custom drawing code here
ctx.fillStyle = "color";
ctx.fillRect(x, y, w, h);
```

### Custom Scenarios

Edit `backend/app.py` `run_sim_thread()` to inject custom logic:

```python
# After spawning drones
if some_condition:
    drones[0].position = Vec3(100, 100, 50)  # Teleport
```

## License

MIT — See [../README.md](../README.md)
