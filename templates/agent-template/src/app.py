"""
Template agent application.
Customize this file for your specific protocol and requirements.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
import uuid
from typing import Dict, Any, Optional

# Import your protocol-specific modules here
# from your_protocol import YourProtocolClient
# from your_models import YourDataModels

# Initialize FastAPI app
app = FastAPI(
    title="{PROTOCOL} {AGENT_NAME} Agent",
    description="A {DESCRIPTION} agent implementing the {PROTOCOL} protocol",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models (customize for your protocol)
class HealthResponse(BaseModel):
    status: str
    timestamp: float
    agent_id: str
    protocol: str

class AgentInfo(BaseModel):
    agent_id: str
    name: str
    version: str
    description: str
    protocol: str
    capabilities: list[str]

class YourRequestModel(BaseModel):
    # Define your request structure
    input_data: str
    parameters: Optional[Dict[str, Any]] = None

class YourResponseModel(BaseModel):
    # Define your response structure
    output_data: str
    status: str
    request_id: str

# Global agent configuration
AGENT_ID = "{AGENT_NAME}-agent"
AGENT_NAME = "{PROTOCOL} {AGENT_NAME} Agent"
AGENT_VERSION = "0.1.0"
PROTOCOL_NAME = "{PROTOCOL}"

# Core endpoints

@app.get("/")
async def root():
    """Root endpoint providing basic agent information."""
    return {
        "agent_id": AGENT_ID,
        "name": AGENT_NAME,
        "version": AGENT_VERSION,
        "description": "A {DESCRIPTION} agent implementing the {PROTOCOL} protocol",
        "protocol": PROTOCOL_NAME,
        "endpoints": {
            "health": "/health",
            "info": "/info",
            # Add your protocol-specific endpoints here
            "your_endpoint": "/your-endpoint"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=time.time(),
        agent_id=AGENT_ID,
        protocol=PROTOCOL_NAME
    )

@app.get("/info", response_model=AgentInfo)
async def get_info():
    """Get comprehensive agent information."""
    return AgentInfo(
        agent_id=AGENT_ID,
        name=AGENT_NAME,
        version=AGENT_VERSION,
        description="A {DESCRIPTION} agent implementing the {PROTOCOL} protocol",
        protocol=PROTOCOL_NAME,
        capabilities=[
            # List your agent's capabilities
            "basic_functionality",
            "health_monitoring",
            "error_handling"
        ]
    )

# Protocol-specific endpoints (customize these)

@app.post("/your-endpoint", response_model=YourResponseModel)
async def your_protocol_endpoint(request: YourRequestModel):
    """
    Implement your protocol-specific functionality here.
    
    This is a template endpoint - replace with your actual protocol endpoints.
    """
    try:
        # Implement your protocol logic here
        # Example:
        result = process_request(request.input_data, request.parameters)
        
        return YourResponseModel(
            output_data=result,
            status="completed",
            request_id=str(uuid.uuid4())
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

# Helper functions (customize for your protocol)

def process_request(input_data: str, parameters: Optional[Dict[str, Any]] = None) -> str:
    """
    Process the request according to your protocol.
    
    Replace this with your actual implementation.
    """
    # Example implementation
    processed_data = f"Processed: {input_data}"
    
    if parameters:
        processed_data += f" with parameters: {parameters}"
    
    return processed_data

# Error handlers

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "agent_id": AGENT_ID
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return {
        "error": "Internal server error",
        "detail": str(exc),
        "status_code": 500,
        "agent_id": AGENT_ID
    }

# Main execution
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )