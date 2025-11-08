# Redis Real-Time Tracking System

This folder contains all components for the Redis-based real-time location tracking system.

## Files

### Core Services

-   **`redis_client.py`** - Redis client for high-frequency location storage
    -   Functions: `get_car_location()`, `update_car_location()`, `get_nearby_cars()`
-   **`location_sync.py`** - Background service that syncs Redis → MongoDB every 10 seconds
    -   Keeps MongoDB updated with latest positions from Redis
-   **`car_simulator.py`** - Simulates realistic police car movement
    -   Updates positions every 1 second
    -   Realistic speeds (20-60 mph) and waypoint navigation

### Testing & Demos

-   **`test_redis_system.py`** - Complete test suite for Redis system
    -   Tests connection, updates, nearby search, simulator
-   **`demo_realtime_tracking.py`** - Live demonstration script
    -   Shows the complete workflow in action

### Package

-   **`__init__.py`** - Makes this folder a Python package
    -   Exports all public functions for easy importing

## Quick Usage

### Import in your code:

```python
from redis import (
    get_car_location,
    update_car_location,
    get_nearby_cars,
    sync_service,
    car_simulator
)
```

### Run tests:

```bash
python redis/test_redis_system.py
```

### Run demo:

```bash
python redis/demo_realtime_tracking.py
```

## Architecture

```
Car Simulator (1s) → Redis → WebSocket → Frontend
                       ↓
                  Sync (10s)
                       ↓
                    MongoDB
```

## Documentation

See `/backend/descriptions/` for complete documentation:

-   `REDIS_QUICK_START.md` - 5-minute setup
-   `REDIS_REALTIME_TRACKING.md` - Full documentation
-   `REDIS_SETUP_COMPLETE.md` - Examples and use cases

## Requirements

-   Redis server running
-   Python packages: `redis`, `websockets`

Install:

```bash
pip install redis websockets
```
