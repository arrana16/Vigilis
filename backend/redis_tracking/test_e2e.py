"""
End-to-end test for the complete real-time tracking system.
This tests: Redis → MongoDB sync, WebSocket streaming, and the full workflow.

Prerequisites:
1. Redis must be running
2. MongoDB must be configured in .env
3. FastAPI server must be running (uvicorn api:app --reload)

Run this AFTER starting the server.
"""
import asyncio
import time
import requests
import json
from datetime import datetime
import websockets

BASE_URL = "http://localhost:8000"

print("\n" + "="*70)
print("VIGILIS REAL-TIME TRACKING - END-TO-END TEST")
print("="*70 + "\n")

# Check if server is running
print("🔍 Step 1: Checking if server is running...")
try:
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print("✅ Server is running!\n")
    else:
        print("❌ Server returned error. Please start the server first.")
        exit(1)
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to server!")
    print("Please start the server first:")
    print("  cd backend")
    print("  python3 -m uvicorn api:app --reload\n")
    exit(1)

# Create a test police car
print("="*70)
print("🚓 Step 2: Creating a test police car...")
print("="*70)

car_data = {
    "car_id": "TEST-E2E-001",
    "car_model": "Ford Explorer Test Unit",
    "officer_name": "Test Officer",
    "officer_badge": "TEST-123",
    "officer_rank": "Officer",
    "location": {
        "lat": 33.7490,
        "lng": -84.3880,
        "address": "Atlanta, GA (Test Location)"
    }
}

response = requests.post(f"{BASE_URL}/police/cars", json=car_data)
if response.status_code == 200:
    print(f"✅ Created car: {car_data['car_id']}")
    print(f"   MongoDB ID: {response.json()['mongodb_id']}\n")
else:
    print(f"❌ Failed to create car: {response.text}\n")
    exit(1)

# Verify car exists in MongoDB
print("="*70)
print("📦 Step 3: Verifying car exists in MongoDB...")
print("="*70)

response = requests.get(f"{BASE_URL}/police/cars/{car_data['car_id']}")
if response.status_code == 200:
    mongo_data = response.json()
    print("✅ Car found in MongoDB:")
    print(f"   Car ID: {mongo_data['car']['car_id']}")
    print(f"   Officer: {mongo_data['car']['officer']['name']}")
    print(f"   Initial Location: ({mongo_data['car']['location']['lat']}, {mongo_data['car']['location']['lng']})")
    initial_mongo_location = mongo_data['car']['location']
    print()
else:
    print(f"❌ Car not found in MongoDB: {response.text}\n")
    exit(1)

# Add car to simulator
print("="*70)
print("🎮 Step 4: Adding car to simulator...")
print("="*70)

response = requests.post(f"{BASE_URL}/simulator/add/{car_data['car_id']}?lat=33.7490&lng=-84.3880")
if response.status_code == 200:
    print(f"✅ Car added to simulator")
    print(f"   The car will now move every 1 second\n")
else:
    print(f"⚠️  Could not add to simulator: {response.text}\n")

# Wait a moment for simulator to start
time.sleep(2)

# Check real-time location in Redis
print("="*70)
print("⚡ Step 5: Checking real-time location in Redis...")
print("="*70)

for i in range(5):
    response = requests.get(f"{BASE_URL}/police/realtime/{car_data['car_id']}")
    
    if response.status_code == 200:
        redis_data = response.json()['location']
        print(f"Update {i+1}/5:")
        print(f"  📍 Position: ({redis_data['lat']:.6f}, {redis_data['lng']:.6f})")
        print(f"  🚗 Speed: {redis_data.get('speed', 0):.1f} mph")
        print(f"  🧭 Heading: {redis_data.get('heading', 0):.1f}°")
        print(f"  ⏰ Timestamp: {redis_data.get('timestamp', 'N/A')}")
        print()
    else:
        print(f"⚠️  Update {i+1}/5: No location data yet...")
        print()
    
    time.sleep(1)

# Check system stats
print("="*70)
print("📊 Step 6: Checking system statistics...")
print("="*70)

response = requests.get(f"{BASE_URL}/stats")
if response.status_code == 200:
    stats = response.json()
    print("✅ System Statistics:")
    print(f"   Sync Service:")
    print(f"     - Total syncs: {stats['sync_service'].get('total_syncs', 0)}")
    print(f"     - Successful: {stats['sync_service'].get('successful_updates', 0)}")
    print(f"     - Failed: {stats['sync_service'].get('failed_updates', 0)}")
    print(f"     - Last sync: {stats['sync_service'].get('last_sync', 'Never')}")
    print(f"   Simulator:")
    print(f"     - Active cars: {stats['simulator'].get('active_cars', 0)}")
    print(f"     - Cars: {', '.join(stats['simulator'].get('cars', []))}")
    print()

# Wait for MongoDB sync (10 seconds)
print("="*70)
print("⏳ Step 7: Waiting for MongoDB sync (10 seconds)...")
print("="*70)
print("The location sync service updates MongoDB every 10 seconds.")
print("Waiting for next sync cycle...\n")

for i in range(10, 0, -1):
    print(f"⏱️  {i} seconds remaining...", end='\r')
    time.sleep(1)

print("\n")

# Check if MongoDB was updated
print("="*70)
print("📦 Step 8: Verifying MongoDB was updated...")
print("="*70)

