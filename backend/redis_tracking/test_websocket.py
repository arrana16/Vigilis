"""
WebSocket client test for tracking police cars in real-time.

Usage:
    python3 redis_tracking/test_websocket.py [CAR_ID]

Example:
    python3 redis_tracking/test_websocket.py PC-001
"""
import asyncio
import websockets
import json
import sys
from datetime import datetime

async def track_car(car_id: str, duration: int = 30):
    """
    Connect to WebSocket and track a car for specified duration.
    
    Args:
        car_id: ID of the car to track
        duration: How long to track in seconds (default 30)
    """
    uri = f"ws://localhost:8000/ws/track/{car_id}"
    
    print("\n" + "="*70)
    print(f"🔌 WEBSOCKET TRACKING TEST - {car_id}")
    print("="*70 + "\n")
    
    try:
        print(f"Connecting to: {uri}")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket!\n")
            
            start_time = asyncio.get_event_loop().time()
            update_count = 0
            
            print("📍 Receiving real-time position updates:")
            print("-" * 70)
            
            while True:
                # Check if duration exceeded
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > duration:
                    print("\n⏰ Duration reached. Disconnecting...")
                    break
                
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(message)
                    
                    # Check if it's the connection confirmation
                    if data.get('status') == 'connected':
                        print(f"✅ {data.get('message')}")
                        print(f"📡 Channel: {data.get('channel')}\n")
                        continue
                    
                    # It's a location update
                    update_count += 1
                    timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                    
                    print(f"Update #{update_count} at {timestamp.strftime('%H:%M:%S')}")
                    print(f"  📍 Position: ({data['lat']:.6f}, {data['lng']:.6f})")
                    print(f"  🚗 Speed: {data.get('speed', 0):.1f} mph")
                    print(f"  🧭 Heading: {data.get('heading', 0):.1f}°")
                    print()
                    
                except asyncio.TimeoutError:
                    print("⏳ No update received (timeout)...")
                    continue
                except json.JSONDecodeError as e:
                    print(f"⚠️  Could not parse message: {e}")
                    continue
            
            print("-" * 70)
            print(f"\n📊 Summary:")
            print(f"  • Total updates received: {update_count}")
            print(f"  • Duration: {elapsed:.1f} seconds")
            print(f"  • Average update rate: {update_count/elapsed:.2f} updates/second")
            print(f"\n✅ WebSocket test completed successfully!\n")
            
    except websockets.exceptions.WebSocketException as e:
        print(f"\n❌ WebSocket error: {e}")
        print("\nTroubleshooting:")
        print("  1. Make sure the server is running:")
        print("     python3 -m uvicorn api:app --reload")
        print(f"  2. Make sure the car '{car_id}' exists and is in the simulator")
        print(f"  3. Try: curl http://localhost:8000/police/realtime/{car_id}")
        print()
        return False
    except ConnectionRefusedError:
        print("\n❌ Connection refused!")
        print("\nMake sure the FastAPI server is running:")
        print("  cd backend")
        print("  python3 -m uvicorn api:app --reload")
        print()
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print()
        return False
    
    return True

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("\n❌ Error: Car ID required")
        print("\nUsage:")
        print("  python3 redis_tracking/test_websocket.py [CAR_ID]")
        print("\nExample:")
        print("  python3 redis_tracking/test_websocket.py PC-001")
        print("\nTip: Run test_e2e.py first to create a test car!")
        print()
        sys.exit(1)
    
    car_id = sys.argv[1]
    duration = 30  # Track for 30 seconds by default
    
    if len(sys.argv) > 2:
        try:
            duration = int(sys.argv[2])
        except ValueError:
            print(f"⚠️  Invalid duration '{sys.argv[2]}', using default (30 seconds)")
    
    # Run the async tracking function
    success = asyncio.run(track_car(car_id, duration))
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
