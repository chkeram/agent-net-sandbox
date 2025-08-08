#!/usr/bin/env python3
"""
Minimal ACP Agent Example

A bare-bones implementation showing the five required endpoints
for ACP protocol compliance. This is the simplest possible agent
that still follows the protocol specification.

Usage:
    python minimal-agent.py

Test with:
    curl http://localhost:8000/auth
    curl http://localhost:8000/schema  
    curl -X POST http://localhost:8000/config -H "Content-Type: application/json" -d '{}'
    curl -X POST http://localhost:8000/invoke -H "Content-Type: application/json" -d '{"input": {}}'
    curl http://localhost:8000/capabilities
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid
import time

# Simple data models
class ConfigRequest(BaseModel):
    config: Dict[str, Any] = {}

class InvokeRequest(BaseModel):
    input: Dict[str, Any]
    config_id: Optional[str] = None

# Create FastAPI app
app = FastAPI(
    title="Minimal ACP Agent",
    description="The simplest possible ACP-compliant agent",
    version="0.1.0"
)

# Simple in-memory storage
configs = {}

# Root endpoint (optional but helpful)
@app.get("/")
async def root():
    """Basic agent info."""
    return {
        "agent": "Minimal ACP Agent",
        "version": "0.1.0",
        "protocol": "acp/v0",
        "endpoints": ["auth", "schema", "config", "invoke", "capabilities"]
    }

# Health check (optional but recommended)
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

# ACP Required Endpoint 1: Authentication
@app.get("/auth")
async def auth():
    """Return authentication requirements."""
    return {
        "type": "none",
        "description": "No authentication required for this minimal agent"
    }

# ACP Required Endpoint 2: Schema
@app.get("/schema")
async def schema():
    """Return input, output, and config schemas."""
    return {
        "input": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Message to echo back"
                }
            }
        },
        "output": {
            "type": "object",
            "properties": {
                "echo": {
                    "type": "string",
                    "description": "Echoed message"
                },
                "timestamp": {
                    "type": "number",
                    "description": "Processing timestamp"
                }
            }
        },
        "config": {
            "type": "object",
            "properties": {
                "prefix": {
                    "type": "string",
                    "description": "Prefix to add to messages",
                    "default": "Echo: "
                }
            }
        }
    }

# ACP Required Endpoint 3: Configuration
@app.post("/config")
async def create_config(request: ConfigRequest):
    """Store configuration and return config ID."""
    config_id = f"cfg_{uuid.uuid4().hex[:8]}"
    configs[config_id] = request.config
    
    return {
        "config_id": config_id,
        "status": "created",
        "timestamp": time.time()
    }

# ACP Required Endpoint 4: Invocation
@app.post("/invoke")
async def invoke(request: InvokeRequest):
    """Execute the agent's main function."""
    # Get configuration if provided
    config = configs.get(request.config_id, {})
    prefix = config.get("prefix", "Echo: ")
    
    # Get message from input
    message = request.input.get("message", "Hello, ACP!")
    
    # Process (simple echo with prefix)
    result = f"{prefix}{message}"
    
    # Return output
    return {
        "output": {
            "echo": result,
            "timestamp": time.time()
        }
    }

# ACP Required Endpoint 5: Capabilities
@app.get("/capabilities")
async def capabilities():
    """Return agent capabilities."""
    return {
        "capabilities": [
            {
                "name": "echo",
                "description": "Echo back a message with optional prefix",
                "version": "0.1.0"
            }
        ],
        "version": "0.1.0",
        "protocol_version": "acp/v0"
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting Minimal ACP Agent...")
    print("Available endpoints:")
    print("  GET  /auth")
    print("  GET  /schema")
    print("  POST /config")
    print("  POST /invoke")
    print("  GET  /capabilities")
    print("\nAgent running at: http://localhost:8000")
    print("API docs available at: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)