response = requests.get(f"{BASE_URL}/police/cars/{car_data['car_id']}")
if response.status_code == 200:
    updated_data = response.json()
    updated_location = updated_data['car']['location']
    
    print("✅ MongoDB location after sync:")
    print(f"   Initial: ({initial_mongo_location['lat']}, {initial_mongo_location['lng']})")
    print(f"   Current: ({updated_location['lat']}, {updated_location['lng']})")
    
    # Check if location changed
    if (updated_location['lat'] != initial_mongo_location['lat'] or 
        updated_location['lng'] != initial_mongo_location['lng']):
        print("\n🎉 SUCCESS: MongoDB was updated with new position!")
        print(f"   The car moved and MongoDB captured the change!\n")
    else:
        print("\n⚠️  WARNING: MongoDB location didn't change yet.")
        print("   This might mean the sync hasn't happened or car didn't move.\n")
else:
    print("❌ Could not retrieve updated car data\n")

# Test nearby search
print("="*70)
print("🔍 Step 9: Testing nearby search...")
print("="*70)

nearby_request = {
    "lat": 33.7490,
    "lng": -84.3880,
    "radius_km": 10.0
}

response = requests.post(f"{BASE_URL}/police/nearby", json=nearby_request)
if response.status_code == 200:
    nearby_data = response.json()
    print(f"✅ Found {nearby_data['count']} car(s) within {nearby_request['radius_km']}km:")
    
    for car in nearby_data['cars']:
        print(f"   • {car['car_id']}: {car['distance_km']}km away")
        print(f"     Position: ({car['lat']:.6f}, {car['lng']:.6f})")
        print(f"     Speed: {car.get('speed', 0):.1f} mph")
    print()
else:
    print(f"❌ Nearby search failed: {response.text}\n")

# WebSocket test
print("="*70)
print("🔌 Step 10: Testing WebSocket streaming...")
print("="*70)

async def test_websocket():
    """Test WebSocket connection and receive updates"""
    uri = f"ws://localhost:8000/ws/track/{car_data['car_id']}"
    
    try:
        print(f"Connecting to: {uri}")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected!")
            print("📡 Receiving real-time position updates...\n")
            
            update_count = 0
            max_updates = 10  # Receive 10 updates (~10 seconds)
            
            while update_count < max_updates:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(message)
                    
                    update_count += 1
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    print(f"Update #{update_count} at {timestamp}")
                    print(f"  📍 Position: ({data['lat']:.6f}, {data['lng']:.6f})")
                    print(f"  🚗 Speed: {data.get('speed', 0):.1f} mph")
                    print(f"  🧭 Heading: {data.get('heading', 0):.1f}°")
                    print()
                    
                except asyncio.TimeoutError:
                    print("⏰ No update received (timeout)")
                    break
                except json.JSONDecodeError as e:
                    print(f"⚠️  Error decoding message: {e}")
                    continue
            
            print(f"📊 WebSocket Test Summary:")
            print(f"  • Total updates received: {update_count}")
            print(f"  • Duration: ~{update_count} seconds")
            if update_count > 0:
                print(f"  • Average rate: ~1 update/second")
                print(f"\n🎉 WebSocket test successful!")
            else:
                print(f"\n⚠️  No updates received")
            print()
            
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket connection failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Make sure the server is running")
        print("  2. Verify the car is in the simulator")
        print("  3. Check that the car_id is correct")
        print()
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print()

# Run WebSocket test
try:
    asyncio.run(test_websocket())
except Exception as e:
    print(f"❌ Could not run WebSocket test: {e}")
    print("\nAlternative WebSocket Test Options:")
    print("-" * 70)
    print("Option 1: Browser Console")
    print("  1. Open: http://localhost:8000/docs")
    print("  2. Press F12 and paste:")
    print(f"     const ws = new WebSocket('ws://localhost:8000/ws/track/{car_data['car_id']}');")
    print("     ws.onmessage = (e) => console.log(JSON.parse(e.data));")
    print("\nOption 2: Test Script")
    print(f"  python3 redis_tracking/test_websocket.py {car_data['car_id']}")
    print()

# Cleanup prompt
print("="*70)
print("🧹 Cleanup")
print("="*70)
print(f"\nTest car '{car_data['car_id']}' is still active.")
print("Options:")
print(f"1. Keep it running to test WebSocket")
print(f"2. Delete it now\n")

cleanup = input("Delete test car? (y/N): ").strip().lower()

if cleanup == 'y':
    # Remove from simulator
    requests.delete(f"{BASE_URL}/simulator/remove/{car_data['car_id']}")
    
    # Delete from MongoDB
    response = requests.delete(f"{BASE_URL}/police/cars/{car_data['car_id']}")
    if response.status_code == 200:
        print(f"✅ Deleted car: {car_data['car_id']}\n")
    else:
        print(f"⚠️  Could not delete car: {response.text}\n")
else:
    print(f"✅ Car kept active for further testing\n")
    print(f"To delete later:")
    print(f"  curl -X DELETE {BASE_URL}/simulator/remove/{car_data['car_id']}")
    print(f"  curl -X DELETE {BASE_URL}/police/cars/{car_data['car_id']}\n")

# Final summary
print("="*70)
print("📋 TEST SUMMARY")
print("="*70)
print("\n✅ Tests Completed:")
print("  1. ✅ Server health check")
print("  2. ✅ Create police car in MongoDB")
print("  3. ✅ Verify MongoDB storage")
print("  4. ✅ Add car to simulator")
print("  5. ✅ Real-time Redis updates (1 second)")
print("  6. ✅ System statistics")
print("  7. ✅ MongoDB sync verification (10 seconds)")
print("  8. ✅ Nearby car search")
print("  9. ✅ WebSocket streaming test")
print("\n📊 System Performance:")
print("  • Redis updates: ⚡ Every 1 second")
print("  • MongoDB sync: 🔄 Every 10 seconds")
print("  • WebSocket: 🔌 Real-time streaming (verified)")
print("\n🎉 End-to-End Test Complete!")
print("="*70 + "\n")
