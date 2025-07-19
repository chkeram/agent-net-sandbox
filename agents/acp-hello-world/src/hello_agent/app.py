"""FastAPI application implementing Agent Connect Protocol (ACP) endpoints."""

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import time
from typing import Dict, Any, Iterator
import uvicorn

from .agent import HelloWorldAgent
from .models import (
    AuthInfo, SchemaDefinition, ConfigRequest, ConfigResponse,
    InvokeRequest, InvokeResponse, HelloInput, ErrorResponse
)


# Initialize the agent
agent = HelloWorldAgent()

# Create FastAPI app
app = FastAPI(
    title="AGNTCY Hello World Agent",
    description="A simple hello world agent implementing the Agent Connect Protocol (ACP)",
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


@app.get("/")
async def root():
    """Root endpoint providing basic agent information."""
    return {
        "agent": agent.agent_name,
        "version": agent.version,
        "description": agent.description,
        "protocol": "Agent Connect Protocol (ACP)",
        "endpoints": {
            "auth": "/auth",
            "schema": "/schema", 
            "config": "/config",
            "invoke": "/invoke",
            "capabilities": "/capabilities"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": time.time()}


# ACP Required Endpoints

@app.get("/auth", response_model=AuthInfo)
async def get_auth_info():
    """
    ACP Required: Authentication endpoint.
    Returns the authentication scheme supported by the agent.
    """
    return AuthInfo(
        type="none",
        description="This hello world agent does not require authentication"
    )


@app.get("/schema", response_model=SchemaDefinition)
async def get_schema():
    """
    ACP Required: Schema definitions endpoint.
    Returns JSON schemas for configuration, input, and output.
    """
    schemas = agent.get_schemas()
    return SchemaDefinition(
        input=schemas["input"],
        output=schemas["output"],
        config=schemas["config"]
    )


@app.post("/config", response_model=ConfigResponse)
async def create_config(request: ConfigRequest):
    """
    ACP Required: Configuration endpoint.
    Creates and stores agent configuration, returns configuration ID.
    """
    try:
        response = agent.store_config(request.config)
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")


@app.get("/config/{config_id}")
async def get_config(config_id: str):
    """Get a stored configuration by ID."""
    config = agent.get_config(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return {"config_id": config_id, "config": config}


@app.post("/invoke", response_model=InvokeResponse)
async def invoke_agent(request: InvokeRequest):
    """
    ACP Required: Invocation endpoint.
    Triggers the execution of the agent with provided input.
    """
    try:
        if request.stream:
            # Return streaming response
            return StreamingResponse(
                stream_response(request),
                media_type="text/plain",
                headers={"Content-Type": "text/event-stream"}
            )
        else:
            # Return regular response
            response = agent.invoke(request)
            return response
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


def stream_response(request: InvokeRequest) -> Iterator[str]:
    """Generate streaming response for agent invocation."""
    try:
        # Simulate streaming by sending partial updates
        yield f"data: {json.dumps({'status': 'started', 'message': 'Processing request...'})}\n\n"
        
        time.sleep(0.1)  # Small delay to simulate processing
        
        # Process the actual request
        response = agent.invoke(request)
        
        yield f"data: {json.dumps({'status': 'processing', 'message': 'Generating greeting...'})}\n\n"
        
        time.sleep(0.1)  # Small delay
        
        # Send the final response
        yield f"data: {json.dumps({'status': 'completed', 'result': response.model_dump()})}\n\n"
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        error_data = {"status": "error", "error": str(e)}
        yield f"data: {json.dumps(error_data)}\n\n"


@app.get("/capabilities")
async def get_capabilities():
    """
    ACP Required: Capabilities endpoint.
    Returns details about the specific capabilities that the agent supports.
    """
    capabilities = agent.get_capabilities()
    return capabilities.model_dump()


# Additional Helper Endpoints

@app.post("/hello")
async def simple_hello(input_data: HelloInput):
    """
    Simple endpoint for direct hello world functionality.
    This is a convenience endpoint that doesn't require full ACP structure.
    """
    try:
        output = agent.generate_greeting(input_data)
        return output.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/agent-info")
async def get_agent_info():
    """Get comprehensive agent information."""
    return {
        "agent_id": agent.agent_id,
        "agent_name": agent.agent_name,
        "version": agent.version,
        "description": agent.description,
        "capabilities": agent.get_capabilities().model_dump(),
        "schemas": agent.get_schemas(),
        "auth_info": AuthInfo().model_dump(),
        "supported_endpoints": [
            "/auth", "/schema", "/config", "/invoke", "/capabilities",
            "/hello", "/agent-info", "/health"
        ]
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            code=str(exc.status_code)
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            code="500",
            details={"message": str(exc)}
        ).model_dump()
    )


def create_app() -> FastAPI:
    """Factory function to create the FastAPI app."""
    return app


if __name__ == "__main__":
    uvicorn.run(
        "hello_agent.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )