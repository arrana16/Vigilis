"""
Example script demonstrating how to use the Police Cars system.
Run this after starting the FastAPI server to test the functionality.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def print_response(response):
    """Pretty print API response"""
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print("-" * 80)

def example_usage():
    """Demonstrate the police car management workflow"""
    
    print("=" * 80)
    print("POLICE CAR MANAGEMENT EXAMPLE")
    print("=" * 80)
    
    # 1. Create police cars
    print("\n1. Creating police cars...")
    print("-" * 80)
    
    cars_to_create = [
        {
            "car_id": "CAR-001",
            "car_model": "Ford Explorer Police Interceptor",
            "officer_name": "John Smith",
            "officer_badge": "B-1234",
            "officer_rank": "Sergeant",
            "unit_number": "UNIT-101",
            "location": {
                "lat": 33.7490,
                "lng": -84.3880,
                "address": "Downtown Atlanta, GA"
            }
        },
        {
            "car_id": "CAR-002",
            "car_model": "Chevrolet Tahoe Police Package",
            "officer_name": "Jane Doe",
            "officer_badge": "B-5678",
            "officer_rank": "Officer",
            "unit_number": "UNIT-102",
            "location": {
                "lat": 33.7550,
                "lng": -84.3900,
                "address": "Midtown Atlanta, GA"
            }
        },
        {
            "car_id": "CAR-003",
            "car_model": "Dodge Charger Pursuit",
            "officer_name": "Mike Johnson",
            "officer_badge": "B-9012",
            "officer_rank": "Officer",
            "unit_number": "UNIT-103",
            "location": {
                "lat": 33.7600,
                "lng": -84.3950,
                "address": "Buckhead, Atlanta, GA"
            }
        }
    ]
    
    for car in cars_to_create:
        response = requests.post(f"{BASE_URL}/police/cars", json=car)
        print(f"Creating {car['car_id']}...")
        print_response(response)
    
    # 2. Get all police cars
    print("\n2. Getting all police cars...")
    print("-" * 80)
    response = requests.get(f"{BASE_URL}/police/cars")
    print_response(response)
    
    # 3. Get available cars
    print("\n3. Getting available (inactive) cars...")
    print("-" * 80)
    response = requests.get(f"{BASE_URL}/police/available")
    print_response(response)
    
    # 4. Dispatch a car to an incident
    print("\n4. Dispatching CAR-001 to incident INC-12345...")
    print("-" * 80)
    dispatch_data = {
        "car_id": "CAR-001",
        "incident_id": "INC-12345",
        "dispatch_location": {
            "lat": 33.7700,
            "lng": -84.4000,
            "address": "Emergency Location, Atlanta, GA"
        }
    }
    response = requests.post(f"{BASE_URL}/police/dispatch", json=dispatch_data)
    print_response(response)
    
    # 5. Get a specific car
    print("\n5. Getting details for CAR-001...")
    print("-" * 80)
    response = requests.get(f"{BASE_URL}/police/cars/CAR-001")
    print_response(response)
    
    # 6. Update car status
    print("\n6. Updating CAR-001 status to 'en_route'...")
    print("-" * 80)
    status_data = {
        "car_id": "CAR-001",
        "status": "en_route"
    }
    response = requests.put(f"{BASE_URL}/police/status", json=status_data)
    print_response(response)
    
    # 7. Update car location
    print("\n7. Updating CAR-001 location...")
    print("-" * 80)
    location_data = {
        "car_id": "CAR-001",
        "lat": 33.7650,
        "lng": -84.3920,
        "address": "En route to incident"
    }
    response = requests.put(f"{BASE_URL}/police/location", json=location_data)
    print_response(response)
    
    # 8. Get cars for specific incident
    print("\n8. Getting all cars dispatched to INC-12345...")
    print("-" * 80)
    response = requests.get(f"{BASE_URL}/police/incident/INC-12345")
    print_response(response)
    
    # 9. Update status to on_scene
    print("\n9. Updating CAR-001 status to 'on_scene'...")
    print("-" * 80)
    status_data = {
        "car_id": "CAR-001",
        "status": "on_scene"
    }
    response = requests.put(f"{BASE_URL}/police/status", json=status_data)
    print_response(response)
    
    # 10. Get dispatched cars (filter by status)
    print("\n10. Getting all dispatched cars...")
    print("-" * 80)
    response = requests.get(f"{BASE_URL}/police/cars?status=on_scene")
    print_response(response)
    
    # 11. Conclude dispatch
    print("\n11. Concluding dispatch for CAR-001...")
    print("-" * 80)
    conclude_data = {
        "car_id": "CAR-001"
    }
    response = requests.post(f"{BASE_URL}/police/conclude", json=conclude_data)
    print_response(response)
    
    # 12. Verify car is back to inactive
    print("\n12. Verifying CAR-001 is back to inactive...")
    print("-" * 80)
    response = requests.get(f"{BASE_URL}/police/cars/CAR-001")
    print_response(response)
    
    # 13. Get available cars again
    print("\n13. Getting available cars (should include CAR-001 now)...")
    print("-" * 80)
    response = requests.get(f"{BASE_URL}/police/available")
    print_response(response)
    
    print("\n" + "=" * 80)
    print("EXAMPLE COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    try:
        example_usage()
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to API server.")
        print("Make sure the FastAPI server is running on http://localhost:8000")
        print("\nStart the server with:")
        print("  uvicorn backend.api:app --reload")
    except Exception as e:
        print(f"ERROR: {e}")
