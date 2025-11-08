# Real-Time Police Car Location Tracking System

## Overview

This system provides **real-time location tracking** for police vehicles using a hybrid Redis + MongoDB architecture with WebSocket streaming.

## Architecture

```
┌─────────────────┐      ┌──────────────┐      ┌──────────────┐
│  Car Simulator  │ ───▶ │    Redis     │ ───▶ │  WebSocket   │
│  (1s updates)   │      │ (Real-time)  │      │   Clients    │
└─────────────────┘      └──────────────┘      └──────────────┘
                               │
                               │ Sync every 10s
                               ▼
                         ┌──────────────┐
                         │   MongoDB    │
                         │ (Persistent) │
                         └──────────────┘
```

### Components

1. **Redis** - High-frequency location storage (1 second updates)
2. **MongoDB** - Persistent storage (synced every 10 seconds)
3. **WebSocket** - Real-time streaming to clients
4. **Car Simulator** - Simulates realistic vehicle movement

## How It Works

### 1. Real-Time Updates (Redis)

-   Car positions are updated **every 1 second** in Redis
-   Each car has a key: `car:location:{car_id}`
-   Data includes: `lat`, `lng`, `speed`, `heading`, `timestamp`
-   Redis pub/sub publishes updates to channel: `car:location:stream:{car_id}`

### 2. Persistent Storage (MongoDB)

-   Background service syncs Redis → MongoDB **every 10 seconds**
-   MongoDB stores the last known position for each car
-   Used for historical queries and incident dispatching

### 3. WebSocket Streaming

-   Clients connect to: `ws://localhost:8000/ws/track/{car_id}`
-   Subscribes to Redis pub/sub for that specific car
-   Receives location updates in real-time (1 second intervals)

### 4. Car Simulation

-   Simulates realistic police car movement in Atlanta area
-   Random patrol routes with realistic speeds (20-60 mph)
-   Automatically updates both Redis and triggers pub/sub

## Setup

### 1. Install Redis

**macOS:**

```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**

```bash
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

**Windows:** Download from: https://redis.io/download

### 2. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Required packages:

-   `redis` - Redis client
-   `websockets` - WebSocket support
-   `fastapi` - API framework
-   `uvicorn` - ASGI server

### 3. Configure Environment

Add to your `.env` file:

```env
# Redis Configuration (optional, defaults shown)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# MongoDB Configuration (existing)
MONGO_URI=mongodb+srv://...
```

### 4. Start the Server

```bash
uvicorn backend.api:app --reload
```

This will automatically start:

-   ✅ Location sync service (Redis → MongoDB every 10s)
-   ✅ Car simulator (movement every 1s)
-   ✅ WebSocket server
-   ✅ REST API endpoints

## API Endpoints

### Get Real-Time Location (Redis)

**Single Car:**

```bash
GET /police/realtime/{car_id}

# Example
curl http://localhost:8000/police/realtime/PC-001
```

**Response:**

```json
{
	"status": "success",
	"car_id": "PC-001",
	"location": {
		"car_id": "PC-001",
		"lat": 33.749,
		"lng": -84.388,
		"speed": 45.2,
		"heading": 270.5,
		"timestamp": "2025-11-08T10:30:45.123Z"
	}
}
```

**All Cars:**

```bash
GET /police/realtime

curl http://localhost:8000/police/realtime
```

### Find Nearby Cars

```bash
POST /police/nearby
Content-Type: application/json

{
  "lat": 33.7490,
  "lng": -84.3880,
  "radius_km": 5.0
}
```

**Response:**

```json
{
	"status": "success",
	"center": { "lat": 33.749, "lng": -84.388 },
	"radius_km": 5.0,
	"count": 3,
	"cars": [
		{
			"car_id": "PC-001",
			"lat": 33.7501,
			"lng": -84.389,
			"speed": 35.0,
			"heading": 180.0,
			"distance_km": 0.15
		}
	]
}
```

### WebSocket: Stream Car Location

**JavaScript Client:**

```javascript
// Connect to WebSocket
const ws = new WebSocket("ws://localhost:8000/ws/track/PC-001");

// Receive real-time updates
ws.onmessage = (event) => {
	const location = JSON.parse(event.data);
	console.log(`Position: ${location.lat}, ${location.lng}`);
	console.log(`Speed: ${location.speed} mph`);
	console.log(`Heading: ${location.heading}°`);

	// Update map marker
	updateCarMarker(location);
};

// Handle connection
ws.onopen = () => console.log("Connected to car tracker");
ws.onerror = (error) => console.error("WebSocket error:", error);
ws.onclose = () => console.log("Disconnected from car tracker");
```

**Python Client:**

```python
import asyncio
import websockets
import json

async def track_car(car_id):
    uri = f"ws://localhost:8000/ws/track/{car_id}"

    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            location = json.loads(message)

            if location.get('status') == 'connected':
                print(f"Connected to {car_id}")
            else:
                print(f"Position: {location['lat']}, {location['lng']}")
                print(f"Speed: {location['speed']} mph")

asyncio.run(track_car("PC-001"))
```

