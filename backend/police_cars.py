"""
Police Cars Management Module
Handles tracking and management of police cars, their officers, and dispatch status.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from db import client

db = client["dispatch_db"]
police_cars_collection = db["police_cars"]

class PoliceCarStatus:
    """Status constants for police cars"""
    INACTIVE = "inactive"
    DISPATCHED = "dispatched"
    EN_ROUTE = "en_route"
    ON_SCENE = "on_scene"
    RETURNING = "returning"

class PoliceCar:
    """Police Car data model"""
    
    @staticmethod
    def create_police_car(
        car_id: str,
        car_model: str,
        officer_name: str,
        officer_badge: str,
        officer_rank: str = "Officer",
        unit_number: str = None,
        location: Dict[str, Any] = None,
        status: str = PoliceCarStatus.INACTIVE
    ) -> str:
        """
        Create a new police car entry in the database.
        
        Args:
            car_id: Unique identifier for the car (e.g., "CAR-001")
            car_model: Model of the car (e.g., "Ford Explorer Police Interceptor")
            officer_name: Full name of the officer
            officer_badge: Badge number
            officer_rank: Rank of the officer (default: "Officer")
            unit_number: Police unit number (default: None, auto-generated)
            location: Current location {lat, lng, address}
            status: Current status (default: inactive)
            
        Returns:
            str: The inserted document's ID
        """
        if unit_number is None:
            unit_number = car_id
        
        police_car = {
            "car_id": car_id,
            "car_model": car_model,
            "unit_number": unit_number,
            "officer": {
                "name": officer_name,
                "badge": officer_badge,
                "rank": officer_rank
            },
            "status": status,
            "incident_id": None,
            "location": location or {"lat": None, "lng": None, "address": "Unknown"},
            "created_at": datetime.utcnow(),
            "last_updated": datetime.utcnow(),
            "dispatch_history": []
        }
        
        result = police_cars_collection.insert_one(police_car)
        return str(result.inserted_id)
    
    @staticmethod
    def get_police_car(car_id: str = None, _id: str = None) -> Optional[Dict[str, Any]]:
        """
        Get a police car by car_id or MongoDB _id.
        
        Args:
            car_id: The car's unique identifier
            _id: The MongoDB document ID
            
        Returns:
            dict or None: The police car document
        """
        if _id:
            try:
                return police_cars_collection.find_one({"_id": ObjectId(_id)})
            except:
                return None
        elif car_id:
            return police_cars_collection.find_one({"car_id": car_id})
        return None
    
    @staticmethod
    def get_all_police_cars(status: str = None) -> List[Dict[str, Any]]:
        """
        Get all police cars, optionally filtered by status.
        
        Args:
            status: Filter by status (optional)
            
        Returns:
            list: List of police car documents
        """
        query = {"status": status} if status else {}
        return list(police_cars_collection.find(query))
    
    @staticmethod
    def dispatch_police_car(
        car_id: str,
        incident_id: str,
        dispatch_location: Dict[str, Any] = None
    ) -> bool:
        """
        Dispatch a police car to an incident.
        
        Args:
            car_id: The car's unique identifier
            incident_id: The incident to dispatch to
            dispatch_location: Location details of the incident
            
        Returns:
            bool: True if successful, False otherwise
        """
        car = PoliceCar.get_police_car(car_id=car_id)
        if not car:
            return False
        
        # Create dispatch record
        dispatch_record = {
            "incident_id": incident_id,
            "dispatched_at": datetime.utcnow(),
            "location": dispatch_location,
            "concluded_at": None
        }
        
        # Update police car
        result = police_cars_collection.update_one(
            {"car_id": car_id},
            {
                "$set": {
                    "status": PoliceCarStatus.DISPATCHED,
                    "incident_id": incident_id,
                    "last_updated": datetime.utcnow()
                },
                "$push": {
                    "dispatch_history": dispatch_record
                }
            }
        )
        
        return result.modified_count > 0
    
    @staticmethod
    def update_car_status(
        car_id: str,
        status: str,
        location: Dict[str, Any] = None
    ) -> bool:
        """
        Update the status of a police car.
        
        Args:
            car_id: The car's unique identifier
            status: New status
            location: Updated location (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        update_data = {
            "status": status,
            "last_updated": datetime.utcnow()
        }
        
        if location:
            update_data["location"] = location
        
        result = police_cars_collection.update_one(
            {"car_id": car_id},
            {"$set": update_data}
        )
        
        return result.modified_count > 0
    
    @staticmethod
    def conclude_dispatch(car_id: str) -> bool:
        """
        Mark a police car as no longer dispatched (returns to inactive).
        Updates the most recent dispatch record.
        
        Args:
            car_id: The car's unique identifier
            
        Returns:
            bool: True if successful, False otherwise
        """
        car = PoliceCar.get_police_car(car_id=car_id)
        if not car:
            return False
        
        # Update the most recent dispatch record
        if car.get("dispatch_history"):
            police_cars_collection.update_one(
                {
                    "car_id": car_id,
                    "dispatch_history.concluded_at": None
                },
                {
                    "$set": {
                        "dispatch_history.$[elem].concluded_at": datetime.utcnow()
                    }
                },
                array_filters=[{"elem.concluded_at": None}]
            )
        
        # Set car back to inactive
        result = police_cars_collection.update_one(
            {"car_id": car_id},
            {
                "$set": {
                    "status": PoliceCarStatus.INACTIVE,
                    "incident_id": None,
                    "last_updated": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
    
    @staticmethod
    def get_available_cars() -> List[Dict[str, Any]]:
        """
        Get all available (inactive) police cars.
        
        Returns:
            list: List of available police car documents
        """
        return PoliceCar.get_all_police_cars(status=PoliceCarStatus.INACTIVE)
    
    @staticmethod
    def get_cars_for_incident(incident_id: str) -> List[Dict[str, Any]]:
        """
        Get all police cars dispatched to a specific incident.
        
        Args:
            incident_id: The incident ID
            
        Returns:
            list: List of police car documents
        """
        return list(police_cars_collection.find({"incident_id": incident_id}))
    
    @staticmethod
    def update_car_location(
        car_id: str,
        lat: float,
        lng: float,
        address: str = None
    ) -> bool:
        """
        Update the current location of a police car.
        
        Args:
            car_id: The car's unique identifier
            lat: Latitude
            lng: Longitude
            address: Address text (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        location = {
            "lat": lat,
            "lng": lng,
            "address": address or "Unknown",
            "updated_at": datetime.utcnow()
        }
        
        return PoliceCar.update_car_status(car_id, None, location)
    
    @staticmethod
    def delete_police_car(car_id: str) -> bool:
        """
        Delete a police car from the database and Redis.
        This ensures complete cleanup across all systems.
        
        Args:
            car_id: The car's unique identifier
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Delete from MongoDB
            result = police_cars_collection.delete_one({"car_id": car_id})
            
            # Also delete from Redis to ensure clean state
            if result.deleted_count > 0:
                # Lazy import to avoid circular dependency
                from redis_tracking.redis_client import delete_car_location
                delete_car_location(car_id)
                print(f"🗑️ Deleted {car_id} from MongoDB and Redis")
                return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting police car {car_id}: {e}")
            return False


# Helper functions for easy access
def create_car(car_id: str, car_model: str, officer_name: str, 
               officer_badge: str, **kwargs) -> str:
    """Convenience function to create a police car"""
    return PoliceCar.create_police_car(
        car_id, car_model, officer_name, officer_badge, **kwargs
    )

def get_car(car_id: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get a police car"""
    return PoliceCar.get_police_car(car_id=car_id)

def dispatch_car(car_id: str, incident_id: str, 
                 dispatch_location: Dict[str, Any] = None) -> bool:
    """Convenience function to dispatch a police car"""
    return PoliceCar.dispatch_police_car(car_id, incident_id, dispatch_location)

def conclude_car_dispatch(car_id: str) -> bool:
    """Convenience function to conclude a dispatch"""
    return PoliceCar.conclude_dispatch(car_id)

def get_available_cars() -> List[Dict[str, Any]]:
    """Convenience function to get available cars"""
    return PoliceCar.get_available_cars()

def get_dispatched_cars(incident_id: str) -> List[Dict[str, Any]]:
    """Convenience function to get cars for an incident"""
    return PoliceCar.get_cars_for_incident(incident_id)
