# Testing the Complete System

This guide shows you how to test the entire real-time tracking system including Redis, MongoDB sync, and WebSocket streaming.

## Step 1: Start the Server

First, make sure MongoDB is configured in your `.env` file, then start the FastAPI server:

```bash
cd backend
python3 -m uvicorn api:app --reload
```

**Expected output:**

```
INFO:     Uvicorn running on http://127.0.0.1:8000
✅ Background services started: location sync & car simulator
```

The server automatically starts:

-   🔄 **Location sync service** - Syncs Redis → MongoDB every 10 seconds
-   🚗 **Car simulator** - Updates car positions every 1 second

## Step 2: Run End-to-End Test

In a **new terminal**, run the comprehensive test:

```bash
cd backend
python3 redis_tracking/test_e2e.py
```

**This test will:**

1. ✅ Check server health
2. ✅ Create a test police car in MongoDB
3. ✅ Add car to simulator (starts moving)
4. ✅ Watch real-time updates in Redis (1 second intervals)
5. ✅ Wait for MongoDB sync (10 seconds)
6. ✅ Verify MongoDB was updated with new position
7. ✅ Test nearby car search
8. ✅ Provide WebSocket testing instructions

**Sample output:**

```
==============================================================
VIGILIS REAL-TIME TRACKING - END-TO-END TEST
==============================================================

🔍 Step 1: Checking if server is running...
✅ Server is running!

🚓 Step 2: Creating a test police car...
✅ Created car: TEST-E2E-001

📦 Step 3: Verifying car exists in MongoDB...
✅ Car found in MongoDB

🎮 Step 4: Adding car to simulator...
✅ Car added to simulator

⚡ Step 5: Checking real-time location in Redis...
Update 1/5:
  📍 Position: (33.749000, -84.388000)
  🚗 Speed: 45.2 mph
  🧭 Heading: 180.5°

⏳ Step 7: Waiting for MongoDB sync (10 seconds)...

📦 Step 8: Verifying MongoDB was updated...
🎉 SUCCESS: MongoDB was updated with new position!
   The car moved and MongoDB captured the change!
```

## Step 3: Test WebSocket Streaming

After the end-to-end test, you have **3 options** to test WebSocket:

### Option A: Browser Console (Easiest)

1. Open http://localhost:8000/docs in your browser
2. Press **F12** to open console
3. Paste this code:

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/track/TEST-E2E-001");

ws.onopen = () => console.log("✅ Connected to WebSocket!");

ws.onmessage = (event) => {
	const data = JSON.parse(event.data);
	console.log(`📍 Position: ${data.lat}, ${data.lng}`);
	console.log(`🚗 Speed: ${data.speed} mph | 🧭 Heading: ${data.heading}°`);
};

ws.onerror = (error) => console.error("❌ Error:", error);
ws.onclose = () => console.log("🔌 Disconnected");
```

4. Watch real-time updates in the console!

### Option B: Python WebSocket Test

```bash
cd backend
python3 redis_tracking/test_websocket.py TEST-E2E-001
```

**Output:**

```
🔌 WEBSOCKET TRACKING TEST - TEST-E2E-001
✅ Connected to WebSocket!

📍 Receiving real-time position updates:
Update #1 at 10:30:45
  📍 Position: (33.749123, -84.388456)
  🚗 Speed: 45.2 mph
  🧭 Heading: 180.5°

Update #2 at 10:30:46
  📍 Position: (33.749156, -84.388489)
  🚗 Speed: 45.2 mph
  🧭 Heading: 180.5°

📊 Summary:
  • Total updates received: 30
  • Duration: 30.0 seconds
  • Average update rate: 1.00 updates/second

✅ WebSocket test completed successfully!
```

### Option C: wscat (Node.js tool)

```bash
# Install wscat
npm install -g wscat

# Connect
wscat -c ws://localhost:8000/ws/track/TEST-E2E-001
```

## What Each Test Validates

### ✅ Redis Real-Time Tracking (1 second)

-   Car positions updated every 1 second
-   High-frequency location storage
-   Speed and heading calculation
-   Tested by: `test_e2e.py` Step 5

### ✅ MongoDB Sync (10 seconds)

-   Background service syncs Redis → MongoDB
-   Keeps permanent database updated
-   Tested by: `test_e2e.py` Steps 7-8

### ✅ WebSocket Streaming

-   Real-time position updates to clients
-   1 update per second per car
-   Tested by: `test_websocket.py` or browser

### ✅ Nearby Search

-   Haversine distance calculation
-   Find cars within radius
-   Tested by: `test_e2e.py` Step 9

### ✅ Car Simulator

-   Realistic movement patterns
-   Random waypoints in Atlanta area
-   Speed variation (20-60 mph)
-   Tested by: All tests

## Quick Test Commands

```bash
# 1. Start server
python3 -m uvicorn api:app --reload

# 2. Run full end-to-end test (new terminal)
python3 redis_tracking/test_e2e.py

# 3. Test WebSocket
python3 redis_tracking/test_websocket.py TEST-E2E-001

# 4. Check system stats
curl http://localhost:8000/stats

# 5. Get real-time location
curl http://localhost:8000/police/realtime/TEST-E2E-001
```

## Troubleshooting

### Server won't start

```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing process
kill -9 <PID>

# Or use different port
python3 -m uvicorn api:app --reload --port 8001
```

### MongoDB sync not working

Check `.env` has correct MongoDB URI:

```env
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/...
```

### WebSocket won't connect

1. Make sure server is running
2. Verify car exists: `curl http://localhost:8000/police/realtime/TEST-E2E-001`
3. Check car is in simulator: `curl http://localhost:8000/stats`

### No Redis updates

1. Check Redis is running: `redis-cli ping`
2. Start Redis: `brew services start redis` (macOS)
3. Verify car is in simulator

## Expected Performance

| Component     | Update Frequency | Latency | Purpose               |
| ------------- | ---------------- | ------- | --------------------- |
| **Redis**     | 1 second         | ~5ms    | Real-time tracking    |
| **MongoDB**   | 10 seconds       | ~20ms   | Persistent storage    |
| **WebSocket** | 1 second         | ~10ms   | Live client streaming |

## Success Indicators

✅ **Redis working** - Location updates every second ✅ **MongoDB sync working** - Location changes after 10 seconds  
✅ **WebSocket working** - Continuous stream of position updates ✅ **Simulator working** - Car moves with realistic speed/heading

## Next Steps

Once everything is working:

1. **Create real cars** - Add PC-001, PC-002, etc.
2. **Test dispatch** - Use `/police/dispatch` endpoint
3. **Frontend integration** - Connect Next.js map to WebSocket
4. **Monitor production** - Watch `/stats` for sync health

---

**You're ready to test!** Start with Step 1 and work through each step. 🚀
