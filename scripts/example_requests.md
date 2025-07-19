# API Request Examples

This document provides examples of how to interact with the Hello World Agent using various tools and methods.

## Prerequisites

Make sure the agent is running:
```bash
# Using Python directly
python -m uvicorn hello_agent.app:app --host 0.0.0.0 --port 8000

# Or using Docker
docker-compose up -d

# Or using Docker directly
docker run -p 8000:8000 hello-world-agent:latest
```

## Basic Examples

### 1. Health Check
```bash
curl -X GET "http://localhost:8000/health"
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1704067200.123
}
```

### 2. Agent Information
```bash
curl -X GET "http://localhost:8000/"
```

**Response:**
```json
{
  "agent": "Hello World Agent",
  "version": "0.1.0",
  "description": "A simple agent that generates greetings in multiple languages",
  "protocol": "Agent Connect Protocol (ACP)",
  "endpoints": {
    "auth": "/auth",
    "schema": "/schema",
    "config": "/config",
    "invoke": "/invoke",
    "capabilities": "/capabilities"
  }
}
```

## ACP Protocol Endpoints

### 3. Authentication Information (ACP Required)
```bash
curl -X GET "http://localhost:8000/auth"
```

**Response:**
```json
{
  "type": "none",
  "description": "This hello world agent does not require authentication"
}
```

### 4. Schema Definitions (ACP Required)
```bash
curl -X GET "http://localhost:8000/schema"
```

**Response:**
```json
{
  "input": {
    "type": "object",
    "properties": {
      "name": {"type": "string", "description": "Name to greet"},
      "message": {"type": "string", "description": "Custom greeting message"},
      "language": {"type": "string", "description": "Language for greeting"}
    }
  },
  "output": {
    "type": "object",
    "properties": {
      "greeting": {"type": "string", "description": "The generated greeting"},
      "timestamp": {"type": "string", "description": "When the greeting was generated"},
      "agent_id": {"type": "string", "description": "ID of the agent"}
    },
    "required": ["greeting", "timestamp", "agent_id"]
  },
  "config": {
    "type": "object",
    "properties": {
      "agent_name": {"type": "string", "description": "Name of the agent"},
      "default_language": {"type": "string", "description": "Default language"},
      "custom_greetings": {"type": "object", "description": "Custom greetings by language"}
    }
  }
}
```

### 5. Agent Capabilities (ACP Required)
```bash
curl -X GET "http://localhost:8000/capabilities"
```

**Response:**
```json
{
  "agent_id": "hello-world-agent",
  "agent_name": "Hello World Agent",
  "description": "A simple agent that generates greetings in multiple languages",
  "version": "0.1.0",
  "capabilities": [
    {
      "name": "generate_greeting",
      "description": "Generate a personalized greeting message",
      "input_schema": {...},
      "output_schema": {...}
    }
  ],
  "supported_languages": ["en", "es", "fr", "de", "it"]
}
```

### 6. Configuration Creation (ACP Required)
```bash
curl -X POST "http://localhost:8000/config" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "agent_name": "Custom Hello Agent",
      "default_language": "es",
      "custom_greetings": {
        "en": "Hi there",
        "es": "Hola",
        "fr": "Salut"
      }
    }
  }'
```

**Response:**
```json
{
  "config_id": "uuid-here",
  "config": {
    "agent_name": "Custom Hello Agent",
    "default_language": "es",
    "custom_greetings": {
      "en": "Hi there",
      "es": "Hola",
      "fr": "Salut"
    }
  },
  "created_at": "2024-01-01T12:00:00.000Z"
}
```

### 7. Agent Invocation (ACP Required)
```bash
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "name": "AGNTCY Community",
      "language": "en"
    }
  }'
```

**Response:**
```json
{
  "id": "run-uuid-here",
  "output": {
    "greeting": "Hello, AGNTCY Community!",
    "timestamp": "2024-01-01T12:00:00.000Z",
    "agent_id": "hello-world-agent"
  },
  "status": "completed",
  "metadata": {
    "agent_name": "Hello World Agent",
    "version": "0.1.0",
    "processing_time_ms": 1
  }
}
```

## Language Examples

### English Greeting
```bash
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "name": "World",
      "language": "en"
    }
  }'
```

### Spanish Greeting
```bash
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "name": "Mundo",
      "language": "es"
    }
  }'
```

### French Greeting
```bash
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "name": "Monde",
      "language": "fr"
    }
  }'
```

### German Greeting
```bash
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "name": "Welt",
      "language": "de"
    }
  }'
```

### Italian Greeting
```bash
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "name": "Mondo",
      "language": "it"
    }
  }'
```

### Custom Message
```bash
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "name": "Developer",
      "message": "Welcome to AGNTCY"
    }
  }'
```

## Simple Endpoint (Non-ACP)

### Direct Hello Request
```bash
curl -X POST "http://localhost:8000/hello" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Simple Test",
    "language": "en"
  }'
```

## Streaming Example

### Streaming Response
```bash
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "name": "Streaming Test",
      "language": "en"
    },
    "stream": true
  }'
```

## Python Examples

### Using requests library
```python
import requests

# Simple hello request
response = requests.post(
    "http://localhost:8000/hello",
    json={"name": "Python User", "language": "en"}
)
print(response.json())

# ACP invoke request
response = requests.post(
    "http://localhost:8000/invoke",
    json={
        "input": {"name": "Python User", "language": "fr"}
    }
)
print(response.json())
```

### Using httpx (async)
```python
import asyncio
import httpx

async def test_agent():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/invoke",
            json={
                "input": {"name": "Async User", "language": "es"}
            }
        )
        return response.json()

result = asyncio.run(test_agent())
print(result)
```

## JavaScript Examples

### Using fetch
```javascript
// Simple hello request
fetch('http://localhost:8000/hello', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        name: 'JavaScript User',
        language: 'en'
    })
})
.then(response => response.json())
.then(data => console.log(data));

// ACP invoke request
fetch('http://localhost:8000/invoke', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        input: {
            name: 'JS User',
            language: 'fr'
        }
    })
})
.then(response => response.json())
.then(data => console.log(data));
```

## Error Handling Examples

### Invalid Language
```bash
curl -X POST "http://localhost:8000/hello" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test",
    "language": "invalid"
  }'
```

### Missing Required Fields
```bash
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Invalid Endpoint
```bash
curl -X GET "http://localhost:8000/nonexistent"
```

## Testing with CLI

### Using the built-in CLI client
```bash
# Install dependencies first
cd /path/to/project
pip install -e .

# Test the agent
python -m hello_agent.simple_cli health
python -m hello_agent.simple_cli info
python -m hello_agent.simple_cli hello --name "CLI User" --language "es"
python -m hello_agent.simple_cli test
```

### Using the test script
```bash
./scripts/test_api.sh
```