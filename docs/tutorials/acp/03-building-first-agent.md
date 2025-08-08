# Part 3: Building Your First ACP Agent

## 🎯 Learning Objectives

By the end of this tutorial, you will:
- Build a complete ACP-compliant agent from scratch
- Implement all five required endpoints
- Use Pydantic for robust type validation
- Handle errors gracefully
- Test your agent with real requests
- Deploy using Docker

## 📚 Prerequisites

- Completed Parts 1 and 2 of this series
- Python 3.11+ installed
- Basic FastAPI knowledge
- Docker installed (for deployment)

## 🏗️ What We're Building

We'll create a **Weather Advisory Agent** that:
- Provides weather-based recommendations
- Supports multiple cities
- Returns activity suggestions based on conditions
- Fully complies with ACP protocol

## 📁 Project Structure

Let's start by creating our project structure:

```bash
mkdir -p agents/acp-weather-advisor
cd agents/acp-weather-advisor
```

Create this structure:
```
agents/acp-weather-advisor/
├── agent-manifest.yaml
├── acp-descriptor.json
├── Dockerfile
├── requirements.txt
├── src/
│   └── weather_advisor/
│       ├── __init__.py
│       ├── agent.py
│       ├── app.py
│       └── models.py
└── tests/
    └── test_agent.py
```

## 🔧 Step 1: Set Up Dependencies

Create `requirements.txt`:

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pyyaml==6.0.1
python-json-logger==2.0.7
httpx==0.25.1
```

Set up virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 📝 Step 2: Define Data Models

Create `src/weather_advisor/models.py`:

```python
"""Pydantic models for ACP protocol compliance."""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


# ACP Protocol Models
class AuthInfo(BaseModel):
    """Authentication information model."""
    type: str = Field(..., description="Authentication type")
    description: str = Field(..., description="Authentication description")
    required: bool = Field(default=False, description="Is authentication required")


class SchemaDefinition(BaseModel):
    """Schema definition for input, output, and config."""
    input: Dict[str, Any] = Field(..., description="Input JSON schema")
    output: Dict[str, Any] = Field(..., description="Output JSON schema")
    config: Dict[str, Any] = Field(..., description="Configuration JSON schema")


class ConfigRequest(BaseModel):
    """Configuration request model."""
    config: Dict[str, Any] = Field(..., description="Configuration parameters")
    metadata: Optional[Dict[str, Any]] = Field(default=None)


class ConfigResponse(BaseModel):
    """Configuration response model."""
    config_id: str = Field(..., description="Unique configuration ID")
    status: str = Field(..., description="Configuration status")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class InvokeRequest(BaseModel):
    """Agent invocation request."""
    input: Dict[str, Any] = Field(..., description="Input data")
    config_id: Optional[str] = Field(default=None, description="Configuration ID")
    metadata: Optional[Dict[str, Any]] = Field(default=None)


class InvokeResponse(BaseModel):
    """Agent invocation response."""
    output: Dict[str, Any] = Field(..., description="Output data")
    metadata: Optional[Dict[str, Any]] = Field(default=None)
    execution_time: Optional[float] = Field(default=None)


# Agent-Specific Models
class WeatherInput(BaseModel):
    """Input model for weather advisor."""
    city: str = Field(..., description="City name")
    activity_type: str = Field(
        default="general",
        description="Type of activity",
        pattern="^(general|outdoor|indoor|sports|travel)$"
    )
    temperature_preference: str = Field(
        default="moderate",
        description="Temperature preference",
        pattern="^(cold|moderate|warm)$"
    )


class WeatherOutput(BaseModel):
    """Output model for weather advisor."""
    city: str = Field(..., description="City name")
    weather_condition: str = Field(..., description="Current weather condition")
    temperature: float = Field(..., description="Temperature in Celsius")
    recommendation: str = Field(..., description="Activity recommendation")
    confidence: float = Field(..., description="Recommendation confidence (0-1)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_id: str = Field(default="weather-advisor-agent")


class AgentConfig(BaseModel):
    """Agent configuration model."""
    default_units: str = Field(default="celsius", pattern="^(celsius|fahrenheit)$")
    include_forecast: bool = Field(default=False)
    max_recommendations: int = Field(default=3, ge=1, le=10)
    language: str = Field(default="en", pattern="^(en|es|fr|de)$")
```

## 🤖 Step 3: Implement Agent Logic

Create `src/weather_advisor/agent.py`:

```python
"""Core agent logic for Weather Advisor."""

import json
import yaml
import uuid
import random
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from .models import WeatherInput, WeatherOutput, AgentConfig


class WeatherAdvisorAgent:
    """Weather Advisory Agent implementation."""
    
    def __init__(self):
        self.agent_id = "weather-advisor-agent"
        self.agent_name = "Weather Advisor Agent"
        self.version = "0.1.0"
        self.description = "Provides weather-based activity recommendations"
        
        # Load configuration files
        self.manifest = self._load_manifest()
        self.descriptor = self._load_descriptor()
        
        # Configuration storage
        self.config_store: Dict[str, AgentConfig] = {}
        
        # Simulated weather data (in production, use real API)
        self.weather_data = {
            "london": {"condition": "rainy", "temp": 12},
            "paris": {"condition": "cloudy", "temp": 15},
            "new york": {"condition": "sunny", "temp": 22},
            "tokyo": {"condition": "clear", "temp": 18},
            "sydney": {"condition": "windy", "temp": 25},
        }
        
        self.recommendations = {
            "rainy": {
                "indoor": "Visit a museum or art gallery",
                "outdoor": "Bring an umbrella and enjoy a walk in the rain",
                "sports": "Try indoor rock climbing or swimming",
                "travel": "Consider postponing or use covered transport",
                "general": "Perfect day for indoor activities"
            },
            "sunny": {
                "indoor": "Open windows for natural light while working",
                "outdoor": "Great day for hiking or picnic",
                "sports": "Perfect for cycling or running",
                "travel": "Ideal conditions for sightseeing",
                "general": "Enjoy outdoor activities with sun protection"
            },
            "cloudy": {
                "indoor": "Good lighting for reading or studying",
                "outdoor": "Comfortable for long walks",
                "sports": "Great for endurance activities",
                "travel": "Pleasant conditions for exploring",
                "general": "Mild conditions suitable for most activities"
            },
            "clear": {
                "indoor": "Take breaks to enjoy the clear weather",
                "outdoor": "Perfect for photography or stargazing",
                "sports": "Excellent visibility for outdoor sports",
                "travel": "Outstanding conditions for any journey",
                "general": "Make the most of the beautiful weather"
            },
            "windy": {
                "indoor": "Stay cozy indoors with warm drinks",
                "outdoor": "Try kite flying or wind surfing",
                "sports": "Good for sailing or paragliding",
                "travel": "Check wind conditions for your route",
                "general": "Dress in layers and secure loose items"
            }
        }
    
    def _load_manifest(self) -> Dict[str, Any]:
        """Load agent manifest from YAML file."""
        manifest_path = Path(__file__).parent.parent.parent / "agent-manifest.yaml"
        if manifest_path.exists():
            with open(manifest_path, "r") as f:
                return yaml.safe_load(f)
        return self._default_manifest()
    
    def _load_descriptor(self) -> Dict[str, Any]:
        """Load ACP descriptor from JSON file."""
        descriptor_path = Path(__file__).parent.parent.parent / "acp-descriptor.json"
        if descriptor_path.exists():
            with open(descriptor_path, "r") as f:
                return json.load(f)
        return self._default_descriptor()
    
    def _default_manifest(self) -> Dict[str, Any]:
        """Return default manifest structure."""
        return {
            "apiVersion": "agntcy.org/v1",
            "kind": "AgentManifest",
            "metadata": {
                "name": self.agent_id,
                "version": self.version,
                "description": self.description
            },
            "spec": {
                "capabilities": [{
                    "name": "weather_advisory",
                    "inputSchema": WeatherInput.model_json_schema(),
                    "outputSchema": WeatherOutput.model_json_schema()
                }],
                "configuration": {
                    "schema": AgentConfig.model_json_schema()
                }
            }
        }
    
    def _default_descriptor(self) -> Dict[str, Any]:
        """Return default ACP descriptor."""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "version": self.version,
            "protocol_version": "acp/v0",
            "base_url": "http://localhost:8000"
        }
    
    def get_schemas(self) -> Dict[str, Any]:
        """Get input, output, and config schemas."""
        return {
            "input": WeatherInput.model_json_schema(),
            "output": WeatherOutput.model_json_schema(),
            "config": AgentConfig.model_json_schema()
        }
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input against schema."""
        try:
            WeatherInput(**input_data)
            return True
        except Exception:
            return False
    
    def store_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store configuration and return config ID."""
        try:
            config = AgentConfig(**config_data)
            config_id = f"cfg_{uuid.uuid4().hex[:8]}"
            self.config_store[config_id] = config
            
            return {
                "config_id": config_id,
                "status": "created",
                "created_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise ValueError(f"Invalid configuration: {str(e)}")
    
    def get_config(self, config_id: str) -> Optional[AgentConfig]:
        """Retrieve stored configuration."""
        return self.config_store.get(config_id)
    
    def execute(self, input_data: Dict[str, Any], config_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute agent logic with input data."""
        # Parse and validate input
        weather_input = WeatherInput(**input_data)
        
        # Get configuration if provided
        config = self.get_config(config_id) if config_id else AgentConfig()
        
        # Get weather data (simulated)
        city_key = weather_input.city.lower()
        if city_key not in self.weather_data:
            # Simulate random weather for unknown cities
            conditions = ["sunny", "cloudy", "rainy", "clear", "windy"]
            weather = {
                "condition": random.choice(conditions),
                "temp": random.uniform(10, 30)
            }
        else:
            weather = self.weather_data[city_key]
        
        # Get recommendation
        condition = weather["condition"]
        activity = weather_input.activity_type
        recommendation = self.recommendations.get(
            condition, {}
        ).get(
            activity, "Check local weather service for details"
        )
        
        # Convert temperature if needed
        temperature = weather["temp"]
        if config.default_units == "fahrenheit":
            temperature = (temperature * 9/5) + 32
        
        # Build output
        output = WeatherOutput(
            city=weather_input.city,
            weather_condition=condition,
            temperature=temperature,
            recommendation=recommendation,
            confidence=0.85 if city_key in self.weather_data else 0.60
        )
        
        return output.model_dump()
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities."""
        return {
            "capabilities": [
                {
                    "name": "weather_advisory",
                    "description": "Provides weather-based activity recommendations",
                    "supported_cities": list(self.weather_data.keys()),
                    "activity_types": ["general", "outdoor", "indoor", "sports", "travel"],
                    "features": ["multi-city", "activity-specific", "confidence-scoring"]
                }
            ],
            "version": self.version,
            "protocol_version": "acp/v0"
        }
```

## 🌐 Step 4: Create FastAPI Application

Create `src/weather_advisor/app.py`:

```python
"""FastAPI application implementing ACP endpoints."""

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import time
import asyncio
from typing import Dict, Any, AsyncIterator

from .agent import WeatherAdvisorAgent
from .models import (
    AuthInfo, SchemaDefinition, ConfigRequest, ConfigResponse,
    InvokeRequest, InvokeResponse
)


# Initialize agent
agent = WeatherAdvisorAgent()

# Create FastAPI app
app = FastAPI(
    title="Weather Advisor Agent",
    description="An ACP-compliant agent providing weather-based recommendations",
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
    """Root endpoint providing agent information."""
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
            "capabilities": "/capabilities",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent_id": agent.agent_id,
        "version": agent.version,
        "timestamp": time.time()
    }


# ACP Required Endpoints

@app.get("/auth", response_model=AuthInfo)
async def get_auth_info():
    """ACP Required: Authentication endpoint."""
    return AuthInfo(
        type="none",
        description="This weather advisor agent does not require authentication",
        required=False
    )


@app.get("/schema", response_model=SchemaDefinition)
async def get_schema():
    """ACP Required: Schema definitions endpoint."""
    schemas = agent.get_schemas()
    return SchemaDefinition(
        input=schemas["input"],
        output=schemas["output"],
        config=schemas["config"]
    )


@app.post("/config", response_model=ConfigResponse)
async def create_config(request: ConfigRequest):
    """ACP Required: Configuration endpoint."""
    try:
        result = agent.store_config(request.config)
        return ConfigResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")


@app.post("/invoke", response_model=InvokeResponse)
async def invoke_agent(request: InvokeRequest):
    """ACP Required: Invocation endpoint."""
    start_time = time.time()
    
    # Validate input
    if not agent.validate_input(request.input):
        raise HTTPException(
            status_code=400,
            detail="Invalid input. Please check the schema."
        )
    
    try:
        # Execute agent logic
        output = agent.execute(
            input_data=request.input,
            config_id=request.config_id
        )
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        return InvokeResponse(
            output=output,
            metadata={
                "execution_time": execution_time,
                "agent_version": agent.version,
                "protocol_version": "acp/v0"
            },
            execution_time=execution_time
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Execution error: {str(e)}"
        )


@app.get("/capabilities")
async def get_capabilities():
    """ACP Required: Capabilities endpoint."""
    return agent.get_capabilities()


# Optional: Streaming endpoint for real-time updates
@app.post("/invoke/stream")
async def invoke_stream(request: InvokeRequest):
    """Optional: Streaming invocation for real-time updates."""
    
    async def generate_stream() -> AsyncIterator[str]:
        """Generate streaming response."""
        # Validate input
        if not agent.validate_input(request.input):
            yield f"data: {json.dumps({'error': 'Invalid input'})}\n\n"
            return
        
        # Start processing
        yield f"data: {json.dumps({'status': 'processing', 'message': 'Analyzing weather data...'})}\n\n"
        await asyncio.sleep(0.5)
        
        # Get weather data
        yield f"data: {json.dumps({'status': 'fetching', 'message': 'Fetching current conditions...'})}\n\n"
        await asyncio.sleep(0.5)
        
        # Execute logic
        try:
            output = agent.execute(request.input, request.config_id)
            yield f"data: {json.dumps({'status': 'complete', 'output': output})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The endpoint {request.url.path} does not exist",
            "available_endpoints": [
                "/auth", "/schema", "/config", "/invoke", "/capabilities"
            ]
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "agent_id": agent.agent_id
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 📋 Step 5: Create Configuration Files

Create `agent-manifest.yaml`:

```yaml
apiVersion: agntcy.org/v1
kind: AgentManifest
metadata:
  name: weather-advisor-agent
  version: "0.1.0"
  description: "Weather-based activity recommendation agent"
  author: "Your Name"
  license: "Apache-2.0"
  tags:
    - weather
    - advisory
    - recommendations
    - acp

spec:
  agent:
    id: weather-advisor-agent
    name: "Weather Advisor Agent"
    description: "Provides weather-based activity recommendations"
    version: "0.1.0"
    
  capabilities:
    - name: weather_advisory
      description: "Generate weather-based activity recommendations"
      inputSchema:
        type: object
        properties:
          city:
            type: string
            description: "City name"
          activity_type:
            type: string
            description: "Type of activity"
            enum: ["general", "outdoor", "indoor", "sports", "travel"]
            default: "general"
          temperature_preference:
            type: string
            description: "Temperature preference"
            enum: ["cold", "moderate", "warm"]
            default: "moderate"
        required:
          - city
      outputSchema:
        type: object
        properties:
          city:
            type: string
          weather_condition:
            type: string
          temperature:
            type: number
          recommendation:
            type: string
          confidence:
            type: number
          timestamp:
            type: string
            format: date-time
          agent_id:
            type: string
        required:
          - city
          - weather_condition
          - temperature
          - recommendation

  configuration:
    schema:
      type: object
      properties:
        default_units:
          type: string
          enum: ["celsius", "fahrenheit"]
          default: "celsius"
        include_forecast:
          type: boolean
          default: false
        max_recommendations:
          type: integer
          minimum: 1
          maximum: 10
          default: 3
        language:
          type: string
          enum: ["en", "es", "fr", "de"]
          default: "en"

  endpoints:
    base_url: "http://localhost:8000"
    protocol: acp
    version: v0
    paths:
      auth: "/auth"
      schema: "/schema"
      config: "/config"
      invoke: "/invoke"
      capabilities: "/capabilities"

  discovery:
    enabled: true
    keywords:
      - weather
      - advisory
      - recommendations
      - activity
    categories:
      - utility
      - information
```

Create `acp-descriptor.json`:

```json
{
  "agent_id": "weather-advisor-agent",
  "agent_name": "Weather Advisor Agent",
  "version": "0.1.0",
  "description": "Provides weather-based activity recommendations",
  "protocol_version": "acp/v0",
  "base_url": "http://localhost:8000",
  
  "metadata": {
    "author": "Your Name",
    "license": "Apache-2.0",
    "tags": ["weather", "advisory", "recommendations", "acp"],
    "categories": ["utility", "information"]
  },

  "authentication": {
    "type": "none",
    "description": "No authentication required"
  },

  "endpoints": {
    "auth": {
      "path": "/auth",
      "method": "GET"
    },
    "schema": {
      "path": "/schema",
      "method": "GET"
    },
    "config": {
      "path": "/config",
      "method": "POST"
    },
    "invoke": {
      "path": "/invoke",
      "method": "POST",
      "supports_streaming": true
    },
    "capabilities": {
      "path": "/capabilities",
      "method": "GET"
    }
  },

  "supported_features": {
    "streaming": true,
    "configuration": true,
    "discovery": true,
    "health_check": true
  }
}
```

## 🐳 Step 6: Create Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY agent-manifest.yaml .
COPY acp-descriptor.json .

# Set Python path
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "weather_advisor.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🧪 Step 7: Test Your Agent

Create `tests/test_agent.py`:

```python
"""Tests for Weather Advisor Agent."""

import pytest
import httpx
import json


BASE_URL = "http://localhost:8000"


def test_health_endpoint():
    """Test health check endpoint."""
    response = httpx.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "agent_id" in data


def test_auth_endpoint():
    """Test authentication endpoint."""
    response = httpx.get(f"{BASE_URL}/auth")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "none"
    assert data["required"] == False


def test_schema_endpoint():
    """Test schema endpoint."""
    response = httpx.get(f"{BASE_URL}/schema")
    assert response.status_code == 200
    data = response.json()
    assert "input" in data
    assert "output" in data
    assert "config" in data


def test_capabilities_endpoint():
    """Test capabilities endpoint."""
    response = httpx.get(f"{BASE_URL}/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert "capabilities" in data
    assert len(data["capabilities"]) > 0


def test_config_creation():
    """Test configuration creation."""
    config_data = {
        "config": {
            "default_units": "fahrenheit",
            "include_forecast": True,
            "max_recommendations": 5
        }
    }
    response = httpx.post(f"{BASE_URL}/config", json=config_data)
    assert response.status_code == 200
    data = response.json()
    assert "config_id" in data
    assert data["status"] == "created"
    return data["config_id"]


def test_invoke_endpoint():
    """Test agent invocation."""
    invoke_data = {
        "input": {
            "city": "London",
            "activity_type": "outdoor"
        }
    }
    response = httpx.post(f"{BASE_URL}/invoke", json=invoke_data)
    assert response.status_code == 200
    data = response.json()
    assert "output" in data
    output = data["output"]
    assert output["city"] == "London"
    assert "recommendation" in output
    assert "weather_condition" in output


def test_invoke_with_config():
    """Test invocation with configuration."""
    # Create config
    config_id = test_config_creation()
    
    # Invoke with config
    invoke_data = {
        "input": {
            "city": "Paris",
            "activity_type": "indoor"
        },
        "config_id": config_id
    }
    response = httpx.post(f"{BASE_URL}/invoke", json=invoke_data)
    assert response.status_code == 200
    data = response.json()
    output = data["output"]
    # Temperature should be in Fahrenheit due to config
    assert output["temperature"] > 32  # Above freezing in Fahrenheit


def test_invalid_input():
    """Test error handling for invalid input."""
    invoke_data = {
        "input": {
            "invalid_field": "test"
        }
    }
    response = httpx.post(f"{BASE_URL}/invoke", json=invoke_data)
    assert response.status_code == 400


if __name__ == "__main__":
    # Run basic smoke test
    print("Testing Weather Advisor Agent...")
    test_health_endpoint()
    print("✓ Health check passed")
    test_auth_endpoint()
    print("✓ Auth endpoint passed")
    test_schema_endpoint()
    print("✓ Schema endpoint passed")
    test_capabilities_endpoint()
    print("✓ Capabilities endpoint passed")
    test_invoke_endpoint()
    print("✓ Invocation passed")
    print("\n✅ All tests passed!")
```

## 🚀 Step 8: Run Your Agent

### Local Development

```bash
# Activate virtual environment
source venv/bin/activate

# Set Python path
export PYTHONPATH=src

# Run the agent
python -m uvicorn weather_advisor.app:app --reload --port 8000
```

### Docker Deployment

```bash
# Build Docker image
docker build -t weather-advisor-agent .

# Run container
docker run -p 8000:8000 weather-advisor-agent
```

## 🧪 Step 9: Manual Testing

Test all endpoints:

```bash
# 1. Check health
curl http://localhost:8000/health | jq

# 2. Get authentication info
curl http://localhost:8000/auth | jq

# 3. Get schemas
curl http://localhost:8000/schema | jq

# 4. Check capabilities
curl http://localhost:8000/capabilities | jq

# 5. Create configuration
curl -X POST http://localhost:8000/config \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "default_units": "fahrenheit",
      "language": "en"
    }
  }' | jq

# 6. Invoke the agent
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "city": "London",
      "activity_type": "outdoor"
    }
  }' | jq

# 7. Test streaming (optional)
curl -X POST http://localhost:8000/invoke/stream \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "city": "Paris",
      "activity_type": "indoor"
    }
  }'
```

## 🎯 Success Checklist

Your agent is ACP-compliant if:

- [ ] All 5 required endpoints are implemented
- [ ] Input/output match declared schemas
- [ ] Configuration management works
- [ ] Error handling returns proper HTTP codes
- [ ] Health check endpoint responds
- [ ] agent-manifest.yaml is valid
- [ ] acp-descriptor.json is valid
- [ ] Docker container builds and runs
- [ ] All tests pass

## 🐛 Common Issues and Solutions

### Issue: Schema validation fails
**Solution**: Ensure Pydantic models match the schemas in manifest

### Issue: Config ID not found
**Solution**: Store configs in persistent storage for production

### Issue: Docker build fails
**Solution**: Check Python version and dependency compatibility

### Issue: Streaming doesn't work
**Solution**: Ensure client supports SSE (Server-Sent Events)

## 🎓 Exercises

1. **Add persistence**: Store configurations in a database
2. **Real weather API**: Integrate with OpenWeatherMap API
3. **Add authentication**: Implement API key authentication
4. **Enhance recommendations**: Use ML for better suggestions
5. **Add caching**: Cache weather data for performance

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic V2 Documentation](https://docs.pydantic.dev/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [ACP Testing Guide](https://docs.agntcy.org/testing)

## ⏭️ Next Steps

Congratulations! You've built a complete ACP-compliant agent. In [Part 4: Advanced Features](./04-advanced-features.md), we'll explore:
- Streaming responses for real-time data
- Advanced configuration management
- Integration with the orchestrator
- Performance optimization
- Production deployment strategies

Your Weather Advisor Agent is now ready to be discovered and used by any ACP-compatible system!

---

*This tutorial is part of the Agent Network Sandbox educational series. All patterns follow official ACP specifications.*