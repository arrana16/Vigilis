from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import your existing functions
from suggest import givesuggestions, summarize_current_status
from update import generate_report, create_bson, set_concluded
from polizia_agent.tools import update_context
from polizia_agent.agent import chat
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

# Response models
class StatusResponse(BaseModel):
    status: str
    message: str

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Vigilis Emergency Services API",
        "version": "1.0.0",
        "endpoints": {
            "GET /health": "Health check",
            "POST /chat": "Chat with Vigilis AI assistant",
            "POST /incident/context": "Get incident context (BSON)",
            "POST /incident/summary": "Get incident summary",
            "POST /incident/suggestions": "Get AI suggestions for incident",
            "POST /incident/report": "Generate incident report",
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
            "DELETE /police/cars/{car_id}": "Delete a police car"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/incident/context")
def get_incident_context(request: IncidentRequest):
    """
    Get the full incident document as JSON
    """
    try:
        context = update_context(request.incident_id)
        if context.startswith("Error") or context.startswith("No incident"):
            raise HTTPException(status_code=404, detail=context)
        
        import json
        return {"incident_id": request.incident_id, "context": json.loads(context)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/incident/summary")
def get_incident_summary(request: IncidentRequest):
    """
    Get a concise summary of the current incident status
    """
    try:
        summary = summarize_current_status(request.incident_id)
        if summary.startswith("Error") or summary.startswith("No incident"):
            raise HTTPException(status_code=404, detail=summary)
        
        return {"incident_id": request.incident_id, "summary": summary}
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/incident/report")
def generate_incident_report(request: IncidentRequest):
    """
    Generate a comprehensive incident report (300 words)
    """
    try:
        report = generate_report(request.incident_id)
        if report.startswith("Error") or report.startswith("No incident"):
            raise HTTPException(status_code=404, detail=report)
        
        return {"incident_id": request.incident_id, "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/incident/conclude")
def conclude_incident(request: ConcludeIncidentRequest):
    """
    Conclude an incident: generate report, create embedding, save to knowledge base
    """
    try:
        # First, mark incident as concluded
        status_msg = set_concluded(request.incident_id)
        
        # Then create and save the BSON document
        result = create_bson(request.incident_id)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Remove the embedding from response (too large)
        response_data = {
            "incident_id": request.incident_id,
            "status_update": status_msg,
            "concluded_at": result.get("concluded_at"),
            "original_incident_id": result.get("original_incident_id"),
            "location": result.get("location"),
            "report_length": len(result.get("final_summary", "")),
            "embedding_dimensions": len(result.get("final_summary_embedding", [])),
            "knowledge_base_id": result.get("_id")
        }
        
        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/incident/status")
def update_incident_status(request: IncidentRequest):
    """
    Mark an incident as concluded in the active incidents collection
    """
    try:
        result = set_concluded(request.incident_id)
        if result.startswith("Error") or result.startswith("No incident"):
            raise HTTPException(status_code=404, detail=result)
        
        return {"incident_id": request.incident_id, "message": result}
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
    Delete a police car from the database
    """
    try:
        success = PoliceCar.delete_police_car(car_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Police car {car_id} not found"
            )
        
        return {
            "status": "success",
            "message": f"Police car {car_id} deleted successfully",
            "car_id": car_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
