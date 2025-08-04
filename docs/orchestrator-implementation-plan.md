# Multi-Protocol Agent Orchestrator: Implementation Plan

## Overview

This document provides the complete implementation plan for the Multi-Protocol Agent Orchestrator, the central hub that discovers and routes requests to specialized agents across multiple protocols (ACP, A2A, MCP).

## Technology Stack

### Core Dependencies (August 2025)
```txt
pydantic-ai==0.4.11              # Agent framework with multi-LLM support
fastapi>=0.110.0                 # Web framework
uvicorn[standard]==0.35.0        # ASGI server with HTTP/2 support
httpx[http2]>=0.25.0            # Async HTTP client with HTTP/2
pydantic>=2.5.0                 # Data validation
pydantic-settings>=2.0.0        # Settings management
python-dotenv>=1.0.0            # Environment variables
docker>=7.0.0                   # Docker SDK for discovery
structlog>=23.0.0               # Structured logging
prometheus-client>=0.17.0       # Metrics collection
```

### Development Dependencies
```txt
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-mock>=3.12.0
black>=23.0.0
ruff>=0.1.0
mypy>=1.8.0
```

## Project Structure

```
agents/orchestrator/
├── Dockerfile                   # Multi-stage Docker build
├── README.md                   # Agent documentation
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Development dependencies
├── pyproject.toml             # Project configuration
├── .env.example               # Environment variables template
├── src/
│   └── orchestrator/
│       ├── __init__.py
│       ├── app.py             # FastAPI application
│       ├── agent.py           # Pydantic AI agent logic
│       ├── config.py          # Configuration management
│       ├── models.py          # Pydantic data models
│       ├── discovery.py       # Multi-protocol discovery
│       ├── routing.py         # Request routing engine
│       ├── protocols/         # Protocol-specific clients
│       │   ├── __init__.py
│       │   ├── base.py        # Abstract protocol interface
│       │   ├── acp_client.py  # ACP protocol implementation
│       │   ├── a2a_client.py  # A2A protocol implementation
│       │   └── mcp_client.py  # MCP protocol implementation
│       ├── tools/             # Pydantic AI tools
│       │   ├── __init__.py
│       │   ├── discovery_tools.py
│       │   └── routing_tools.py
│       └── utils/             # Utility functions
│           ├── __init__.py
│           ├── logging.py
│           └── metrics.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Pytest fixtures
│   ├── test_agent.py         # Agent logic tests
│   ├── test_discovery.py     # Discovery service tests
│   ├── test_routing.py       # Routing engine tests
│   └── test_integration.py   # End-to-end tests
└── scripts/
    ├── test_orchestrator.sh   # Testing script
    └── demo_routing.py        # Demo script
```

## Component Implementation Details

### 1. Configuration Management (config.py)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Literal
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    
    # Application settings
    app_name: str = "Multi-Protocol Agent Orchestrator"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # LLM Provider settings
    llm_provider: Literal["openai", "anthropic", "both"] = "both"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    default_model_temperature: float = 0.7
    
    # OpenAI specific
    openai_model: str = "gpt-4o"
    openai_max_tokens: int = 4096
    
    # Anthropic specific
    anthropic_model: str = "claude-3-5-sonnet-20240620"
    anthropic_max_tokens: int = 4096
    
    # Discovery settings
    discovery_interval_seconds: int = 30
    discovery_timeout_seconds: int = 5
    docker_network: str = "agent-network"
    
    # Routing settings
    routing_timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    
    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090

@lru_cache()
def get_settings():
    return Settings()
```

### 2. Data Models (models.py)

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
from enum import Enum

class ProtocolType(str, Enum):
    ACP = "acp"
    A2A = "a2a"
    MCP = "mcp"
    CUSTOM = "custom"

class AgentStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class AgentCapability(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., description="Capability name")
    description: str = Field(..., description="What this capability does")
    input_schema: Optional[Dict[str, Any]] = Field(None, description="Expected input format")
    output_schema: Optional[Dict[str, Any]] = Field(None, description="Expected output format")
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="Usage examples")

class DiscoveredAgent(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    agent_id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Human-readable agent name")
    protocol: ProtocolType = Field(..., description="Communication protocol")
    endpoint: str = Field(..., description="Agent endpoint URL")
    capabilities: List[AgentCapability] = Field(default_factory=list)
    status: AgentStatus = Field(AgentStatus.UNKNOWN)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    last_health_check: Optional[datetime] = None
    container_id: Optional[str] = None
    version: Optional[str] = None

class RoutingRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str = Field(..., description="User's request to be routed")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    preferred_protocol: Optional[ProtocolType] = None
    timeout_seconds: Optional[float] = None

class RoutingDecision(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    request_id: str
    selected_agent: Optional[DiscoveredAgent] = None
    reasoning: str = Field(..., description="Explanation of routing decision")
    confidence: float = Field(..., ge=0.0, le=1.0)
    alternative_agents: List[DiscoveredAgent] = Field(default_factory=list)
    error: Optional[str] = None

class AgentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    request_id: str
    agent_id: str
    protocol: ProtocolType
    response_data: Any
    duration_ms: float
    success: bool
    error: Optional[str] = None
```

