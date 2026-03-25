# 🚀 API Reference — Drone Swarm Web Backend

Flask REST API with WebSocket support for real-time simulation streaming.

## Base URL

**Development:**
```
http://localhost:5000
```

**Production (Docker):**
```
http://backend:5000
```

---

## HTTP Endpoints

### 1. GET `/api/health`

Health check and server status.

**Response (200 OK):**
```json
{
  "status": "ok",
  "simulation_running": false
}
```

**Example:**
```bash
curl http://localhost:5000/api/health
```

---

### 2. GET `/api/config`

Retrieve current simulation parameters.

**Response (200 OK):**
```json
{
  "num_drones": 5,
  "num_threats": 2,
  "duration": 60.0,
  "dt": 0.05,
  "headless": true
}
```

**Example:**
```bash
curl http://localhost:5000/api/config
```

---

### 3. POST `/api/config`

Update simulation parameters. **Cannot be called while simulation is running.**

**Request Body (JSON):**
```json
{
  "num_drones": 8,
  "num_threats": 3,
  "duration": 120.0,
  "dt": 0.05
}
```

**Response (200 OK):**
```json
{
  "config": {
    "num_drones": 8,
    "num_threats": 3,
    "duration": 120.0,
    "dt": 0.05,
    "headless": true
  }
}
```

**Error (400 Bad Request):**
```json
{
  "error": "Cannot update config while simulation is running"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/config \
  -H "Content-Type: application/json" \
  -d '{"num_drones": 8, "duration": 120}'
```

---

### 4. GET `/api/simulation/status`

Get current simulation status without blocking.

**Response (200 OK):**
```json
{
  "running": false,
  "params": {
    "num_drones": 5,
    "num_threats": 2,
    "duration": 60.0,
    "dt": 0.05,
    "headless": true
  }
}
```

**Example:**
```bash
curl http://localhost:5000/api/simulation/status
```

---

### 5. POST `/api/simulation/start`

Start a new simulation with optional parameters.

**Request Body (JSON, Optional):**
```json
{
  "num_drones": 5,
  "num_threats": 2,
  "duration": 60.0,
  "dt": 0.05,
  "headless": true
}
```

If no body provided, uses current config from `/api/config`.

**Response (200 OK):**
```json
{
  "status": "started",
  "params": {
    "num_drones": 5,
    "num_threats": 2,
    "duration": 60.0,
    "dt": 0.05,
    "headless": true
  }
}
```

**Error (400 Bad Request):**
```json
{
  "error": "Simulation already running"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/simulation/start \
  -H "Content-Type: application/json" \
  -d '{
    "num_drones": 5,
    "num_threats": 2,
    "duration": 60.0,
    "dt": 0.05
  }'
```

---

### 6. POST `/api/simulation/stop`

Stop the currently running simulation.

**Response (200 OK):**
```json
{
  "status": "stopped"
}
```

**Error (400 Bad Request):**
```json
{
  "error": "No simulation running"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/simulation/stop
```

---

## WebSocket Events

### Connection

```javascript
const socket = io('http://localhost:5000');

socket.on('connected', (data) => {
  console.log(data.data);  // "Connected to Drone Swarm Server"
});
```

---

### Event: `simulation_started`

Fired when simulation begins.

**Payload:**
```json
{
  "timestamp": "2026-03-25T12:00:00.123456"
}
```

**Handler:**
```javascript
socket.on('simulation_started', (data) => {
  console.log('Simulation started at:', data.timestamp);
});
```

---

### Event: `drones_spawned`

Fired after drones are spawned.

**Payload:**
```json
{
  "count": 5,
  "drones": [
    {
      "id": "drone_000",
      "position": {"x": 15.3, "y": -22.1, "z": 18.5},
      "velocity": {"x": 2.1, "y": 0.8, "z": 0},
      "heading": 0.785,
      "battery_pct": 100.0,
      "role": "SCOUT",
      "status": "ACTIVE"
    },
    ...
  ]
}
```

**Handler:**
```javascript
socket.on('drones_spawned', (data) => {
  console.log(`Spawned ${data.count} drones`);
  data.drones.forEach(drone => {
    console.log(drone.id, drone.role);
  });
});
```

---

### Event: `simulation_update`

Emitted **every 5 simulated seconds** with current state snapshot.

**Payload:**
```json
{
  "time": 5.0,
  "tick": 100,
  "drones": [
    {
      "id": "drone_000",
      "position": {"x": 25.3, "y": -15.2, "z": 19.1},
      "velocity": {"x": 1.8, "y": 1.2, "z": 0.1},
      "heading": 0.891,
      "battery_pct": 99.23,
      "role": "SCOUT",
      "status": "ACTIVE"
    },
    ...
  ],
  "threats": [
    {
      "id": "threat_000",
      "position": {"x": 50.0, "y": 60.0, "z": 0},
      "classification": "person",
      "active": true
    },
    ...
  ],
  "stats": {
    "active_drones": 5,
    "total_drones": 5,
    "avg_battery": 98.5,
    "threats": 2
  }
}
```

