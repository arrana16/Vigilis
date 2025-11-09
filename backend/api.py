from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import sys
import os
import asyncio
import json
from polizia_agent.polizia_agent import chat


# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")


manager = ConnectionManager()


# Import your existing functions
from suggest import givesuggestions, summarize_current_status
from update import generate_report, create_bson, set_concluded, post_story
from fill_agent.fill_agent import update_dynamic_fields
from polizia_agent.polizia_tools import get_incident_context
# from polizia_agent.polizia_agent import chat
from db import add_transcript, retrieve_chat_elements, get_current_summary
from police_cars import (
   PoliceCar,
   PoliceCarStatus,
   create_car,
   get_car,
   dispatch_car,
   conclude_car_dispatch,
   get_available_cars,
   get_dispatched_cars
)


# Import Redis and simulation services
from redis_tracking import (
   get_car_location,
   get_all_car_locations,
   get_nearby_cars,
   redis_client,
   sync_service,
   get_sync_stats,
   car_simulator,
   add_simulated_car,
   remove_simulated_car
)


app = FastAPI(title="Vigilis Emergency Services API", version="1.0.0")


# Enable CORS
app.add_middleware(
   CORSMiddleware,
   allow_origins=["*"],  # Configure this based on your frontend URL
   allow_credentials=True,
   allow_methods=["*"],
   allow_headers=["*"],
)


# Request models
class IncidentRequest(BaseModel):
   incident_id: str


class AddTranscriptRequest(BaseModel):
   incident_id: str
   transcript: str
   caller: str
   convo: str


class ConcludeIncidentRequest(BaseModel):
   incident_id: str


class ChatRequest(BaseModel):
   message: str
   incident_id: Optional[str] = None


# Police Car request models
class CreatePoliceCarRequest(BaseModel):
   car_id: str
   car_model: str
   officer_name: str
   officer_badge: str
   officer_rank: Optional[str] = "Officer"
   unit_number: Optional[str] = None
   location: Optional[Dict[str, Any]] = None


class DispatchCarRequest(BaseModel):
   car_id: str
   incident_id: str
   dispatch_location: Optional[Dict[str, Any]] = None


class UpdateCarStatusRequest(BaseModel):
   car_id: str
   status: str
   location: Optional[Dict[str, Any]] = None


class UpdateCarLocationRequest(BaseModel):
   car_id: str
   lat: float
   lng: float
   address: Optional[str] = None


class CarIdRequest(BaseModel):
   car_id: str


class NearbyRequest(BaseModel):
   lat: float
   lng: float
   radius_km: Optional[float] = 5.0


# Response models
class StatusResponse(BaseModel):
   status: str
   message: str


# ============================================================================
# LIFECYCLE EVENTS
# ============================================================================


@app.on_event("startup")
async def startup_event():
   """Start background services when the API starts"""
   # Start the location sync service (Redis -> MongoDB every 10 seconds)
   asyncio.create_task(sync_service.start())
  
   # Start the car simulator (simulates car movement)
   asyncio.create_task(car_simulator.start())
  
   # Auto-add existing cars from DB to simulator
   car_simulator.auto_add_cars_from_db()
  
   print("✅ Background services started: location sync & car simulator")


@app.on_event("shutdown")
async def shutdown_event():
   """Stop background services when the API shuts down"""
   sync_service.stop()
   car_simulator.stop()
   print("🛑 Background services stopped")


# ============================================================================
# ROOT & HEALTH
# ============================================================================