### 3. Pydantic AI Agent (agent.py)

```python
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.anthropic import AnthropicModel
from typing import List, Optional, Union
import structlog

from .models import RoutingRequest, RoutingDecision, DiscoveredAgent
from .config import get_settings

logger = structlog.get_logger()

class OrchestrationAgent:
    def __init__(self):
        self.settings = get_settings()
        self.agent = self._create_agent()
        
    def _create_agent(self) -> Agent[RoutingDecision, None]:
        """Create the Pydantic AI agent with multi-model support"""
        models = []
        
        if self.settings.llm_provider in ["openai", "both"] and self.settings.openai_api_key:
            models.append(
                OpenAIModel(
                    self.settings.openai_model,
                    api_key=self.settings.openai_api_key,
                    temperature=self.settings.default_model_temperature,
                    max_tokens=self.settings.openai_max_tokens
                )
            )
            
        if self.settings.llm_provider in ["anthropic", "both"] and self.settings.anthropic_api_key:
            models.append(
                AnthropicModel(
                    self.settings.anthropic_model,
                    api_key=self.settings.anthropic_api_key,
                    temperature=self.settings.default_model_temperature,
                    max_tokens=self.settings.anthropic_max_tokens
                )
            )
            
        if not models:
            raise ValueError("No LLM provider configured. Set API keys in environment.")
            
        return Agent(
            models[0] if len(models) == 1 else models,  # Use fallback if multiple
            result_type=RoutingDecision,
            system_prompt=self._get_system_prompt()
        )
    
    def _get_system_prompt(self) -> str:
        return """You are an intelligent agent orchestrator responsible for routing requests 
        to the most appropriate specialized agent in a multi-protocol system.
        
        Your tasks:
        1. Analyze the user's request to understand the intent and requirements
        2. Review available agents and their capabilities
        3. Select the best agent based on capability match and current health status
        4. Provide clear reasoning for your routing decision
        5. Suggest alternatives if the primary agent might not be optimal
        
        Consider these factors:
        - Capability match: How well does the agent's capabilities align with the request?
        - Protocol efficiency: Some protocols may be better suited for certain tasks
        - Agent health: Prefer healthy agents over degraded ones
        - Load balancing: Distribute requests when multiple agents have similar capabilities
        
        Always provide a confidence score (0.0-1.0) for your routing decision."""
    
    @agent.tool
    async def get_available_agents(ctx: RunContext[None]) -> List[DiscoveredAgent]:
        """Get list of currently available agents and their capabilities"""
        discovery_service = ctx.deps["discovery_service"]
        agents = await discovery_service.get_all_agents()
        return [agent for agent in agents if agent.status != AgentStatus.UNHEALTHY]
    
    @agent.tool
    async def analyze_request_intent(ctx: RunContext[None], query: str) -> Dict[str, Any]:
        """Analyze the user's request to extract intent and requirements"""
        # This tool helps the LLM understand complex requests
        return {
            "query": query,
            "detected_intents": ["greeting", "calculation", "information_retrieval"],
            "required_capabilities": ["natural_language_processing"],
            "complexity": "simple"
        }
    
    async def route_request(
        self, 
        request: RoutingRequest, 
        available_agents: List[DiscoveredAgent]
    ) -> RoutingDecision:
        """Route a request to the most appropriate agent"""
        
        logger.info(
            "Routing request",
            request_id=request.request_id,
            query=request.query,
            available_agents=len(available_agents)
        )
        
        try:
            decision = await self.agent.run(
                request,
                deps={"discovery_service": self.discovery_service}
            )
            
            logger.info(
                "Routing decision made",
                request_id=request.request_id,
                selected_agent=decision.data.selected_agent.agent_id if decision.data.selected_agent else None,
                confidence=decision.data.confidence
            )
            
            return decision.data
            
        except Exception as e:
            logger.error("Routing failed", error=str(e), request_id=request.request_id)
            return RoutingDecision(
                request_id=request.request_id,
                reasoning=f"Failed to route request: {str(e)}",
                confidence=0.0,
                error=str(e)
            )
```

