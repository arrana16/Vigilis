# Quick Start Guide - Police Cars System

## Installation & Setup

### 1. Install Dependencies

Make sure you're in the Vigilis project directory and have your virtual environment activated:

```bash
cd /Users/abdur-rahmanrana/Documents/AI\ ATL/Vigilis

# If you haven't created a virtual environment yet:
python3 -m venv venv
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Make sure your `.env` file in the project root has:

```env
MONGO_URI=your_mongodb_connection_string
GEMINI_API_KEY=your_google_api_key
```

### 3. Start the API Server

```bash
# From the project root
uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
```

The server will start on `http://localhost:8000`

### 4. Access the API Documentation

Open your browser and go to:

-   **Swagger UI**: http://localhost:8000/docs
-   **ReDoc**: http://localhost:8000/redoc

You'll see all the police car endpoints along with the existing incident endpoints.

## Quick Test

### Option 1: Use the Test Script

```bash
# Make sure the server is running, then in another terminal:
cd /Users/abdur-rahmanrana/Documents/AI\ ATL/Vigilis
source venv/bin/activate
python backend/test_police_cars.py
```

This will run through a complete example workflow.

### Option 2: Use cURL

```bash
# Create a police car
curl -X POST "http://localhost:8000/police/cars" \
  -H "Content-Type: application/json" \
  -d '{
    "car_id": "CAR-001",
    "car_model": "Ford Explorer Police Interceptor",
    "officer_name": "John Smith",
    "officer_badge": "B-1234",
    "officer_rank": "Sergeant"
  }'

# Get all cars
curl "http://localhost:8000/police/cars"

# Get available cars
curl "http://localhost:8000/police/available"

# Dispatch a car
curl -X POST "http://localhost:8000/police/dispatch" \
  -H "Content-Type: application/json" \
  -d '{
    "car_id": "CAR-001",
    "incident_id": "INC-12345"
  }'

# Get car details
curl "http://localhost:8000/police/cars/CAR-001"

# Update car status
curl -X PUT "http://localhost:8000/police/status" \
  -H "Content-Type: application/json" \
  -d '{
    "car_id": "CAR-001",
    "status": "en_route"
  }'

# Conclude dispatch
curl -X POST "http://localhost:8000/police/conclude" \
  -H "Content-Type: application/json" \
  -d '{
    "car_id": "CAR-001"
  }'
```

### Option 3: Use the Interactive API Docs

1. Go to http://localhost:8000/docs
2. Click on any endpoint (e.g., "POST /police/cars")
3. Click "Try it out"
4. Fill in the request body
5. Click "Execute"

## Common Commands

```bash
# Start the server in development mode (auto-reload on file changes)
uvicorn backend.api:app --reload

# Start the server in production mode with multiple workers
uvicorn backend.api:app --workers 4

# Start on a different port
uvicorn backend.api:app --port 8001

# View all routes
curl http://localhost:8000/
```

## Typical Workflow

1. **Create police cars** when they become available for dispatch
2. **Monitor available cars** using GET `/police/available`
3. **Dispatch a car** to an incident using POST `/police/dispatch`
4. **Update status** as the car responds (en_route → on_scene)
5. **Update location** periodically as the car moves
6. **Conclude dispatch** when the incident is resolved
7. **View dispatch history** by getting the car details

## Integration with Your Frontend

From your Next.js frontend, you can use fetch or axios:

```typescript
// Example: Get available police cars
const response = await fetch("http://localhost:8000/police/available");
const data = await response.json();
console.log(data.available_cars);

// Example: Dispatch a car
const response = await fetch("http://localhost:8000/police/dispatch", {
	method: "POST",
	headers: { "Content-Type": "application/json" },
	body: JSON.stringify({
		car_id: "CAR-001",
		incident_id: incidentId,
	}),
});
```

## Troubleshooting

### "Connection refused" error

-   Make sure the API server is running
-   Check that you're using the correct port (default: 8000)

### Import errors when starting server

-   Make sure you've activated your virtual environment: `source venv/bin/activate`
-   Reinstall dependencies: `pip install -r requirements.txt`

### MongoDB connection errors

-   Verify your `MONGO_URI` in the `.env` file
-   Check your network connection
-   Ensure your MongoDB cluster allows connections from your IP

### "Car not found" errors

-   Make sure you created the car first using POST `/police/cars`
-   Verify the `car_id` matches exactly (case-sensitive)

## Next Steps

See `POLICE_CARS_README.md` for:

-   Complete API documentation
-   Database schema details
-   Python code examples
-   Integration patterns
