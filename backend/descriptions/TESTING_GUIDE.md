# 🧪 Testing Redis Real-Time Tracking - Step by Step

Follow these steps to test your Redis real-time tracking system.

## ✅ Step 1: Install Redis

### macOS (using Homebrew)

```bash
brew install redis
brew services start redis
```

### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

### Verify Redis is Running

```bash
redis-cli ping
```

**Expected output:** `PONG`

---

## ✅ Step 2: Install Python Dependencies

```bash
cd backend
pip install redis websockets
```

Or install all dependencies:

```bash
pip install -r requirements.txt
```

---

## ✅ Step 3: Configure Environment

Make sure your `.env` file has MongoDB and Redis settings:

```bash
# Copy example if you haven't already
cp .env.example .env

# Edit .env and add your MongoDB URI
nano .env
```

Your `.env` should have:

```env
MONGO_URI=mongodb+srv://your-connection-string

# Redis (optional - these are defaults)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
```

---

## ✅ Step 4: Run the Redis Test Suite

This will verify everything is working:

```bash
cd backend
python redis/test_redis_system.py
```

**Expected output:**

```
==============================================================
REDIS REAL-TIME TRACKING SYSTEM - TEST SUITE
==============================================================

TEST 1: Redis Connection
✅ Successfully connected to Redis!

TEST 2: Location Updates
✅ Location update successful
✅ Location retrieved:
   Lat: 33.749
   Lng: -84.388
   Speed: 45.5 mph
   Heading: 270.0°

TEST 3: All Locations
✅ Found 3 car(s) in Redis:
   - TEST-001: (33.7490, -84.3880)
   - TEST-002: (33.7500, -84.3900)
   - TEST-003: (33.7510, -84.3920)

TEST 4: Nearby Search
✅ Found 3 nearby car(s):
   - TEST-001: 0.0km away
   - TEST-002: 0.23km away
   - TEST-003: 0.48km away

TEST 5: Car Simulator
🚓 Added SIM-001 to simulator...
Running simulator for 5 seconds...
✅ Simulator test complete

==============================================================
TEST SUMMARY
==============================================================
✅ PASS: Redis Connection
✅ PASS: Location Updates
✅ PASS: All Locations
✅ PASS: Nearby Search
✅ PASS: Car Simulator

Passed: 5/5

🎉 All tests passed! System is working correctly.
```

---

## ✅ Step 5: Start the FastAPI Server

```bash
cd backend
uvicorn api:app --reload
```

**Expected output:**

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
✅ Background services started: location sync & car simulator
```

The server automatically starts:

-   🔄 Location sync service (Redis → MongoDB every 10s)
-   🚗 Car simulator (simulates movement every 1s)

---

## ✅ Step 6: Test API Endpoints

Keep the server running and open a **new terminal**.

### 6.1 Check Server Health

```bash
curl http://localhost:8000/health
```

**Expected:**

```json
{ "status": "healthy" }
```

### 6.2 Check System Statistics

```bash
curl http://localhost:8000/stats
```

**Expected:**

```json
{
	"sync_service": {
		"total_syncs": 0,
		"successful_updates": 0,
		"failed_updates": 0,
		"last_sync": null
	},
	"simulator": {
		"active_cars": 0,
		"cars": []
	}
}
```

### 6.3 Create a Police Car

```bash
curl -X POST http://localhost:8000/police/cars \
  -H "Content-Type: application/json" \
  -d '{
    "car_id": "PC-001",
    "car_model": "Ford Explorer Police Interceptor",
    "officer_name": "John Smith",
    "officer_badge": "B12345",
    "officer_rank": "Officer",
    "location": {
      "lat": 33.7490,
      "lng": -84.3880,
      "address": "Downtown Atlanta"
    }
  }'
```

**Expected:**

```json
{
	"status": "success",
	"message": "Police car PC-001 created successfully",
	"car_id": "PC-001",
	"mongodb_id": "..."
}
```

### 6.4 Add Car to Simulator

```bash
curl -X POST "http://localhost:8000/simulator/add/PC-001?lat=33.7490&lng=-84.3880"
```

**Expected:**

```json
{
	"status": "success",
	"message": "Car PC-001 added to simulator",
	"car_id": "PC-001"
}
```

### 6.5 Get Real-Time Location from Redis

Wait 2-3 seconds, then:

```bash
curl http://localhost:8000/police/realtime/PC-001
```

**Expected:**

```json
{
	"status": "success",
	"car_id": "PC-001",
	"location": {
		"car_id": "PC-001",
		"lat": 33.74905,
		"lng": -84.38802,
		"speed": 45.2,
		"heading": 180.5,
		"timestamp": "2025-11-08T10:30:45.123Z"
	}
}
```

### 6.6 Find Nearby Cars

```bash
curl -X POST http://localhost:8000/police/nearby \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 33.7490,
    "lng": -84.3880,
    "radius_km": 5.0
  }'