### 4. FastAPI Application (app.py)

```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

from .agent import OrchestrationAgent
from .discovery import UnifiedDiscoveryService
from .routing import RoutingEngine
from .models import *
from .config import get_settings
from .utils.metrics import setup_metrics, track_request_duration

logger = structlog.get_logger()

# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting orchestrator agent")
    
    # Initialize services
    app.state.settings = get_settings()
    app.state.discovery_service = UnifiedDiscoveryService()
    app.state.orchestration_agent = OrchestrationAgent()
    app.state.routing_engine = RoutingEngine(
        app.state.orchestration_agent,
        app.state.discovery_service
    )
    
    # Start discovery service
    await app.state.discovery_service.start()
    
    # Setup metrics if enabled
    if app.state.settings.enable_metrics:
        setup_metrics(app)
    
    yield
    
    # Shutdown
    logger.info("Shutting down orchestrator agent")
    await app.state.discovery_service.stop()

# Create FastAPI app
app = FastAPI(
    title="Multi-Protocol Agent Orchestrator",
    description="Intelligent routing for multi-protocol agent systems",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    discovery_healthy = await app.state.discovery_service.is_healthy()
    return {
        "status": "healthy" if discovery_healthy else "degraded",
        "version": app.state.settings.app_version,
        "discovery_service": "healthy" if discovery_healthy else "unhealthy"
    }

# Main routing endpoint
@app.post("/route", response_model=AgentResponse)
@track_request_duration
async def route_request(request: RoutingRequest):
    """Route a request to the most appropriate agent"""
    try:
        # Get routing decision
        response = await app.state.routing_engine.route(request)
        return response
    except Exception as e:
        logger.error("Routing error", error=str(e), request_id=request.request_id)
        raise HTTPException(status_code=500, detail=str(e))

# Agent discovery endpoints
@app.get("/agents", response_model=List[DiscoveredAgent])
async def list_agents(
    protocol: Optional[ProtocolType] = None,
    status: Optional[AgentStatus] = None
):
    """List all discovered agents"""
    agents = await app.state.discovery_service.get_all_agents()
    
    # Filter by protocol if specified
    if protocol:
        agents = [a for a in agents if a.protocol == protocol]
    
    # Filter by status if specified
    if status:
        agents = [a for a in agents if a.status == status]
    
    return agents

@app.get("/agents/{agent_id}", response_model=DiscoveredAgent)
async def get_agent(agent_id: str):
    """Get details for a specific agent"""
    agent = await app.state.discovery_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return agent

@app.post("/agents/refresh")
async def refresh_agents(background_tasks: BackgroundTasks):
    """Trigger agent discovery refresh"""
    background_tasks.add_task(app.state.discovery_service.refresh)
    return {"status": "refresh initiated"}

# Capabilities endpoint
@app.get("/capabilities")
async def get_capabilities():
    """Get orchestrator capabilities"""
    return {
        "name": "Multi-Protocol Agent Orchestrator",
        "version": app.state.settings.app_version,
        "supported_protocols": ["acp", "a2a", "mcp", "custom"],
        "llm_providers": [],
        "features": [
            "multi-protocol-discovery",
            "intelligent-routing",
            "fallback-handling",
            "health-monitoring",
            "metrics-collection"
        ]
    }

# Metrics endpoint (if enabled)
if get_settings().enable_metrics:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
```

### 5. Routing Engine (routing.py)