**Handler:**
```javascript
socket.on('simulation_update', (data) => {
  console.log(`T=${data.time}s | Ticks=${data.tick}`);
  console.log(`Active: ${data.stats.active_drones}/${data.stats.total_drones}`);
  console.log(`Avg Battery: ${data.stats.avg_battery.toFixed(1)}%`);
  
  // Render drones and threats
  data.drones.forEach(drone => {
    const x = projectX(drone.position.x);
    const y = projectY(drone.position.y);
    drawDrone(x, y, drone.role);
  });
});
```

---

### Event: `simulation_complete`

Fired when simulation finishes or is stopped.

**Payload:**
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

**Handler:**
```javascript
socket.on('simulation_complete', (data) => {
  console.log('Simulation finished');
  console.log(`Total ticks: ${data.metrics.total_ticks}`);
  console.log(`Final avg battery: ${data.metrics.avg_battery.toFixed(1)}%`);
});
```

---

### Event: `simulation_error`

Fired if an error occurs during simulation.

**Payload:**
```json
{
  "error": "Division by zero in physics engine"
}
```

**Handler:**
```javascript
socket.on('simulation_error', (data) => {
  console.error('Simulation error:', data.error);
});
```

---

## Data Models

### DroneState

```typescript
{
  id: string              // "drone_000", "drone_001", ...
  position: Vec3          // {x, y, z} in meters
  velocity: Vec3          // {x, y, z} in m/s
  heading: number         // radians, 0 = +X axis
  battery_pct: number     // 0.0 - 100.0
  role: "SCOUT" | "GUARD" | "RELAY"
  status: "ACTIVE" | "RETURNING" | "DOCKED" | "OFFLINE"
}
```

### ThreatVector

```typescript
{
  id: string              // "threat_000", "threat_001", ...
  position: Vec3          // {x, y, z} in meters
  classification: string  // "person", "vehicle", etc.
  active: boolean         // true if currently detected
}
```

### Vec3

```typescript
{
  x: number               // meters
  y: number               // meters
  z: number               // meters
}
```

---

## Configuration Parameters

### num_drones
- **Type:** integer
- **Range:** 1-50
- **Default:** 5
- **Description:** Number of autonomous drones to spawn

### num_threats
- **Type:** integer
- **Range:** 0-10
- **Default:** 2
- **Description:** Number of threat actors to spawn

### duration
- **Type:** float
- **Range:** 10-600
- **Default:** 60.0
- **Unit:** seconds
- **Description:** Simulation runtime

### dt
- **Type:** float
- **Range:** 0.01-0.1
- **Default:** 0.05
- **Unit:** seconds
- **Description:** Physics timestep (smaller = more accurate, slower)

### headless
- **Type:** boolean
- **Default:** true
- **Description:** Disable Pygame visualization (use false only if display available)

---

## Error Handling

All errors follow this format:

```json
{
  "error": "Human-readable error message"
}
```

### Status Codes

- **200 OK** — Request successful
- **400 Bad Request** — Invalid parameters or invalid state
- **500 Internal Server Error** — Backend crash

---

## Example: Complete Workflow

```javascript
// 1. Connect to server
const socket = io('http://localhost:5000');

// 2. Wait for socket connection
socket.on('connected', () => {
  console.log('Connected!');
});

// 3. Update config (optional)
fetch('http://localhost:5000/api/config', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ num_drones: 10, duration: 120 })
});

// 4. Start simulation
fetch('http://localhost:5000/api/simulation/start', {
  method: 'POST'
});

// 5. Listen for updates
socket.on('simulation_update', (data) => {
  console.log(`Sim time: ${data.time}s`);
  console.log(`Active drones: ${data.stats.active_drones}`);
  // Render visualization here
});

// 6. Listen for completion
socket.on('simulation_complete', (data) => {
  console.log('Done!', data.metrics);
});

// 7. Handle errors
socket.on('simulation_error', (data) => {
  console.error('Error:', data.error);
});

// Manual stop (optional)
// fetch('http://localhost:5000/api/simulation/stop', { method: 'POST' });
```

---

## Rate Limits

- WebSocket events: ~1 per 5 simulated seconds
- HTTP requests: No limit (local development)

---

## CORS

Frontend hosted at different origin? Ensure backend allows:

```python
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000"]}})
```

---

## Troubleshooting

### WebSocket Connection Fails
- Check backend running: `curl http://localhost:5000/api/health`
- Check CORS headers
- Browser console (F12) for detailed errors

### Simulation Never Starts
- Check `/api/config` has valid parameters
- Check backend logs for Python exceptions
- Try smaller drone count (< 10)

### Simulation Crashes
- Increase `dt` to 0.1 for stability
- Reduce `num_drones`
- Check terminal for traceback

---

## License

MIT © 2026
