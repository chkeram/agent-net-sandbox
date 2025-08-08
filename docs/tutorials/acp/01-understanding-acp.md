# Part 1: Understanding ACP Fundamentals

## 🎯 Learning Objectives

By the end of this tutorial, you will:
- Understand what the Agent Connect Protocol (ACP) is and why it matters
- Learn the core concepts and architectural patterns of ACP
- Identify required vs optional endpoints and their purposes
- Analyze a real ACP agent implementation from our repository
- Be ready to start building your own ACP-compliant agents

## 📚 Prerequisites

- Basic understanding of REST APIs
- Familiarity with Python (we'll use it for examples)
- Docker installed (optional, for running the example)

## 🌟 What is the Agent Connect Protocol?

The Agent Connect Protocol (ACP) is a standardized protocol developed by AGNTCY for building interoperable AI agents. It defines a consistent interface that allows agents to:

- **Discover** each other's capabilities
- **Communicate** using standardized endpoints
- **Configure** themselves dynamically
- **Execute** tasks in a predictable manner

Think of ACP as the "USB standard" for AI agents - it ensures any ACP-compliant agent can work with any ACP-compliant system.

## 🏗️ Core Architecture

An ACP agent is essentially a web service that implements specific endpoints. Let's examine our real implementation:

```python
# From agents/acp-hello-world/src/hello_agent/app.py

app = FastAPI(
    title="AGNTCY Hello World Agent",
    description="A simple hello world agent implementing the Agent Connect Protocol (ACP)",
    version="0.1.0"
)

# Root endpoint showing available ACP endpoints
@app.get("/")
async def root():
    return {
        "agent": agent.agent_name,
        "version": agent.version,
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

This shows the five required ACP endpoints that every agent MUST implement.

## 🔌 Required Endpoints

### 1. `/auth` - Authentication Information

**Purpose**: Declares what authentication the agent requires (if any).

**Real Implementation**:
```python
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
```

**Key Points**:
- Must return authentication requirements
- Can be "none" for public agents
- Supports various auth schemes (API keys, OAuth, etc.)

### 2. `/schema` - Data Schemas

**Purpose**: Provides JSON schemas for input, output, and configuration.

**Real Implementation**:
```python
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
```

**What It Returns**:
```json
{
  "input": {
    "type": "object",
    "properties": {
      "name": {"type": "string", "default": "World"},
      "language": {"type": "string", "enum": ["en", "es", "fr", "de", "it"]}
    }
  },
  "output": {
    "type": "object",
    "properties": {
      "greeting": {"type": "string"},
      "timestamp": {"type": "string", "format": "date-time"},
      "agent_id": {"type": "string"}
    }
  }
}
```

### 3. `/config` - Configuration Management

**Purpose**: Creates and stores agent configuration instances.

**Real Implementation**:
```python
@app.post("/config", response_model=ConfigResponse)
async def create_config(request: ConfigRequest):
    """
    ACP Required: Configuration endpoint.
    Creates and stores agent configuration, returns configuration ID.
    """
    response = agent.store_config(request.config)
    return response
```

**Usage Flow**:
1. Client sends configuration parameters
2. Agent validates and stores configuration
3. Returns a `config_id` for future reference
4. Client uses this ID when invoking the agent

### 4. `/invoke` - Task Execution

**Purpose**: The main execution endpoint where the agent performs its task.

**Real Implementation**:
```python
@app.post("/invoke", response_model=InvokeResponse)
async def invoke_agent(request: InvokeRequest):
    """
    ACP Required: Invocation endpoint.
    Executes the agent's main functionality with provided input.
    """
    # Validate input against schema
    if not agent.validate_input(request.input):
        raise HTTPException(status_code=400, detail="Invalid input")
    
    # Execute agent logic
    result = agent.execute(
        input_data=request.input,
        config_id=request.config_id
    )
    
    return InvokeResponse(
        output=result,
        metadata={
            "execution_time": time.time() - start_time,
            "agent_version": agent.version
        }
    )
```

### 5. `/capabilities` - Capability Discovery

**Purpose**: Describes what the agent can do.

**Real Implementation**:
```python
@app.get("/capabilities")
async def get_capabilities():
    """
    ACP Required: Capabilities endpoint.
    Returns the agent's capabilities and supported operations.
    """
    return {
        "capabilities": [
            {
                "name": "generate_greeting",
                "description": "Generate a personalized greeting message",
                "supported_languages": ["en", "es", "fr", "de", "it"],
                "features": ["personalization", "multi-language"]
            }
        ],
        "version": "0.1.0",
        "protocol_version": "acp/v0"
    }
```

## 🔄 Request Flow Example

Let's trace a complete interaction with our Hello World agent:

```bash
# 1. Check authentication requirements
curl http://localhost:8000/auth
# Response: {"type": "none", "description": "..."}

# 2. Get schemas to understand data format
curl http://localhost:8000/schema
# Response: {"input": {...}, "output": {...}, "config": {...}}

# 3. Create a configuration (optional)
curl -X POST http://localhost:8000/config \
  -H "Content-Type: application/json" \
  -d '{"config": {"default_language": "es"}}'
# Response: {"config_id": "cfg_123", "status": "created"}

# 4. Invoke the agent
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "input": {"name": "Maria", "language": "es"},
    "config_id": "cfg_123"
  }'