```python
import httpx
import asyncio
from typing import Optional
import structlog

from .models import *
from .agent import OrchestrationAgent
from .discovery import UnifiedDiscoveryService
from .protocols.base import ProtocolClient
from .protocols import get_protocol_client

logger = structlog.get_logger()

class RoutingEngine:
    def __init__(
        self,
        orchestration_agent: OrchestrationAgent,
        discovery_service: UnifiedDiscoveryService
    ):
        self.orchestration_agent = orchestration_agent
        self.discovery_service = discovery_service
        self.protocol_clients: Dict[ProtocolType, ProtocolClient] = {}
        
    async def route(self, request: RoutingRequest) -> AgentResponse:
        """Route a request through the orchestrator to the appropriate agent"""
        
        # Get available agents
        available_agents = await self.discovery_service.get_healthy_agents()
        
        if not available_agents:
            return AgentResponse(
                request_id=request.request_id,
                agent_id="orchestrator",
                protocol=ProtocolType.CUSTOM,
                response_data=None,
                duration_ms=0,
                success=False,
                error="No healthy agents available"
            )
        
        # Get routing decision from AI
        decision = await self.orchestration_agent.route_request(
            request,
            available_agents
        )
        
        if not decision.selected_agent:
            return AgentResponse(
                request_id=request.request_id,
                agent_id="orchestrator",
                protocol=ProtocolType.CUSTOM,
                response_data=None,
                duration_ms=0,
                success=False,
                error=decision.error or "No suitable agent found"
            )
        
        # Execute request on selected agent
        return await self._execute_on_agent(
            request,
            decision.selected_agent,
            decision.alternative_agents
        )
    
    async def _execute_on_agent(
        self,
        request: RoutingRequest,
        agent: DiscoveredAgent,
        fallback_agents: List[DiscoveredAgent]
    ) -> AgentResponse:
        """Execute request on specific agent with fallback support"""
        
        # Get protocol client
        client = self._get_protocol_client(agent.protocol)
        
        # Try primary agent
        try:
            logger.info(
                "Executing request on agent",
                agent_id=agent.agent_id,
                protocol=agent.protocol
            )
            
            start_time = asyncio.get_event_loop().time()
            response_data = await client.execute(
                agent,
                request.query,
                request.context,
                request.timeout_seconds
            )
            duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            
            return AgentResponse(
                request_id=request.request_id,
                agent_id=agent.agent_id,
                protocol=agent.protocol,
                response_data=response_data,
                duration_ms=duration_ms,
                success=True
            )
            
        except Exception as e:
            logger.error(
                "Agent execution failed",
                agent_id=agent.agent_id,
                error=str(e)
            )
            
            # Try fallback agents
            for fallback in fallback_agents:
                try:
                    return await self._execute_on_agent(
                        request,
                        fallback,
                        []  # No further fallbacks
                    )
                except:
                    continue
            
            # All agents failed
            return AgentResponse(
                request_id=request.request_id,
                agent_id=agent.agent_id,
                protocol=agent.protocol,
                response_data=None,
                duration_ms=0,
                success=False,
                error=str(e)
            )
    
    def _get_protocol_client(self, protocol: ProtocolType) -> ProtocolClient:
        """Get or create protocol client"""
        if protocol not in self.protocol_clients:
            self.protocol_clients[protocol] = get_protocol_client(protocol)
        return self.protocol_clients[protocol]
```

## Docker Configuration

### Dockerfile

```dockerfile
# Multi-stage build for production
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 agent && chown -R agent:agent /app

# Copy wheels and install
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir /wheels/*

# Copy application
COPY --chown=agent:agent src/ ./src/

# Switch to non-root user
USER agent

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Environment
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Expose ports
EXPOSE 8000 9090

# Run application
CMD ["uvicorn", "orchestrator.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose Integration

```yaml
  orchestrator:
    build:
      context: ./agents/orchestrator
      dockerfile: Dockerfile
    container_name: orchestrator-agent
    ports:
      - "8500:8000"      # Main API
      - "9500:9090"      # Metrics
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - LLM_PROVIDER=both
      - DISCOVERY_INTERVAL_SECONDS=30
      - ENABLE_METRICS=true
      - LOG_LEVEL=INFO
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro  # For Docker discovery
    depends_on:
      - acp-hello-world
    networks:
      - agent-network
    labels:
      - "agent.protocol=orchestrator"
      - "agent.type=routing"
      - "agent.version=0.1.0"
```

## Testing Strategy

### Unit Tests
- Test routing logic with mocked agents
- Test discovery service with fake Docker API
- Test protocol clients independently
- Test Pydantic AI agent decisions

### Integration Tests
- Test with real ACP Hello World agent
- Test failover between LLM providers
- Test agent discovery and health checks
- Test error handling and retries

### Demo Script (scripts/demo_routing.py)

```python
import asyncio
import httpx

async def demo_routing():
    async with httpx.AsyncClient() as client:
        # Simple greeting request
        response = await client.post(
            "http://localhost:8500/route",
            json={
                "query": "Hello, can you greet me in Spanish?",
                "context": {"user": "Demo User"}
            }
        )
        print(f"Greeting Response: {response.json()}")
        
        # Math request (will fail until A2A agent exists)
        response = await client.post(
            "http://localhost:8500/route",
            json={
                "query": "What is 15 * 23?",
                "context": {"precision": "high"}
            }
        )
        print(f"Math Response: {response.json()}")

if __name__ == "__main__":
    asyncio.run(demo_routing())
```

## Implementation Timeline

- **Day 1-2**: Core structure and configuration
- **Day 3-4**: Pydantic AI agent and routing logic
- **Day 5-6**: Discovery service and protocol clients
- **Day 7**: Testing and documentation

This implementation leverages Pydantic AI's strengths for intelligent routing while maintaining clean architecture and extensibility for future protocols.