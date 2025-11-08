# WebSocket Troubleshooting Guide

## Common WebSocket Issues and Solutions

### Issue 1: No messages received (timeout)

**Symptoms:**

-   WebSocket connects successfully
-   Receives initial confirmation message
-   But no location updates come through

**Root Causes:**

1. **Car is not in the simulator**

    - Check: `curl http://localhost:8000/stats`
    - Look for `"active_cars"` count
    - If 0, add car: `curl -X POST "http://localhost:8000/simulator/add/TEST-E2E-001"`

2. **Car doesn't exist in Redis**

    - Check: `curl http://localhost:8000/police/realtime/TEST-E2E-001`
    - Should return location data
    - If not, car hasn't been added to simulator

3. **Redis pub/sub not working**
    - Test Redis: `redis-cli ping` (should return PONG)
    - Check if updates are being published

### Issue 2: Connection fails immediately

**Symptoms:**

-   `InvalidStatusCode` error
-   Connection refused
-   Timeout on connect

**Root Causes:**

1. **Server not running**

    ```bash
    # Start server
    cd backend
    python3 -m uvicorn api:app --reload
    ```

2. **Wrong port**

    - Verify server is on port 8000
    - Check: `curl http://localhost:8000/health`

3. **Server error during startup**
    - Check terminal for error messages
    - Look for import errors, circular dependencies

### Issue 3: Connection drops after a few seconds

**Symptoms:**

-   Connects successfully
-   Receives a few messages
-   Then disconnects

**Root Causes:**

1. **Car removed from simulator**

    - Simulator might have issues
    - Check server logs for errors

2. **Redis connection issue**
    - Redis might have restarted
    - Check: `redis-cli ping`

## Diagnostic Steps

### Step 1: Verify Server is Running

```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

### Step 2: Verify Car Exists in MongoDB

```bash
curl http://localhost:8000/police/cars/TEST-E2E-001
# Should return car data with location
```

### Step 3: Verify Car is in Redis

```bash
curl http://localhost:8000/police/realtime/TEST-E2E-001
# Should return real-time location
```

### Step 4: Verify Car is in Simulator

```bash
curl http://localhost:8000/stats
# Check "simulator" -> "cars" array
# Should include TEST-E2E-001
```

### Step 5: Add Car to Simulator (if missing)

```bash
curl -X POST "http://localhost:8000/simulator/add/TEST-E2E-001?lat=33.7490&lng=-84.3880"
# Should return success message
```

### Step 6: Test WebSocket with Diagnostic Script

```bash
cd backend
python3 redis_tracking/debug_websocket.py
```

### Step 7: Check Server Logs

Look for:

-   WebSocket connection messages
-   Redis pub/sub errors
-   Simulator errors

## Quick Fix Script

If you want to quickly test everything:

```bash
# 1. Make sure server is running
cd backend
python3 -m uvicorn api:app --reload &

# 2. Create test car
curl -X POST "http://localhost:8000/police/cars" \
  -H "Content-Type: application/json" \
  -d '{
    "car_id": "TEST-WS-001",
    "car_model": "Test Unit",
    "officer_name": "Test Officer",
    "officer_badge": "TEST-999",
    "location": {"lat": 33.7490, "lng": -84.3880, "address": "Atlanta"}
  }'

# 3. Add to simulator
curl -X POST "http://localhost:8000/simulator/add/TEST-WS-001?lat=33.7490&lng=-84.3880"

# 4. Wait 2 seconds for movement to start
sleep 2

# 5. Test WebSocket
python3 redis_tracking/debug_websocket.py

# 6. Or run full E2E test
python3 redis_tracking/test_e2e.py
```

## Common Error Messages

### "No module named 'websockets'"

```bash
pip install websockets
```

### "Address already in use"

Server is already running. Kill it:

```bash
lsof -i :8000
kill -9 <PID>
```

### "Connection refused"

Server is not running. Start it:

```bash
cd backend
python3 -m uvicorn api:app --reload
```

### "Timeout waiting for message"

Car is not moving or not in simulator:

```bash
# Check stats
curl http://localhost:8000/stats

# Add to simulator if missing
curl -X POST "http://localhost:8000/simulator/add/TEST-E2E-001"
```

## Testing WebSocket in Browser Console

The easiest way to test WebSocket:

1. Open http://localhost:8000/docs
2. Press F12 (open console)
3. Paste this code:

```javascript
// Create WebSocket connection
const ws = new WebSocket("ws://localhost:8000/ws/track/TEST-E2E-001");

// Connection opened
ws.onopen = () => {
	console.log("✅ WebSocket connected!");
};

// Listen for messages
ws.onmessage = (event) => {
	const data = JSON.parse(event.data);
	console.log("📍 Update:", data);
};

// Connection closed
ws.onclose = () => {
	console.log("🔌 WebSocket disconnected");
};

// Error handler
ws.onerror = (error) => {
	console.error("❌ WebSocket error:", error);
};
```

You should see:

1. Initial confirmation message
2. Location updates every ~1 second

## Redis Pub/Sub Testing

Test if Redis is publishing location updates:

```bash
# In one terminal, subscribe to the channel
redis-cli
SUBSCRIBE car:location:stream:TEST-E2E-001

# You should see messages coming in every second
# Press Ctrl+C to exit
```

If no messages appear, the simulator isn't updating Redis properly.