@app.get("/")
def root():
   """Root endpoint"""
   return {
       "message": "Vigilis Emergency Services API",
       "version": "1.0.0",
       "services": {
           "redis": "Real-time location tracking",
           "mongodb": "Persistent data storage",
           "websocket": "Live position streaming",
           "simulator": "Simulated car movement"
       },
       "endpoints": {
           "GET /health": "Health check",
           "GET /stats": "Service statistics",
           "GET /incidents": "Get all active incidents",
           "GET /incidents/all": "DEBUG: Get all incidents (any status)",
           "POST /chat": "Chat with Vigilis AI assistant",
           "POST /incident/update_transcript": "Add transcript to incident (creates new or appends to existing)",
           "GET /incident/chat_elements/{incident_id}": "Get chat elements for incident",
           "POST /incident/context": "Get incident context (BSON)",
           "POST /incident/summary": "Get incident summary",
           "POST /incident/suggestions": "Get AI suggestions for incident",
           "POST /incident/report": "Generate incident report",
        #    "POST /incident/fill_agent": "Use AI agent to detect deviations in location/severity from transcripts",
           "POST /incident/conclude": "Conclude incident and save to knowledge base",
           "PUT /incident/status": "Update incident status to concluded",
           "POST /police/cars": "Create a new police car",
           "GET /police/cars": "Get all police cars (optional: filter by status)",
           "GET /police/cars/{car_id}": "Get a specific police car",
           "POST /police/dispatch": "Dispatch a police car to an incident",
           "POST /police/conclude": "Conclude a police car dispatch",
           "PUT /police/status": "Update police car status",
           "PUT /police/location": "Update police car location",
           "GET /police/available": "Get all available police cars",
           "GET /police/incident/{incident_id}": "Get cars dispatched to an incident",
           "DELETE /police/cars/{car_id}": "Delete a police car",
           "GET /police/realtime/{car_id}": "Get real-time location from Redis",
           "GET /police/realtime": "Get all real-time locations from Redis",
           "POST /police/nearby": "Get nearby police cars within radius",
           "WS /ws/track/{car_id}": "WebSocket: Stream real-time car location",
           "POST /simulator/add/{car_id}": "Add car to simulator",
           "DELETE /simulator/remove/{car_id}": "Remove car from simulator"
       }
   }


@app.get("/health")
def health_check():
   """Health check endpoint"""
   return {"status": "healthy"}


@app.get("/incidents/all")
def get_all_incidents_debug():
   """
   DEBUG: Get ALL incidents regardless of status
   """
   try:
       from db import client
       from bson import json_util
       import json
       
       db = client["dispatch_db"]
       collection = db["active_incidents"]
       
       incidents = list(collection.find({}).limit(10))
       incidents_json = json.loads(json_util.dumps(incidents))
       
       return {"incidents": incidents_json, "count": len(incidents_json)}
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))


@app.get("/incidents")
def get_all_incidents():
   """
   Get all active incidents from the database
   """
   try:
       from db import client
       from bson import json_util
       import json
       
       print("📊 Fetching incidents from MongoDB...")
       db = client["dispatch_db"]
       collection = db["active_incidents"]
       
       # Fetch all active incidents, sorted by last update (most recent first)
       print("🔍 Querying active_incidents collection...")
       
       # First check total count
       total_count = collection.count_documents({})
       active_count = collection.count_documents({"status": "active"})
       print(f"📊 Total incidents: {total_count}, Active: {active_count}")
       
       incidents = list(collection.find(
           {"status": "active"}
       ).sort("last_summary_update_at", -1).limit(100))  # Limit to prevent huge queries
       
       print(f"✅ Found {len(incidents)} active incidents")
       
       # Convert MongoDB documents to JSON (handles ObjectId and other BSON types)
       incidents_json = json.loads(json_util.dumps(incidents))
       
       return {"incidents": incidents_json, "count": len(incidents_json)}
   except Exception as e:
       print(f"❌ Error in /incidents endpoint: {e}")
       raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
def get_stats():
   """Get service statistics"""
   return {
       "sync_service": get_sync_stats(),
       "simulator": {
           "active_cars": len(car_simulator.simulated_cars),
           "cars": list(car_simulator.simulated_cars.keys())
       }
   }


@app.post("/chat")
def chat_with_agent(request: ChatRequest):
   """
   Chat with the Vigilis AI assistant. Optionally provide an incident_id for context.
   """
   try:
       response = chat(request.message, request.incident_id)
       return {
           "message": request.message,
           "incident_id": request.incident_id,
           "response": response
       }
   except ValueError as e:
       raise HTTPException(status_code=404, detail=str(e))
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# INCIDENT DATABASE ENDPOINTS
# ============================================================================


