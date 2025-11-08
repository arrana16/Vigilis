"""
Simulates realistic police car movement for testing.
Moves cars along random paths with realistic speeds and behaviors.
"""
import asyncio
import random
import math
from datetime import datetime
from typing import List, Dict, Any, Tuple
from .redis_client import update_car_location
from police_cars import PoliceCar

class CarSimulator:
    def __init__(self, update_interval: float = 1.0):
        """
        Initialize the car simulator.
        
        Args:
            update_interval: How often to update positions (in seconds), default 1.0
        """
        self.update_interval = update_interval
        self.running = False
        self.simulated_cars = {}  # car_id -> simulation state
        
        # Atlanta area bounds (roughly downtown to suburbs)
        self.bounds = {
            "min_lat": 33.6490,
            "max_lat": 33.8490,
            "min_lng": -84.5880,
            "max_lng": -84.2880
        }
    
    def generate_random_waypoint(self) -> Tuple[float, float]:
        """Generate a random waypoint within Atlanta bounds"""
        lat = random.uniform(self.bounds["min_lat"], self.bounds["max_lat"])
        lng = random.uniform(self.bounds["min_lng"], self.bounds["max_lng"])
        return lat, lng
    
    def calculate_bearing(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate bearing between two points in degrees"""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lng = math.radians(lng2 - lng1)
        
        x = math.sin(delta_lng) * math.cos(lat2_rad)
        y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lng)
        
        bearing = math.degrees(math.atan2(x, y))
        return (bearing + 360) % 360
    
    def move_towards(self, current_lat: float, current_lng: float, 
                     target_lat: float, target_lng: float, 
                     speed_kmh: float) -> Tuple[float, float, float]:
        """
        Move a car towards a target at a given speed.
        
        Returns:
            (new_lat, new_lng, distance_remaining_km)
        """
        # Calculate distance using Haversine
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(current_lat)
        lat2_rad = math.radians(target_lat)
        delta_lat = math.radians(target_lat - current_lat)
        delta_lng = math.radians(target_lng - current_lng)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        distance_km = R * c
        
        # Calculate how far we can move in this interval
        distance_to_move = (speed_kmh / 3600) * self.update_interval  # Convert to km per interval
        
        if distance_to_move >= distance_km:
            # We'll reach the target this interval
            return target_lat, target_lng, 0.0
        
        # Calculate new position
        fraction = distance_to_move / distance_km
        new_lat = current_lat + (target_lat - current_lat) * fraction
        new_lng = current_lng + (target_lng - current_lng) * fraction
        
        return new_lat, new_lng, distance_km - distance_to_move
    
    def add_car(self, car_id: str, start_lat: float = None, start_lng: float = None):
        """Add a car to the simulator"""
        if start_lat is None or start_lng is None:
            start_lat, start_lng = self.generate_random_waypoint()
        
        target_lat, target_lng = self.generate_random_waypoint()
        
        # Random speed between 20-60 mph (patrol speed)
        speed_mph = random.uniform(20, 60)
        speed_kmh = speed_mph * 1.60934
        
        self.simulated_cars[car_id] = {
            "current_lat": start_lat,
            "current_lng": start_lng,
            "target_lat": target_lat,
            "target_lng": target_lng,
            "speed_mph": speed_mph,
            "speed_kmh": speed_kmh,
            "status": "patrolling"
        }
        
        print(f"🚓 Added {car_id} to simulator at ({start_lat:.4f}, {start_lng:.4f}), "
              f"heading to ({target_lat:.4f}, {target_lng:.4f}) at {speed_mph:.1f} mph")
    
    def remove_car(self, car_id: str):
        """Remove a car from the simulator"""
        if car_id in self.simulated_cars:
            del self.simulated_cars[car_id]
            print(f"Removed {car_id} from simulator")
    
    async def update_car_position(self, car_id: str):
        """Update a single car's position"""
        if car_id not in self.simulated_cars:
            return
        
        car = self.simulated_cars[car_id]
        
        # Move towards target
        new_lat, new_lng, distance_remaining = self.move_towards(
            car["current_lat"], car["current_lng"],
            car["target_lat"], car["target_lng"],
            car["speed_kmh"]
        )
        
        # Calculate heading
        heading = self.calculate_bearing(
            car["current_lat"], car["current_lng"],
            new_lat, new_lng
        )
        
        # Update position
        car["current_lat"] = new_lat
        car["current_lng"] = new_lng
        
        # If we reached the target, generate a new one
        if distance_remaining < 0.01:  # Less than 10 meters
            car["target_lat"], car["target_lng"] = self.generate_random_waypoint()
            # Randomly change speed
            car["speed_mph"] = random.uniform(20, 60)
            car["speed_kmh"] = car["speed_mph"] * 1.60934
            
            print(f"🎯 {car_id} reached waypoint, new target: "
                  f"({car['target_lat']:.4f}, {car['target_lng']:.4f}) at {car['speed_mph']:.1f} mph")
        
        # Update Redis with new position
        update_car_location(
            car_id=car_id,
            lat=new_lat,
            lng=new_lng,
            speed=car["speed_mph"],
            heading=heading,
            timestamp=datetime.utcnow().isoformat()
        )
    
    async def simulate(self):
        """Main simulation loop"""
        while self.running:
            # Update all cars
            for car_id in list(self.simulated_cars.keys()):
                await self.update_car_position(car_id)
            
            await asyncio.sleep(self.update_interval)
    
    async def start(self):
        """Start the simulator"""
        self.running = True
        print(f"🎮 Car simulator started (update interval: {self.update_interval}s)")
        await self.simulate()
    
    def stop(self):
        """Stop the simulator"""
        self.running = False
        print("🛑 Car simulator stopped")
    
    def auto_add_cars_from_db(self):
        """Automatically add all active/dispatched cars from MongoDB to simulator"""
        try:
            # Get all cars that aren't inactive
            cars = PoliceCar.get_all_police_cars()
            
            for car in cars:
                if car.get("status") != "inactive":
                    car_id = car.get("car_id")
                    location = car.get("location", {})
                    
                    if car_id and location:
                        self.add_car(
                            car_id=car_id,
                            start_lat=location.get("lat"),
                            start_lng=location.get("lng")
                        )
            
            print(f"✅ Added {len(self.simulated_cars)} cars from database to simulator")
            
        except Exception as e:
            print(f"Error auto-adding cars: {e}")

# Global instance
car_simulator = CarSimulator(update_interval=1.0)

async def start_car_simulator(auto_add_from_db: bool = True):
    """Start the car simulator"""
    if auto_add_from_db:
        car_simulator.auto_add_cars_from_db()
    
    await car_simulator.start()

def add_simulated_car(car_id: str, lat: float = None, lng: float = None):
    """Add a car to the simulator"""
    car_simulator.add_car(car_id, lat, lng)

def remove_simulated_car(car_id: str):
    """Remove a car from the simulator"""
    car_simulator.remove_car(car_id)

if __name__ == "__main__":
    # Test the simulator
    print("Starting car simulator...")
    
    # Add a few test cars
    car_simulator.add_car("PC-001")
    car_simulator.add_car("PC-002")
    car_simulator.add_car("PC-003")
    
    # Run the simulator
    asyncio.run(car_simulator.start())
