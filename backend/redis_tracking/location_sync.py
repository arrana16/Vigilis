"""
Background service that syncs car locations from Redis to MongoDB every 10 seconds.
This keeps the permanent database updated with the latest positions.
"""
import asyncio
import time
from datetime import datetime
from typing import Dict, Any
from .redis_client import get_all_car_locations
from police_cars import PoliceCar

class LocationSyncService:
    def __init__(self, sync_interval: int = 10):
        """
        Initialize the location sync service.
        
        Args:
            sync_interval: How often to sync (in seconds), default 10
        """
        self.sync_interval = sync_interval
        self.running = False
        self.stats = {
            "total_syncs": 0,
            "successful_updates": 0,
            "failed_updates": 0,
            "last_sync": None
        }
    
    async def sync_locations(self):
        """Sync all car locations from Redis to MongoDB"""
        try:
            # Get all locations from Redis
            redis_locations = get_all_car_locations()
            
            if not redis_locations:
                print(f"[{datetime.now()}] No car locations to sync")
                return
            
            print(f"[{datetime.now()}] Syncing {len(redis_locations)} car locations to MongoDB...")
            
            for location in redis_locations:
                try:
                    car_id = location.get("car_id")
                    if not car_id:
                        continue
                    
                    # Update MongoDB with the latest location from Redis
                    success = PoliceCar.update_car_location(
                        car_id=car_id,
                        lat=location.get("lat"),
                        lng=location.get("lng"),
                        address=f"Moving at {location.get('speed', 0)} mph"
                    )
                    
                    if success:
                        self.stats["successful_updates"] += 1
                    else:
                        self.stats["failed_updates"] += 1
                        
                except Exception as e:
                    print(f"Error syncing car {location.get('car_id')}: {e}")
                    self.stats["failed_updates"] += 1
            
            self.stats["total_syncs"] += 1
            self.stats["last_sync"] = datetime.now().isoformat()
            
            print(f"[{datetime.now()}] Sync complete. Total syncs: {self.stats['total_syncs']}, "
                  f"Success: {self.stats['successful_updates']}, Failed: {self.stats['failed_updates']}")
            
        except Exception as e:
            print(f"Error during location sync: {e}")
    
    async def start(self):
        """Start the background sync service"""
        self.running = True
        print(f"🚀 Location sync service started (interval: {self.sync_interval}s)")
        
        while self.running:
            await self.sync_locations()
            await asyncio.sleep(self.sync_interval)
    
    def stop(self):
        """Stop the background sync service"""
        self.running = False
        print("🛑 Location sync service stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get sync statistics"""
        return self.stats

# Global instance
sync_service = LocationSyncService(sync_interval=10)

async def start_sync_service():
    """Start the sync service"""
    await sync_service.start()

def get_sync_stats():
    """Get sync service statistics"""
    return sync_service.get_stats()

if __name__ == "__main__":
    # Run the sync service
    print("Starting location sync service...")
    asyncio.run(start_sync_service())