@app.post("/incident/update_transcript")
async def add_incident_transcript(request: AddTranscriptRequest):
   """
   Add transcript to an incident. 
   Creates a new incident if it doesn't exist, or appends to existing incident.
   """
   try:
       # Add transcript to database (synchronous, blocks until write completes)
       add_transcript(request.incident_id, request.transcript, request.caller, request.convo)
       print(f"✅ Transcript added to incident {request.incident_id}")
       
       # Broadcast to all connected WebSocket clients
       await manager.broadcast("data_updated")
       
       # Trigger fill agent analysis immediately (no delay needed - add_transcript is synchronous)
       # This runs AFTER the transcript is confirmed written to the database
       try:
           print(f"🤖 Triggering fill agent analysis for incident {request.incident_id}")
           result = update_dynamic_fields(incident_id=request.incident_id)
           print(f"Fill agent result: {result}")
       except Exception as e:
           print(f"⚠️  Error analyzing incident {request.incident_id}: {e}")
       
       return {
           "status": "success",
           "message": f"Transcript added to incident {request.incident_id}",
           "incident_id": request.incident_id,
           "caller": request.caller
       }
   except ValueError as e:
       raise HTTPException(status_code=400, detail=str(e))
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))


@app.get("/incident/chat_elements/{incident_id}")
def get_chat_elements(incident_id: str):
   """
   Get chat_elements field from an incident
   """
   try:
       result = retrieve_chat_elements(incident_id)
       return {
           "incident_id": incident_id,
           "chat_elements": result["chat_elements"]
       }
   except ValueError as e:
       raise HTTPException(status_code=404, detail=str(e))
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# INCIDENT ANALYSIS ENDPOINTS
# ============================================================================


@app.post("/incident/context")
def get_incident_context_endpoint(request: IncidentRequest):
   """
   Get the full incident document as JSON
   """
   try:
       context = get_incident_context(request.incident_id)
       import json
       return {"incident_id": request.incident_id, "context": json.loads(context)}
   except ValueError as e:
       raise HTTPException(status_code=404, detail=str(e))
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))


@app.post("/incident/summary")
def get_incident_summary(request: IncidentRequest):
   """
   Get a concise summary of the current incident status
   """
   try:
       summary = get_current_summary(request.incident_id)
       return {"incident_id": request.incident_id, "summary": summary}
   except ValueError as e:
       raise HTTPException(status_code=404, detail=str(e))
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))


@app.post("/incident/suggestions")
def get_incident_suggestions(request: IncidentRequest):
   """
   Get AI-powered suggestions for handling the incident based on similar past incidents
   """
   try:
       suggestions = givesuggestions(request.incident_id)
       return {"incident_id": request.incident_id, "suggestions": suggestions}
   except ValueError as e:
       raise HTTPException(status_code=404, detail=str(e))
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))


@app.post("/incident/report")
def generate_incident_report(request: IncidentRequest):
   """
   Generate a comprehensive incident report (300 words)
   """
   try:
       report = generate_report(request.incident_id)
       return {"incident_id": request.incident_id, "report": report}
   except ValueError as e:
       raise HTTPException(status_code=404, detail=str(e))
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))


# @app.post("/incident/fill_agent")
# def fill_fields_with_agent(request: IncidentRequest):
#    """
#    Use AI agent to detect deviations between transcripts and current location/severity fields.
#    The agent will only update fields when genuine deviations are detected.
#    """
#    try:
#        # Run the agent analysis - single call
#        agent_response = update_dynamic_fields(request.incident_id)
      
#        return {
#            "incident_id": request.incident_id,
#            "message": agent_response
#        }
#    except ValueError as e:
#        raise HTTPException(status_code=404, detail=str(e))
#    except Exception as e:
#        raise HTTPException(status_code=500, detail=str(e))


@app.post("/incident/post_story")
def post_story_endpoint(request: ConcludeIncidentRequest):
   """
   Conclude an incident: mark as concluded, generate report, create embedding, save to knowledge base
   """
   try:
       result = post_story(request.incident_id)
      
       # Remove the embedding from response (too large)
       response_data = {
           "incident_id": request.incident_id,
           "concluded_at": result.get("concluded_at"),
           "original_incident_id": result.get("original_incident_id"),
           "location": result.get("location"),
           "report_length": len(result.get("final_summary", "")),
           "embedding_dimensions": len(result.get("final_summary_embedding", [])),
           "knowledge_base_id": result.get("_id")
       }
      
       return response_data
   except ValueError as e:
       raise HTTPException(status_code=404, detail=str(e))
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))


