from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import your existing functions
from suggest import givesuggestions, summarize_current_status
from update import generate_report, create_bson, set_concluded
from polizia_agent.tools import update_context
from polizia_agent.agent import chat

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
            "PUT /incident/status": "Update incident status to concluded"
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