### Simulator Control

**Add Car to Simulator:**

```bash
POST /simulator/add/PC-001?lat=33.7490&lng=-84.3880
```

**Remove Car from Simulator:**

```bash
DELETE /simulator/remove/PC-001
```

## Use Case: Dispatcher Workflow

### Scenario: Incident Reported

1. **Dispatcher receives incident** at location: `33.7490, -84.3880`

2. **Find nearby available cars:**

```bash
POST /police/nearby
{
  "lat": 33.7490,
  "lng": -84.3880,
  "radius_km": 3.0
}
```

3. **View last known positions** (from MongoDB - 10s resolution)

```bash
GET /police/available
```

4. **Dispatcher selects car** `PC-001` to dispatch

5. **Subscribe to real-time tracking** (WebSocket - 1s resolution)

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/track/PC-001");
ws.onmessage = (event) => {
	const location = JSON.parse(event.data);
	// Update map with car's current position every second
	map.updateMarker("PC-001", location.lat, location.lng);
};
```

6. **Dispatch the car:**

```bash
POST /police/dispatch
{
  "car_id": "PC-001",
  "incident_id": "INC-12345"
}
```

7. **Track car until arrival** via WebSocket stream

## Service Statistics

Get real-time service stats:

```bash
GET /stats
```

**Response:**

```json
{
	"sync_service": {
		"total_syncs": 145,
		"successful_updates": 1450,
		"failed_updates": 0,
		"last_sync": "2025-11-08T10:30:45.123Z"
	},
	"simulator": {
		"active_cars": 5,
		"cars": ["PC-001", "PC-002", "PC-003", "K9-001", "K9-002"]
	}
}
```

## Testing

### Test Redis Connection

```bash
cd backend
python redis_client.py
```

### Test Location Sync Service

```bash
python location_sync.py
```

### Test Car Simulator

```bash
python car_simulator.py
```

### Test WebSocket Connection

```bash
# Using wscat (install: npm install -g wscat)
wscat -c ws://localhost:8000/ws/track/PC-001
```

## Performance Characteristics

| Operation | Data Source | Update Frequency | Latency | Use Case |
| --- | --- | --- | --- | --- |
| Real-time location | Redis | 1 second | ~5ms | Active tracking |
| Historical position | MongoDB | 10 seconds | ~20ms | Incident dispatch |
| WebSocket stream | Redis pub/sub | 1 second | ~10ms | Live monitoring |
| Nearby search | Redis | Real-time | ~15ms | Finding available units |

## Data Structure

### Redis Location Data

```json
{
	"car_id": "PC-001",
	"lat": 33.749,
	"lng": -84.388,
	"speed": 45.2,
	"heading": 270.5,
	"timestamp": "2025-11-08T10:30:45.123Z"
}
```

### MongoDB Location Data

```json
{
	"car_id": "PC-001",
	"location": {
		"lat": 33.749,
		"lng": -84.388,
		"address": "Moving at 45.2 mph"
	},
	"updated_at": "2025-11-08T10:30:40.000Z"
}
```

## Troubleshooting

### Redis Connection Failed

```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# Start Redis
brew services start redis  # macOS
sudo systemctl start redis  # Linux
```

### No Location Updates

1. Check if simulator is running:

```bash
GET /stats
```

2. Add cars to simulator:

```bash
POST /simulator/add/PC-001
```

3. Check Redis keys:

```bash
redis-cli keys "car:location:*"
```

### WebSocket Not Connecting

1. Verify WebSocket URL format: `ws://` not `wss://`
2. Check if car exists in simulator
3. Verify Redis pub/sub is working:

```bash
redis-cli SUBSCRIBE car:location:stream:PC-001
```

## Production Considerations

### Scaling

-   Use Redis Cluster for high availability
-   Use Redis Sentinel for automatic failover
-   Consider Redis Stream instead of pub/sub for guaranteed delivery

### Security

-   Enable Redis authentication: `REDIS_PASSWORD=your_secure_password`
-   Use `wss://` (WebSocket Secure) in production
-   Implement JWT authentication for WebSocket connections

### Monitoring

-   Monitor Redis memory usage: `redis-cli INFO memory`
-   Set TTL on location keys (currently 5 minutes)
-   Monitor sync service statistics via `/stats` endpoint

## Next Steps

1. **Frontend Integration**: Connect React/Next.js to WebSocket
2. **Route Prediction**: Use historical data to predict ETA
3. **Geofencing**: Alert when cars enter/exit zones
4. **Battery Optimization**: Adaptive update frequency based on movement
5. **Historical Playback**: Replay car movements from MongoDB logs

## Resources

-   [Redis Documentation](https://redis.io/docs/)
-   [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
-   [Mapbox Real-time Updates](https://docs.mapbox.com/mapbox-gl-js/example/)