@app.put("/incident/status")
def update_incident_status(request: IncidentRequest):
   """
   Mark an incident as concluded in the active incidents collection
   """
   try:
       result = set_concluded(request.incident_id)
       return {"incident_id": request.incident_id, "message": result}
   except ValueError as e:
       raise HTTPException(status_code=404, detail=str(e))
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# POLICE CAR ENDPOINTS
# ============================================================================


@app.post("/police/cars")
def create_police_car(request: CreatePoliceCarRequest):
   """
   Create a new police car entry in the database
   """
   try:
       car_id = create_car(
           car_id=request.car_id,
           car_model=request.car_model,
           officer_name=request.officer_name,
           officer_badge=request.officer_badge,
           officer_rank=request.officer_rank,
           unit_number=request.unit_number,
           location=request.location
       )
      
       return {
           "status": "success",
           "message": f"Police car {request.car_id} created successfully",
           "car_id": request.car_id,
           "mongodb_id": car_id
       }
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))


@app.get("/police/cars")
def get_all_police_cars(status: Optional[str] = None):
   """
   Get all police cars, optionally filtered by status.
   Valid statuses: inactive, dispatched, en_route, on_scene, returning
   """
   try:
       cars = PoliceCar.get_all_police_cars(status=status)
      
       # Convert ObjectId to string for JSON serialization
       for car in cars:
           car["_id"] = str(car["_id"])
      
       return {
           "status": "success",
           "count": len(cars),
           "filter": status,
           "cars": cars
       }
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))


@app.get("/police/cars/{car_id}")
def get_police_car_by_id(car_id: str):
   """
   Get a specific police car by its car_id
   """
   try:
       car = get_car(car_id)
      
       if not car:
           raise HTTPException(
               status_code=404,
               detail=f"Police car {car_id} not found"
           )
      
       # Convert ObjectId to string
       car["_id"] = str(car["_id"])
      
       return {
           "status": "success",
           "car": car
       }
   except HTTPException:
       raise
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))


@app.post("/police/dispatch")
def dispatch_police_car(request: DispatchCarRequest):
   """
   Dispatch a police car to an incident
   """
   try:
       success = dispatch_car(
           car_id=request.car_id,
           incident_id=request.incident_id,
           dispatch_location=request.dispatch_location
       )
      
       if not success:
           raise HTTPException(
               status_code=404,
               detail=f"Police car {request.car_id} not found or could not be dispatched"
           )
      
       return {
           "status": "success",
           "message": f"Police car {request.car_id} dispatched to incident {request.incident_id}",
           "car_id": request.car_id,
           "incident_id": request.incident_id
       }
   except HTTPException:
       raise
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))


@app.post("/police/conclude")
def conclude_police_dispatch(request: CarIdRequest):
   """
   Conclude a police car dispatch and return it to inactive status
   """
   try:
       success = conclude_car_dispatch(request.car_id)
      
       if not success:
           raise HTTPException(
               status_code=404,
               detail=f"Police car {request.car_id} not found or not currently dispatched"
           )
      
       return {
           "status": "success",
           "message": f"Police car {request.car_id} dispatch concluded, returned to inactive status",
           "car_id": request.car_id
       }
   except HTTPException:
       raise
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))


@app.put("/police/status")
def update_police_car_status(request: UpdateCarStatusRequest):
   """
   Update the status of a police car
   Valid statuses: inactive, dispatched, en_route, on_scene, returning
   """
   try:
       # Validate status
       valid_statuses = [
           PoliceCarStatus.INACTIVE,
           PoliceCarStatus.DISPATCHED,
           PoliceCarStatus.EN_ROUTE,
           PoliceCarStatus.ON_SCENE,
           PoliceCarStatus.RETURNING
       ]
      
       if request.status not in valid_statuses:
           raise HTTPException(
               status_code=400,
               detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
           )
      
       success = PoliceCar.update_car_status(
           car_id=request.car_id,
           status=request.status,
           location=request.location
       )
      
       if not success:
           raise HTTPException(
               status_code=404,
               detail=f"Police car {request.car_id} not found"
           )
      
       return {
           "status": "success",
           "message": f"Police car {request.car_id} status updated to {request.status}",
           "car_id": request.car_id,
           "new_status": request.status
       }
   except HTTPException:
       raise
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))


