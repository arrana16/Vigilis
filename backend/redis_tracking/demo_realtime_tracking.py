"""
Visual demonstration of how the real-time tracking system works.
Run this after starting Redis and the FastAPI server.
"""
import time
import requests
from redis_client import get_car_location

def demo():
    print("\n" + "="*70)
    print("REAL-TIME POLICE CAR TRACKING - LIVE DEMO")
    print("="*70 + "\n")
    
    BASE_URL = "http://localhost:8000"
    car_id = "DEMO-001"
    
    # Step 1: Create a car
    print("Step 1: Creating police car...")
    response = requests.post(f"{BASE_URL}/police/cars", json={
        "car_id": car_id,
        "car_model": "Ford Explorer Demo Unit",
        "officer_name": "Demo Officer",
        "officer_badge": "DEMO123",
        "location": {"lat": 33.7490, "lng": -84.3880, "address": "Atlanta, GA"}
    })
    
    if response.status_code == 200:
        print(f"✅ Created car: {car_id}\n")
    else:
        print(f"❌ Error creating car: {response.text}\n")
        return
    
    # Step 2: Add to simulator
    print("Step 2: Adding car to simulator...")
    response = requests.post(f"{BASE_URL}/simulator/add/{car_id}?lat=33.7490&lng=-84.3880")
    
    if response.status_code == 200:
        print(f"✅ Car added to simulator (will move every 1 second)\n")
    else:
        print(f"⚠️  Could not add to simulator: {response.text}\n")
    
    # Step 3: Watch real-time updates
    print("Step 3: Watching real-time position updates...")
    print("(Position is updated every 1 second in Redis)\n")
    print("-" * 70)
    
    for i in range(10):
        time.sleep(1)
        
        # Get from Redis (real-time, 1-second updates)
        location = get_car_location(car_id)
        
        if location:
            print(f"Update {i+1}/10:")
            print(f"  📍 Position: ({location['lat']:.6f}, {location['lng']:.6f})")
            print(f"  🚗 Speed: {location.get('speed', 0):.1f} mph")
            print(f"  🧭 Heading: {location.get('heading', 0):.1f}°")
            print(f"  ⏰ Time: {location.get('timestamp', 'N/A')}")
            print()
        else:
            print(f"Update {i+1}/10: ⏳ Waiting for position data...")
            print()
    
    print("-" * 70)
    
    # Step 4: Check MongoDB (should be synced after 10 seconds)
    print("\nStep 4: Checking MongoDB (synced every 10 seconds)...")
    time.sleep(1)
    
    response = requests.get(f"{BASE_URL}/police/cars/{car_id}")
    
    if response.status_code == 200:
        data = response.json()
        mongo_location = data.get('car', {}).get('location', {})
        print(f"✅ MongoDB has been synced:")
        print(f"  Position: ({mongo_location.get('lat')}, {mongo_location.get('lng')})")
        print(f"  Address: {mongo_location.get('address', 'N/A')}\n")
    else:
        print(f"⚠️  Could not fetch from MongoDB: {response.text}\n")
    
    # Step 5: Find nearby cars
    print("Step 5: Finding nearby cars...")
    response = requests.post(f"{BASE_URL}/police/nearby", json={
        "lat": 33.7490,
        "lng": -84.3880,
        "radius_km": 10.0
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['count']} car(s) within 10km:")
        
        for car in data['cars']:
            print(f"  • {car['car_id']}: {car['distance_km']}km away")
        print()
    else:
        print(f"⚠️  Could not search nearby: {response.text}\n")
    
    # Step 6: Check stats
    print("Step 6: System statistics...")
    response = requests.get(f"{BASE_URL}/stats")
    
    if response.status_code == 200:
        stats = response.json()
        sync_stats = stats.get('sync_service', {})
        sim_stats = stats.get('simulator', {})
        
        print(f"✅ Sync Service:")
        print(f"  Total syncs: {sync_stats.get('total_syncs', 0)}")
        print(f"  Successful: {sync_stats.get('successful_updates', 0)}")
        print(f"  Failed: {sync_stats.get('failed_updates', 0)}")
        print(f"  Last sync: {sync_stats.get('last_sync', 'Never')}")
        print()
        print(f"✅ Simulator:")
        print(f"  Active cars: {sim_stats.get('active_cars', 0)}")
        print(f"  Cars: {', '.join(sim_stats.get('cars', []))}")
        print()
    
    # Step 7: Cleanup
    print("Step 7: Cleanup (removing demo car)...")
    requests.delete(f"{BASE_URL}/simulator/remove/{car_id}")
    requests.delete(f"{BASE_URL}/police/cars/{car_id}")
    print("✅ Demo car removed\n")
    
    print("="*70)
    print("DEMO COMPLETE!")
    print("="*70)
    print("\nWhat just happened:")
    print("1. ✅ Created a police car in MongoDB")
    print("2. ✅ Added it to the simulator")
    print("3. ✅ Watched it move in real-time (Redis, 1s updates)")
    print("4. ✅ Verified MongoDB sync (10s interval)")
    print("5. ✅ Found nearby cars using distance calculation")
    print("6. ✅ Checked system statistics")
    print("\nNext: Connect your frontend to WebSocket for live tracking!")
    print("  → ws://localhost:8000/ws/track/PC-001")
    print()

if __name__ == "__main__":
    try:
        demo()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to FastAPI server")
        print("Make sure the server is running:")
        print("  → uvicorn api:app --reload")
        print()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print()
