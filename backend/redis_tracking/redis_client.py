"""
Redis client for real-time police car location tracking.
Stores high-frequency position updates in Redis.
"""
import redis
import json
import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Create Redis client
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    db=REDIS_DB,
    decode_responses=True  # Automatically decode responses to strings
)

def get_car_location(car_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the current location of a car from Redis.
    
    Args:
        car_id: The unique identifier for the car
        
    Returns:
        Dictionary with location data or None if not found
    """
    try:
        location_data = redis_client.get(f"car:location:{car_id}")
        if location_data:
            return json.loads(location_data)
        return None
    except Exception as e:
        print(f"Error getting car location from Redis: {e}")
        return None

def update_car_location(car_id: str, lat: float, lng: float, 
                       speed: Optional[float] = None, 
                       heading: Optional[float] = None,
                       timestamp: Optional[str] = None) -> bool:
    """
    Update a car's location in Redis with high-frequency updates.
    
    Args:
        car_id: The unique identifier for the car
        lat: Latitude
        lng: Longitude
        speed: Speed in mph (optional)
        heading: Heading in degrees (optional)
        timestamp: ISO timestamp (optional, will use current time if not provided)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from datetime import datetime
        
        location_data = {
            "car_id": car_id,
            "lat": lat,
            "lng": lng,
            "speed": speed,
            "heading": heading,
            "timestamp": timestamp or datetime.utcnow().isoformat()
        }
        
        # Store in Redis with a key like "car:location:PC-001"
        redis_client.set(
            f"car:location:{car_id}",
            json.dumps(location_data),
            ex=300  # Expire after 5 minutes of no updates
        )
        
        # Also publish to Redis pub/sub channel for WebSocket subscribers
        redis_client.publish(
            f"car:location:stream:{car_id}",
            json.dumps(location_data)
        )
        
        return True
    except Exception as e:
        print(f"Error updating car location in Redis: {e}")
        return False

def get_all_car_locations() -> List[Dict[str, Any]]:
    """
    Get all car locations from Redis.
    
    Returns:
        List of location dictionaries
    """
    try:
        locations = []
        # Get all keys matching the pattern
        keys = redis_client.keys("car:location:*")
        
        for key in keys:
            location_data = redis_client.get(key)
            if location_data:
                locations.append(json.loads(location_data))
        
        return locations
    except Exception as e:
        print(f"Error getting all car locations from Redis: {e}")
        return []

def delete_car_location(car_id: str) -> bool:
    """
    Delete a car's location from Redis.
    
    Args:
        car_id: The unique identifier for the car
        
    Returns:
        True if successful, False otherwise
    """
    try:
        redis_client.delete(f"car:location:{car_id}")
        return True
    except Exception as e:
        print(f"Error deleting car location from Redis: {e}")
        return False

def get_nearby_cars(lat: float, lng: float, radius_km: float = 5.0) -> List[Dict[str, Any]]:
    """
    Get cars within a certain radius of a location.
    Uses the Haversine formula to calculate distance.
    
    Args:
        lat: Center latitude
        lng: Center longitude
        radius_km: Radius in kilometers (default 5km)
        
    Returns:
        List of nearby cars with their locations and distances
    """
    import math
    
    def haversine_distance(lat1, lon1, lat2, lon2):
        """Calculate distance between two points in kilometers"""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    try:
        all_locations = get_all_car_locations()
        nearby = []
        
        for location in all_locations:
            distance = haversine_distance(
                lat, lng,
                location["lat"], location["lng"]
            )
            
            if distance <= radius_km:
                location["distance_km"] = round(distance, 2)
                nearby.append(location)
        
        # Sort by distance (closest first)
        nearby.sort(key=lambda x: x["distance_km"])
        
        return nearby
    except Exception as e:
        print(f"Error getting nearby cars: {e}")
        return []

def test_redis_connection():
    """Test if Redis connection is working"""
    try:
        redis_client.ping()
        print("✅ Successfully connected to Redis!")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

if __name__ == "__main__":
    # Test the connection
    test_redis_connection()