@app.put("/police/location")
def update_police_car_location(request: UpdateCarLocationRequest):
   """
   Update the current location of a police car
   """
   try:
       success = PoliceCar.update_car_location(
           car_id=request.car_id,
           lat=request.lat,
           lng=request.lng,
           address=request.address
       )
      
       if not success:
           raise HTTPException(
               status_code=404,
               detail=f"Police car {request.car_id} not found"
           )
      
       return {
           "status": "success",
           "message": f"Police car {request.car_id} location updated",
           "car_id": request.car_id,
           "location": {
               "lat": request.lat,
               "lng": request.lng,
               "address": request.address
           }
       }
   except HTTPException:
       raise
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))


@app.get("/police/available")
def get_available_police_cars():
   """
   Get all available (inactive) police cars
   """
   try:
       cars = get_available_cars()
      
       # Convert ObjectId to string
       for car in cars:
           car["_id"] = str(car["_id"])
      
       return {
           "status": "success",
           "count": len(cars),
           "available_cars": cars
       }
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))


@app.get("/police/incident/{incident_id}")
def get_cars_for_incident(incident_id: str):
   """
   Get all police cars dispatched to a specific incident
   """
   try:
       cars = get_dispatched_cars(incident_id)
      
       # Convert ObjectId to string
       for car in cars:
           car["_id"] = str(car["_id"])
      
       return {
           "status": "success",
           "incident_id": incident_id,
           "count": len(cars),
           "dispatched_cars": cars
       }
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))


@app.delete("/police/cars/{car_id}")
def delete_police_car(car_id: str):
   """
   Delete a police car from the database, Redis, and simulator.
   This ensures complete cleanup across all systems.
   """
   try:
       # Delete from MongoDB and Redis
       success = PoliceCar.delete_police_car(car_id)
      
       if not success:
           raise HTTPException(
               status_code=404,
               detail=f"Police car {car_id} not found"
           )
      
       # Also remove from simulator if it's running
       car_simulator.remove_car(car_id)
      
       return {
           "status": "success",
           "message": f"Police car {car_id} deleted from all systems (MongoDB, Redis, Simulator)",
           "car_id": car_id
       }
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# REAL-TIME LOCATION ENDPOINTS (Redis)
# ============================================================================


@app.get("/police/realtime/{car_id}")
def get_realtime_location(car_id: str):
   """
   Get the real-time location of a specific car from Redis.
   This is high-frequency data updated every second.
   """
   try:
       location = get_car_location(car_id)
      
       if not location:
           raise HTTPException(
               status_code=404,
               detail=f"No real-time location found for car {car_id}"
           )
      
       return {
           "status": "success",
           "car_id": car_id,
           "location": location
       }
   except HTTPException:
       raise
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))


@app.get("/police/realtime")
def get_all_realtime_locations():
   """
   Get all real-time car locations from Redis.
   This is high-frequency data updated every second.
   """
   try:
       locations = get_all_car_locations()
      
       return {
           "status": "success",
           "count": len(locations),
           "locations": locations
       }
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))


@app.post("/police/nearby")
def find_nearby_cars(request: NearbyRequest):
   """
   Find police cars within a certain radius of a location.
   Uses real-time Redis data for most accurate results.
   """
   try:
       nearby = get_nearby_cars(
           lat=request.lat,
           lng=request.lng,
           radius_km=request.radius_km
       )
      
       return {
           "status": "success",
           "center": {"lat": request.lat, "lng": request.lng},
           "radius_km": request.radius_km,
           "count": len(nearby),
           "cars": nearby
       }
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WEBSOCKET ENDPOINTS (Real-time Streaming)
# ============================================================================


