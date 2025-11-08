# 🚀 Quick Start: Redis Real-Time Tracking

Get the real-time police car tracking system up and running in 5 minutes!

## Prerequisites

-   Python 3.8+
-   Redis server
-   MongoDB Atlas account (already configured)

## Step 1: Install Redis

### macOS

```bash
brew install redis
brew services start redis
```

### Ubuntu/Debian

```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

### Verify Redis is Running

```bash
redis-cli ping
# Should return: PONG
```

## Step 2: Install Python Dependencies

```bash
cd backend
pip install redis websockets
# or install all dependencies
pip install -r requirements.txt
```

## Step 3: Configure Environment

Add Redis settings to your `.env` file (optional, these are the defaults):

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
```

## Step 4: Test the System

Run the test suite to verify everything works:

```bash
python test_redis_system.py
```

You should see:

```
✅ PASS: Redis Connection
✅ PASS: Location Updates
✅ PASS: All Locations
✅ PASS: Nearby Search
✅ PASS: Car Simulator

🎉 All tests passed! System is working correctly.
```

## Step 5: Start the Server

```bash
uvicorn api:app --reload
```

The server will automatically start:

-   ✅ Location sync service (Redis → MongoDB every 10s)
-   ✅ Car simulator (simulates movement every 1s)
-   ✅ WebSocket server for real-time streaming

## Step 6: Create a Police Car

```bash
curl -X POST http://localhost:8000/police/cars \
  -H "Content-Type: application/json" \
  -d '{
    "car_id": "PC-001",
    "car_model": "Ford Explorer Police Interceptor",
    "officer_name": "John Smith",
    "officer_badge": "B12345",
    "officer_rank": "Officer",
    "location": {"lat": 33.7490, "lng": -84.3880}
  }'
```

## Step 7: Add Car to Simulator

The car will be automatically added to the simulator on startup, but you can manually add cars:

```bash
curl -X POST "http://localhost:8000/simulator/add/PC-001?lat=33.7490&lng=-84.3880"
```

## Step 8: Watch Real-Time Updates

### Option A: HTTP Polling

```bash
# Get real-time location from Redis (updates every 1s)
curl http://localhost:8000/police/realtime/PC-001
```

### Option B: WebSocket Streaming

**Using `wscat` (install: `npm install -g wscat`):**

```bash
wscat -c ws://localhost:8000/ws/track/PC-001
```

**Using JavaScript:**

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/track/PC-001");

ws.onmessage = (event) => {
	const data = JSON.parse(event.data);
	console.log(`Position: ${data.lat}, ${data.lng}`);
	console.log(`Speed: ${data.speed} mph, Heading: ${data.heading}°`);
};
```

### Option C: View in Browser

Open Swagger UI: http://localhost:8000/docs

Try these endpoints:

-   `GET /police/realtime` - See all car positions
-   `GET /stats` - See system statistics
-   `POST /police/nearby` - Find nearby cars

## Step 9: Find Nearby Cars

```bash
curl -X POST http://localhost:8000/police/nearby \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 33.7490,
    "lng": -84.3880,
    "radius_km": 5.0
  }'
```

## Step 10: Verify MongoDB Sync

Wait 10 seconds, then check MongoDB has been updated:

```bash
# Get car from MongoDB (synced every 10s)
curl http://localhost:8000/police/cars/PC-001
```

## Common Commands

### Check System Status

```bash
curl http://localhost:8000/stats
```

### Get All Real-Time Positions

```bash
curl http://localhost:8000/police/realtime
```

### Add More Cars

```bash
# Create in MongoDB
curl -X POST http://localhost:8000/police/cars -H "Content-Type: application/json" -d '{
  "car_id": "PC-002",
  "car_model": "Dodge Charger Pursuit",
  "officer_name": "Sarah Johnson",
  "officer_badge": "B67890"
}'

# Add to simulator
curl -X POST http://localhost:8000/simulator/add/PC-002
```

### Remove Car from Simulator

```bash
curl -X DELETE http://localhost:8000/simulator/remove/PC-001
```

## Troubleshooting

### Redis Connection Failed

```bash
# Check Redis status
redis-cli ping

# Start Redis
brew services start redis  # macOS
sudo systemctl start redis  # Linux
```

### No Location Updates

```bash
# Check stats
curl http://localhost:8000/stats

# Manually add car to simulator
curl -X POST http://localhost:8000/simulator/add/PC-001
```

### Port Already in Use

```bash
# Use a different port
uvicorn api:app --reload --port 8001
```

## What's Happening Behind the Scenes?

1. **Car Simulator** updates positions every 1 second → Redis
2. **Redis** stores current position and publishes to pub/sub channel
3. **WebSocket** subscribers receive updates in real-time
4. **Location Sync Service** copies Redis → MongoDB every 10 seconds
5. **MongoDB** stores last known position for incidents/dispatch

## Next Steps

1. **Frontend Integration**: Connect your Next.js map to the WebSocket
2. **Dispatch Workflow**: Use `/police/nearby` to find cars near incidents
3. **Live Tracking**: Subscribe to WebSocket when dispatcher assigns a car
4. **Historical Data**: Query MongoDB for past positions

## Full Documentation

See `REDIS_REALTIME_TRACKING.md` for complete documentation.

## Architecture Overview

```
Simulator (1s) → Redis → WebSocket → Frontend Map
                   ↓
              Sync (10s)
                   ↓
                MongoDB → Dispatch System
```

---

🎉 **You're all set!** Your real-time police car tracking system is now running.
