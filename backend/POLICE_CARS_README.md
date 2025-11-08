# Police Cars Management System

## Overview

The Police Cars Management System tracks the state, location, and dispatch status of police vehicles in the Vigilis emergency response platform. Each police car maintains information about its assigned officer, current status, and dispatch history.

## Database Schema

### Collection: `police_cars`

```json
{
  "_id": ObjectId("..."),
  "car_id": "CAR-001",
  "car_model": "Ford Explorer Police Interceptor",
  "unit_number": "UNIT-101",
  "officer": {
    "name": "John Smith",
    "badge": "B-1234",
    "rank": "Sergeant"
  },
  "status": "inactive",
  "incident_id": null,
  "location": {
    "lat": 33.7490,
    "lng": -84.3880,
    "address": "Downtown Atlanta, GA",
    "updated_at": "2024-11-08T12:00:00Z"
  },
  "created_at": "2024-11-08T10:00:00Z",
  "last_updated": "2024-11-08T12:00:00Z",
  "dispatch_history": [
    {
      "incident_id": "INC-12345",
      "dispatched_at": "2024-11-08T11:00:00Z",
      "location": {
        "lat": 33.7700,
        "lng": -84.4000,
        "address": "Emergency Location, Atlanta, GA"
      },
      "concluded_at": "2024-11-08T11:45:00Z"
    }
  ]
}
```

## Status Types

-   `inactive` - Car is available and not currently dispatched
-   `dispatched` - Car has been assigned to an incident
-   `en_route` - Car is traveling to the incident location
-   `on_scene` - Car has arrived at the incident location
-   `returning` - Car is returning from the incident

## API Endpoints

### 1. Create Police Car

**POST** `/police/cars`

Creates a new police car in the database.

```json
{
	"car_id": "CAR-001",
	"car_model": "Ford Explorer Police Interceptor",
	"officer_name": "John Smith",
	"officer_badge": "B-1234",
	"officer_rank": "Sergeant",
	"unit_number": "UNIT-101",
	"location": {
		"lat": 33.749,
		"lng": -84.388,
		"address": "Downtown Atlanta, GA"
	}
}
```

### 2. Get All Police Cars

**GET** `/police/cars?status={status}`

Retrieves all police cars, optionally filtered by status.

Query Parameters:

-   `status` (optional): Filter by status (inactive, dispatched, en_route, on_scene, returning)

### 3. Get Specific Police Car

**GET** `/police/cars/{car_id}`

Retrieves details for a specific police car.

### 4. Dispatch Police Car

**POST** `/police/dispatch`

Dispatches a police car to an incident.

```json
{
	"car_id": "CAR-001",
	"incident_id": "INC-12345",
	"dispatch_location": {
		"lat": 33.77,
		"lng": -84.4,
		"address": "Emergency Location, Atlanta, GA"
	}
}
```

### 5. Update Car Status

**PUT** `/police/status`

Updates the status of a police car.

```json
{
	"car_id": "CAR-001",
	"status": "en_route",
	"location": {
		"lat": 33.76,
		"lng": -84.39,
		"address": "On route"
	}
}
```

### 6. Update Car Location

**PUT** `/police/location`

Updates the current location of a police car.

```json
{
	"car_id": "CAR-001",
	"lat": 33.765,
	"lng": -84.392,
	"address": "En route to incident"
}
```

### 7. Conclude Dispatch

**POST** `/police/conclude`

Concludes a dispatch and returns the car to inactive status.

```json
{
	"car_id": "CAR-001"
}
```

### 8. Get Available Cars

**GET** `/police/available`

Retrieves all available (inactive) police cars.

### 9. Get Cars for Incident

**GET** `/police/incident/{incident_id}`

Retrieves all police cars dispatched to a specific incident.

### 10. Delete Police Car

**DELETE** `/police/cars/{car_id}`

Deletes a police car from the database.

## Python Usage Examples

### Using the Module Directly

```python
from police_cars import (
    create_car,
    get_car,
    dispatch_car,
    conclude_car_dispatch,
    get_available_cars,
    PoliceCar
)

# Create a new police car
car_id = create_car(
    car_id="CAR-001",
    car_model="Ford Explorer Police Interceptor",
    officer_name="John Smith",
    officer_badge="B-1234",
    officer_rank="Sergeant",
    unit_number="UNIT-101",
    location={
        "lat": 33.7490,
        "lng": -84.3880,
        "address": "Downtown Atlanta, GA"
    }
)

# Get available cars
available = get_available_cars()
print(f"Available cars: {len(available)}")

# Dispatch a car
success = dispatch_car(
    car_id="CAR-001",
    incident_id="INC-12345",
    dispatch_location={
        "lat": 33.7700,
        "lng": -84.4000,
        "address": "Emergency Location"
    }
)

# Update car status
PoliceCar.update_car_status("CAR-001", "en_route")

# Update location
PoliceCar.update_car_location(
    car_id="CAR-001",
    lat=33.7650,
    lng=-84.3920,
    address="En route"
)

# Conclude dispatch
conclude_car_dispatch("CAR-001")
```

### Using the API

```python
import requests

BASE_URL = "http://localhost:8000"

# Create a car
response = requests.post(f"{BASE_URL}/police/cars", json={
    "car_id": "CAR-001",
    "car_model": "Ford Explorer Police Interceptor",
    "officer_name": "John Smith",
    "officer_badge": "B-1234",
    "officer_rank": "Sergeant"
})

# Get available cars
response = requests.get(f"{BASE_URL}/police/available")
cars = response.json()

# Dispatch a car
response = requests.post(f"{BASE_URL}/police/dispatch", json={
    "car_id": "CAR-001",
    "incident_id": "INC-12345"
})

# Update status
response = requests.put(f"{BASE_URL}/police/status", json={
    "car_id": "CAR-001",
    "status": "en_route"
})

# Conclude dispatch
response = requests.post(f"{BASE_URL}/police/conclude", json={
    "car_id": "CAR-001"
})
```

## Testing

Run the test script to see a complete workflow example:

```bash
# Make sure the API server is running first
uvicorn backend.api:app --reload

# In another terminal
python backend/test_police_cars.py
```

## Integration with Incidents

The police car system integrates with the incident management system through the `incident_id` field. When a car is dispatched:

1. The car's `status` changes to `dispatched`
2. The `incident_id` is set to the target incident
3. A dispatch record is added to `dispatch_history`
4. The dispatch location is recorded

When the dispatch is concluded:

1. The car's `status` returns to `inactive`
2. The `incident_id` is cleared
3. The dispatch record is marked with `concluded_at`

## Dispatch History

Every dispatch is recorded in the `dispatch_history` array, maintaining a complete audit trail of:

-   Which incidents the car was dispatched to
-   When dispatches occurred
-   Where the car was sent
-   When dispatches were concluded

This historical data can be used for:

-   Performance analytics
-   Response time calculations
-   Officer workload tracking
-   Incident reporting

## Future Enhancements

Potential features to add:

-   Real-time GPS tracking integration
-   Automatic status updates based on location
-   Route optimization for dispatches
-   Officer shift management
-   Vehicle maintenance tracking
-   Fuel and mileage logging
-   Integration with CAD (Computer-Aided Dispatch) systems
