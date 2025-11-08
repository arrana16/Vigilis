"""
Quick WebSocket diagnostic script to debug connection issues.
"""
import asyncio
import websockets
import json

async def test_connection():
    uri = "ws://localhost:8000/ws/track/TEST-E2E-001"
    
    print("="*70)
    print("WebSocket Diagnostic Test")
    print("="*70)
    print(f"\nConnecting to: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connection successful!")
            
            # Wait for initial confirmation message
            print("\nWaiting for messages...")
            
            for i in range(5):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    data = json.loads(message)
                    
                    print(f"\nMessage {i+1}:")
                    print(f"  Type: {type(data)}")
                    print(f"  Content: {json.dumps(data, indent=2)}")
                    
                except asyncio.TimeoutError:
                    print(f"\nTimeout waiting for message {i+1}")
                    print("This might mean:")
                    print("  1. The car is not in the simulator")
                    print("  2. Redis pub/sub is not publishing")
                    print("  3. The car_id doesn't exist")
                    break
                    
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket error: {e}")
        print("\nPossible issues:")
        print("  1. Server is not running")
        print("  2. Wrong URL/port")
        print("  3. WebSocket endpoint not properly configured")
        
    except ConnectionRefusedError:
        print("❌ Connection refused!")
        print("\nThe server is not running. Start it with:")
        print("  cd backend")
        print("  python3 -m uvicorn api:app --reload")
        
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        
    print("\n" + "="*70)

if __name__ == "__main__":
    asyncio.run(test_connection())