@app.websocket("/ws/track/{car_id}")
async def websocket_track_car(websocket: WebSocket, car_id: str):
   """
   WebSocket endpoint for streaming real-time car location updates.
   Subscribes to Redis pub/sub channel for the specified car.
  
   Usage:
       const ws = new WebSocket('ws://localhost:8000/ws/track/PC-001');
       ws.onmessage = (event) => {
           const location = JSON.parse(event.data);
           console.log('Car position:', location.lat, location.lng);
       };
   """
   await websocket.accept()
  
   # Create Redis pubsub client
   pubsub = redis_client.pubsub()
   channel_name = f"car:location:stream:{car_id}"
  
   try:
       # Subscribe to the car's location channel
       pubsub.subscribe(channel_name)
      
       # Send initial confirmation
       await websocket.send_json({
           "status": "connected",
           "car_id": car_id,
           "channel": channel_name,
           "message": f"Subscribed to real-time updates for {car_id}"
       })
      
       # Listen for messages
       while True:
           # Check for messages from Redis (non-blocking with timeout)
           message = pubsub.get_message(timeout=0.1)
          
           if message and message['type'] == 'message':
               # Forward the location update to the WebSocket client
               location_data = json.loads(message['data'])
               await websocket.send_json(location_data)
          
           # Small delay to prevent CPU spinning
           await asyncio.sleep(0.1)
          
   except WebSocketDisconnect:
       print(f"WebSocket disconnected for car {car_id}")
   except Exception as e:
       print(f"WebSocket error for car {car_id}: {e}")
       await websocket.send_json({
           "status": "error",
           "message": str(e)
       })
   finally:
       # Clean up
       pubsub.unsubscribe(channel_name)
       pubsub.close()


# ============================================================================
# SIMULATOR CONTROL ENDPOINTS
# ============================================================================


@app.post("/simulator/add/{car_id}")
def add_car_to_simulator(car_id: str, lat: Optional[float] = None, lng: Optional[float] = None):
   """
   Add a car to the movement simulator.
   If lat/lng not provided, will start at a random location in Atlanta.
   """
   try:
       add_simulated_car(car_id, lat, lng)
      
       return {
           "status": "success",
           "message": f"Car {car_id} added to simulator",
           "car_id": car_id
       }
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))


@app.delete("/simulator/remove/{car_id}")
def remove_car_from_simulator(car_id: str):
   """
   Remove a car from the movement simulator.
   """
   try:
       remove_simulated_car(car_id)
      
       return {
           "status": "success",
           "message": f"Car {car_id} removed from simulator",
           "car_id": car_id
       }
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))




@app.post("/internal/notify-clients")
async def notify_clients_from_trigger(request: Request):
   """
   Internal endpoint for a Mongo Trigger.
   Broadcasts a "data_updated" message to all connected clients.
   """
   # Security: Validate the trigger secret from environment
   expected_secret = os.getenv("WEBSOCKET_SECRET")
   provided_secret = request.headers.get('x-trigger-secret')

   if not expected_secret or provided_secret != expected_secret:
       raise HTTPException(status_code=401, detail="Unauthorized")

   # Parse the JSON payload to get incident_id
   payload = await request.json()
   incident_id = payload.get("incident_id")
   
#    if incident_id:
#        # Run the fill agent analysis
#        try:
#            update_dynamic_fields(incident_id=incident_id)
#        except Exception as e:
#            print(f"Error analyzing incident {incident_id}: {e}")

   # Broadcast to all connected clients
   await manager.broadcast("data_updated")

   return {"message": "Notification sent to all clients"}




@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
   """
   The main WebSocket endpoint for clients to connect to.
   """
   await manager.connect(websocket)
   try:
       while True:
           # Wait for messages from the client.
           data = await websocket.receive_text()
           # Optionally handle messages here, e.g.:
           # print(f"Client sent: {data}")


   except WebSocketDisconnect:
       manager.disconnect(websocket)
       print("Client disconnected")


   except Exception as e:
       print(f"WebSocket error: {e}")
       manager.disconnect(websocket)




if __name__ == "__main__":
   import uvicorn
   uvicorn.run(app, host="0.0.0.0", port=8000)