```

**Expected:**

```json
{
	"status": "success",
	"center": { "lat": 33.749, "lng": -84.388 },
	"radius_km": 5.0,
	"count": 1,
	"cars": [
		{
			"car_id": "PC-001",
			"lat": 33.74905,
			"lng": -84.38802,
			"speed": 45.2,
			"heading": 180.5,
			"distance_km": 0.05,
			"timestamp": "..."
		}
	]
}
```

---

## ✅ Step 7: Test WebSocket Streaming

### Option A: Using Browser Console

1. Open http://localhost:8000/docs (Swagger UI)
2. Open browser console (F12)
3. Run this code:

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/track/PC-001");

ws.onopen = () => console.log("✅ Connected to WebSocket");

ws.onmessage = (event) => {
	const data = JSON.parse(event.data);
	console.log("📍 Position:", data.lat, data.lng);
	console.log("🚗 Speed:", data.speed, "mph");
	console.log("🧭 Heading:", data.heading, "°");
};

ws.onerror = (error) => console.error("❌ WebSocket error:", error);
ws.onclose = () => console.log("🔌 Disconnected");
```

### Option B: Using wscat (Node.js tool)

```bash
# Install wscat
npm install -g wscat

# Connect to WebSocket
wscat -c ws://localhost:8000/ws/track/PC-001
```

You should see position updates every second!

---

## ✅ Step 8: Run the Live Demo

In a new terminal:

```bash
cd backend
python redis/demo_realtime_tracking.py
```

This will:

1. Create a demo car
2. Add it to the simulator
3. Watch it move in real-time for 10 seconds
4. Check MongoDB sync
5. Find nearby cars
6. Show system statistics
7. Clean up

---

## ✅ Step 9: Verify MongoDB Sync

After 10+ seconds, check if Redis synced to MongoDB:

```bash
curl http://localhost:8000/police/cars/PC-001
```

The `location` field should have been updated from Redis!

---

## ✅ Step 10: Check System Stats Again

```bash
curl http://localhost:8000/stats
```

Now you should see:

```json
{
	"sync_service": {
		"total_syncs": 6,
		"successful_updates": 6,
		"failed_updates": 0,
		"last_sync": "2025-11-08T10:31:00.000Z"
	},
	"simulator": {
		"active_cars": 1,
		"cars": ["PC-001"]
	}
}
```

---

## 🎉 Success Checklist

-   ✅ Redis is running (`redis-cli ping` returns `PONG`)
-   ✅ All tests pass (`python redis/test_redis_system.py`)
-   ✅ Server starts without errors
-   ✅ Can create police cars
-   ✅ Can add cars to simulator
-   ✅ Real-time locations appear in Redis
-   ✅ WebSocket streams position updates
-   ✅ MongoDB syncs every 10 seconds
-   ✅ Nearby search finds cars by distance
-   ✅ System stats show active services

---

## 🐛 Troubleshooting

### Redis not running

```bash
# macOS
brew services start redis

# Linux
sudo systemctl start redis

# Verify
redis-cli ping  # Should return: PONG
```

### Server won't start

```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill the process if needed
kill -9 <PID>

# Or use a different port
uvicorn api:app --reload --port 8001
```

### No location updates

```bash
# Check if car is in simulator
curl http://localhost:8000/stats

# Manually add car
curl -X POST http://localhost:8000/simulator/add/PC-001
```

### WebSocket not connecting

-   Make sure you use `ws://` not `wss://`
-   Verify car exists: `curl http://localhost:8000/police/realtime/PC-001`
-   Check server logs for errors

### Import errors

```bash
# Make sure you're in the backend directory
cd backend

# Reinstall dependencies
pip install -r requirements.txt
```

---

## 📊 What You're Testing

1. **Redis Storage** - High-frequency location updates (1s)
2. **MongoDB Sync** - Periodic synchronization (10s)
3. **Car Simulator** - Realistic movement simulation
4. **WebSocket Streaming** - Real-time position updates
5. **Distance Search** - Finding nearby cars using Haversine
6. **Background Services** - Auto-start location sync and simulator

---

## 🔜 Next Steps

Once everything is working:

1. **Create more cars** - Add PC-002, PC-003, etc.
2. **Test dispatch** - Use `/police/dispatch` endpoint
3. **Frontend integration** - Connect your Next.js map to WebSocket
4. **Monitor stats** - Watch `/stats` endpoint to see syncs happening

---

## 📖 More Information

-   **Full docs**: `descriptions/REDIS_REALTIME_TRACKING.md`
-   **Quick start**: `descriptions/REDIS_QUICK_START.md`
-   **API docs**: http://localhost:8000/docs

---

**You're ready to test!** Start with Step 1 and work your way through. Good luck! 🚀