# Response: {
#   "output": {
#     "greeting": "¡Hola, Maria!",
#     "timestamp": "2024-01-15T10:30:00Z",
#     "agent_id": "hello-world-agent"
#   }
# }

# 5. Discover capabilities
curl http://localhost:8000/capabilities
# Response: {"capabilities": [...], "version": "0.1.0"}
```

## 📁 Real Agent Structure

Our `acp-hello-world` agent follows this structure:

```
agents/acp-hello-world/
├── agent-manifest.yaml      # Agent metadata and configuration
├── acp-descriptor.json      # Protocol-specific descriptor
├── Dockerfile              # Container definition
├── requirements.txt        # Python dependencies
└── src/
    └── hello_agent/
        ├── __init__.py
        ├── agent.py        # Core agent logic
        ├── app.py          # FastAPI application (ACP endpoints)
        └── models.py       # Pydantic models for type safety
```

## 🎭 Key Design Patterns

### 1. **Separation of Concerns**
- `app.py`: HTTP layer and ACP endpoint implementation
- `agent.py`: Business logic and agent functionality
- `models.py`: Data validation and type definitions

### 2. **Type Safety with Pydantic**
```python
from pydantic import BaseModel

class HelloInput(BaseModel):
    name: str = "World"
    language: str = "en"
    message: Optional[str] = None

class InvokeRequest(BaseModel):
    input: Dict[str, Any]
    config_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
```

### 3. **Stateless Design**
Each request is independent, configuration is stored separately, and agents can scale horizontally.

## 🔍 Optional Endpoints

While not required, these enhance functionality:

### `/health` - Health Check
```python
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": time.time()}
```

### Streaming Support
For long-running operations:
```python
@app.post("/invoke/stream")
async def invoke_stream(request: InvokeRequest):
    async def generate():
        for chunk in agent.execute_streaming(request.input):
            yield f"data: {json.dumps(chunk)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

## 🚀 Running the Example

To see ACP in action with our Hello World agent:

```bash
# Using Docker
docker-compose up acp-hello-world

# Or run locally (in virtual environment)
cd agents/acp-hello-world
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
export PYTHONPATH=src
python -m uvicorn hello_agent.app:app --port 8000
```

Test the agent:
```bash
# Check it's running
curl http://localhost:8000/health

# Invoke it
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{"input": {"name": "Developer", "language": "en"}}'
```

## 📝 Key Takeaways

1. **ACP is a contract** - Your agent promises to implement these endpoints
2. **Five required endpoints** - auth, schema, config, invoke, capabilities
3. **Predictable interface** - Any ACP client can work with any ACP agent
4. **Type safety matters** - Use Pydantic models for validation
5. **Stateless by design** - Enables scaling and reliability

## 🎓 Exercises

1. **Explore the agent**: Run the Hello World agent and call each endpoint
2. **Modify greetings**: Add a new language to the agent
3. **Test error handling**: Send invalid input and observe the response
4. **Check the schemas**: Validate that input/output match the schemas

## 📚 Additional Resources

- [Official ACP Documentation](https://docs.agntcy.org/)
- [ACP Specification](https://spec.acp.agntcy.org/)
- [Python SDK Documentation](https://agntcy.github.io/acp-sdk/html/index.html)
- [Our Implementation](https://github.com/chkeram/agent-net-sandbox/tree/main/agents/acp-hello-world)

## ⏭️ Next Steps

In [Part 2: Configuration & Discovery](./02-configuration-discovery.md), we'll dive deep into:
- The `agent-manifest.yaml` structure
- The `acp-descriptor.json` format
- How agents advertise their capabilities
- Integration with discovery services

Ready to continue? You now understand the fundamental building blocks of ACP!

---

*This tutorial is part of the Agent Network Sandbox educational series. All code examples are from our production-ready implementations.*