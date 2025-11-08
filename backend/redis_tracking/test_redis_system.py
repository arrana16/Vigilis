"""
Quick test script to verify the Redis real-time tracking system is working.
"""
import asyncio
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redis_tracking.redis_client import test_redis_connection, update_car_location, get_car_location, get_all_car_locations, get_nearby_cars
from redis_tracking.car_simulator import CarSimulator

def test_redis_basic():
    """Test basic Redis connection"""
    print("=" * 60)
    print("TEST 1: Redis Connection")
    print("=" * 60)
    
    if test_redis_connection():
        print("✅ Redis connection successful\n")
        return True
    else:
        print("❌ Redis connection failed\n")
        return False

def test_location_updates():
    """Test updating and retrieving car locations"""
    print("=" * 60)
    print("TEST 2: Location Updates")
    print("=" * 60)
    
    car_id = "TEST-001"
    
    # Update location
    print(f"Updating location for {car_id}...")
    success = update_car_location(
        car_id=car_id,
        lat=33.7490,
        lng=-84.3880,
        speed=45.5,
        heading=270.0
    )
    
    if success:
        print("✅ Location update successful")
    else:
        print("❌ Location update failed")
        return False
    
    # Retrieve location
    print(f"Retrieving location for {car_id}...")
    location = get_car_location(car_id)
    
    if location:
        print(f"✅ Location retrieved:")
        print(f"   Lat: {location['lat']}")
        print(f"   Lng: {location['lng']}")
        print(f"   Speed: {location['speed']} mph")
        print(f"   Heading: {location['heading']}°")
        print(f"   Timestamp: {location['timestamp']}\n")
        return True
    else:
        print("❌ Location retrieval failed\n")
        return False

def test_all_locations():
    """Test retrieving all car locations"""
    print("=" * 60)
    print("TEST 3: All Locations")
    print("=" * 60)
    
    # Add multiple test cars
    test_cars = [
        ("TEST-001", 33.7490, -84.3880),
        ("TEST-002", 33.7500, -84.3900),
        ("TEST-003", 33.7510, -84.3920),
    ]
    
    for car_id, lat, lng in test_cars:
        update_car_location(car_id, lat, lng, speed=30.0, heading=180.0)
    
    # Retrieve all
    all_locations = get_all_car_locations()
    
    print(f"✅ Found {len(all_locations)} car(s) in Redis:")
    for loc in all_locations:
        print(f"   - {loc['car_id']}: ({loc['lat']}, {loc['lng']})")
    
    print()
    return True

def test_nearby_search():
    """Test finding nearby cars"""
    print("=" * 60)
    print("TEST 4: Nearby Search")
    print("=" * 60)
    
    # Search center point
    center_lat = 33.7490
    center_lng = -84.3880
    radius = 5.0
    
    print(f"Searching for cars within {radius}km of ({center_lat}, {center_lng})...")
    nearby = get_nearby_cars(center_lat, center_lng, radius)
    
    print(f"✅ Found {len(nearby)} nearby car(s):")
    for car in nearby:
        print(f"   - {car['car_id']}: {car['distance_km']}km away")
    
    print()
    return True

async def test_simulator():
    """Test the car simulator"""
    print("=" * 60)
    print("TEST 5: Car Simulator")
    print("=" * 60)
    
    simulator = CarSimulator(update_interval=1.0)
    
    # Add test cars
    simulator.add_car("SIM-001", 33.7490, -84.3880)
    simulator.add_car("SIM-002", 33.7500, -84.3900)
    
    print("Running simulator for 5 seconds...")
    
    # Run for 5 iterations
    for i in range(5):
        await simulator.update_car_position("SIM-001")
        await simulator.update_car_position("SIM-002")
        
        # Check Redis for updated positions
        loc1 = get_car_location("SIM-001")
        loc2 = get_car_location("SIM-002")
        
        print(f"  Iteration {i+1}:")
        if loc1:
            print(f"    SIM-001: ({loc1['lat']:.5f}, {loc1['lng']:.5f}) @ {loc1['speed']:.1f}mph")
        if loc2:
            print(f"    SIM-002: ({loc2['lat']:.5f}, {loc2['lng']:.5f}) @ {loc2['speed']:.1f}mph")
        
        await asyncio.sleep(1)
    
    print("✅ Simulator test complete\n")
    return True

def cleanup():
    """Clean up test data"""
    print("=" * 60)
    print("Cleanup")
    print("=" * 60)
    
    from redis_client import delete_car_location
    
    test_car_ids = ["TEST-001", "TEST-002", "TEST-003", "SIM-001", "SIM-002"]
    
    for car_id in test_car_ids:
        delete_car_location(car_id)
        print(f"Deleted: {car_id}")
    
    print("✅ Cleanup complete\n")

async def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("REDIS REAL-TIME TRACKING SYSTEM - TEST SUITE")
    print("=" * 60 + "\n")
    
    results = []
    
    # Test 1: Redis connection
    results.append(("Redis Connection", test_redis_basic()))
    
    if not results[0][1]:
        print("❌ Cannot proceed without Redis connection")
        return
    
    # Test 2: Location updates
    results.append(("Location Updates", test_location_updates()))
    
    # Test 3: All locations
    results.append(("All Locations", test_all_locations()))
    
    # Test 4: Nearby search
    results.append(("Nearby Search", test_nearby_search()))
    
    # Test 5: Simulator
    results.append(("Car Simulator", await test_simulator()))
    
    # Cleanup
    cleanup()
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! System is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the output above.")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
