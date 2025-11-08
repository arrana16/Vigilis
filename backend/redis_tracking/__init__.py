"""
Redis-based real-time location tracking system.

This package provides high-frequency location tracking for police vehicles using Redis,
with automatic synchronization to MongoDB every 10 seconds.
"""

from .redis_client import (
    redis_client,
    get_car_location,
    update_car_location,
    get_all_car_locations,
    delete_car_location,
    get_nearby_cars,
    test_redis_connection
)

from .location_sync import (
    sync_service,
    start_sync_service,
    get_sync_stats
)

from .car_simulator import (
    car_simulator,
    start_car_simulator,
    add_simulated_car,
    remove_simulated_car
)

__all__ = [
    # Redis client functions
    'redis_client',
    'get_car_location',
    'update_car_location',
    'get_all_car_locations',
    'delete_car_location',
    'get_nearby_cars',
    'test_redis_connection',
    
    # Sync service
    'sync_service',
    'start_sync_service',
    'get_sync_stats',
    
    # Car simulator
    'car_simulator',
    'start_car_simulator',
    'add_simulated_car',
    'remove_simulated_car',
]
