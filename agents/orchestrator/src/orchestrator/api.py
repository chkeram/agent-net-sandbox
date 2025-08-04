"""FastAPI application for the Multi-Protocol Agent Orchestrator"""

import asyncio
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any
from datetime import datetime

import structlog
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .agent import OrchestratorAgent
from .discovery import UnifiedDiscoveryService
from .models import (
    RoutingRequest, RoutingDecision, AgentResponse, DiscoveredAgent,
    HealthCheckResponse, OrchestrationMetrics, ProtocolType
)
from .config import get_settings

logger = structlog.get_logger(__name__)

# Global instances
discovery_service: Optional[UnifiedDiscoveryService] = None
orchestrator_agent: Optional[OrchestratorAgent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global discovery_service, orchestrator_agent
    
    logger.info("Starting Multi-Protocol Agent Orchestrator")
    
    try:
        # Initialize discovery service
        discovery_service = UnifiedDiscoveryService()
        await discovery_service.start()
        
        # Initialize orchestrator agent
        orchestrator_agent = OrchestratorAgent(discovery_service)
        
        # Start background discovery
        await discovery_service.start()
        
        logger.info("Orchestrator initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error("Failed to initialize orchestrator", error=str(e))
        raise
    finally:
        logger.info("Shutting down orchestrator")
        
        # Stop discovery service
        if discovery_service:
            await discovery_service.stop()


# Create FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multi-Protocol Agent Orchestrator - Intelligent routing across agent protocols",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)


# Dependency injection
async def get_discovery_service() -> UnifiedDiscoveryService:
    """Get discovery service instance"""
    if discovery_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Discovery service not available"
        )
    return discovery_service


async def get_orchestrator_agent() -> OrchestratorAgent:
    """Get orchestrator agent instance"""
    if orchestrator_agent is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator agent not available"
        )
    return orchestrator_agent


# Request/Response models
class RouteRequestModel(BaseModel):
    """API model for routing requests"""
    query: str = Field(..., description="User query to route", min_length=1)
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    preferred_protocol: Optional[str] = Field(None, description="Preferred protocol (acp, a2a, mcp)")
    preferred_agent: Optional[str] = Field(None, description="Preferred agent ID")
    timeout_seconds: Optional[float] = Field(None, description="Request timeout", gt=0)


class ProcessRequestModel(RouteRequestModel):
    """API model for processing requests (includes routing + execution)"""
    pass


class AgentSummary(BaseModel):
    """Summary model for discovered agents"""
    agent_id: str
    name: str
    protocol: str
    status: str
    capabilities: List[str]
    endpoint: str
    last_seen: datetime


class SystemStatus(BaseModel):
    """Overall system status"""
    status: str
    timestamp: datetime
    orchestrator_healthy: bool
    discovery_service_healthy: bool
    total_agents: int
    healthy_agents: int
    protocols_supported: List[str]
    version: str


# Health check endpoint
@app.get("/health", response_model=HealthCheckResponse)
async def health_check(
    orchestrator: OrchestratorAgent = Depends(get_orchestrator_agent)
) -> HealthCheckResponse:
    """Get orchestrator health status"""
    try:
        health_data = await orchestrator.health_check()
        
        overall_status = "healthy"
        if not health_data.get("orchestrator_healthy", False):
            overall_status = "unhealthy"
        elif not health_data.get("discovery_service_healthy", False):
            overall_status = "degraded"
        elif health_data.get("available_agents", 0) == 0:
            overall_status = "degraded"
        
        return HealthCheckResponse(
            status=overall_status,
            version=settings.app_version,
            services={
                "orchestrator": "healthy" if health_data.get("orchestrator_healthy") else "unhealthy",
                "discovery_service": "healthy" if health_data.get("discovery_service_healthy") else "unhealthy",
                "llm_provider": health_data.get("llm_provider", "unknown")
            },
            details=health_data
        )
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return HealthCheckResponse(
            status="unhealthy",
            version=settings.app_version,
            services={
                "orchestrator": "unhealthy",
                "discovery_service": "unknown",
                "error": str(e)
            }
        )


# System status endpoint
@app.get("/status", response_model=SystemStatus)
async def system_status(
    discovery: UnifiedDiscoveryService = Depends(get_discovery_service),
    orchestrator: OrchestratorAgent = Depends(get_orchestrator_agent)
) -> SystemStatus:
    """Get comprehensive system status"""
    try:
        health_data = await orchestrator.health_check()
        all_agents = await discovery.get_all_agents()
        healthy_agents = await discovery.get_healthy_agents()
        
        protocols = set()
        for agent in all_agents:
            protocols.add(agent.protocol.value)
        
        return SystemStatus(
            status="healthy" if health_data.get("orchestrator_healthy") else "degraded",
            timestamp=datetime.utcnow(),
            orchestrator_healthy=health_data.get("orchestrator_healthy", False),
            discovery_service_healthy=health_data.get("discovery_service_healthy", False),
            total_agents=len(all_agents),
            healthy_agents=len(healthy_agents),
            protocols_supported=sorted(list(protocols)),
            version=settings.app_version
        )
        
    except Exception as e:
        logger.error("System status check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"System status check failed: {str(e)}"
        )


# Agent discovery endpoints
@app.get("/agents", response_model=List[AgentSummary])
async def list_agents(
    protocol: Optional[str] = None,
    capability: Optional[str] = None,
    status_filter: Optional[str] = None,
    discovery: UnifiedDiscoveryService = Depends(get_discovery_service)
) -> List[AgentSummary]:
    """List discovered agents with optional filtering"""
    try:
        # Get agents based on filters
        if capability:
            agents = await discovery.get_agents_by_capability(capability)
        elif protocol:
            try:
                protocol_type = ProtocolType(protocol.lower())
                agents = await discovery.get_agents_by_protocol(protocol_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid protocol: {protocol}"
                )
        else:
            agents = await discovery.get_all_agents()
        
        # Apply status filter
        if status_filter:
            agents = [agent for agent in agents if agent.status.value == status_filter.lower()]
        
        # Convert to summary format
        summaries = []
        for agent in agents:
            summaries.append(AgentSummary(
                agent_id=agent.agent_id,
                name=agent.name,
                protocol=agent.protocol.value,
                status=agent.status.value,
                capabilities=[cap.name for cap in agent.capabilities],
                endpoint=agent.endpoint,
                last_seen=agent.discovered_at
            ))
        
        return summaries
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list agents", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list agents: {str(e)}"
        )


@app.get("/agents/{agent_id}", response_model=DiscoveredAgent)
async def get_agent(
    agent_id: str,
    discovery: UnifiedDiscoveryService = Depends(get_discovery_service)
) -> DiscoveredAgent:
    """Get detailed information about a specific agent"""
    try:
        agent = await discovery.get_agent_by_id(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
        return agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get agent", agent_id=agent_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent: {str(e)}"
        )


@app.post("/agents/refresh")
async def refresh_agents(
    background_tasks: BackgroundTasks,
    discovery: UnifiedDiscoveryService = Depends(get_discovery_service)
) -> Dict[str, str]:
    """Trigger immediate agent discovery refresh"""
    try:
        # Run refresh in background to return quickly
        background_tasks.add_task(discovery.refresh)
        
        return {
            "status": "refresh_triggered",
            "message": "Agent discovery refresh has been initiated"
        }
        
    except Exception as e:
        logger.error("Failed to trigger agent refresh", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger refresh: {str(e)}"
        )


# Routing endpoints
@app.post("/route", response_model=RoutingDecision)
async def route_request(
    request: RouteRequestModel,
    orchestrator: OrchestratorAgent = Depends(get_orchestrator_agent)
) -> RoutingDecision:
    """Route a request to the most appropriate agent"""
    try:
        # Convert API model to internal model
        routing_request = RoutingRequest(
            query=request.query,
            context=request.context,
            preferred_protocol=ProtocolType(request.preferred_protocol) if request.preferred_protocol else None,
            preferred_agent=request.preferred_agent,
            timeout_seconds=request.timeout_seconds
        )
        
        # Route the request
        decision = await orchestrator.route_request(routing_request)
        
        logger.info(
            "Request routed",
            query=request.query[:50] + "..." if len(request.query) > 50 else request.query,
            selected_agent=decision.selected_agent.agent_id if decision.selected_agent else None,
            confidence=decision.confidence
        )
        
        return decision
        
    except Exception as e:
        logger.error("Request routing failed", query=request.query, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Routing failed: {str(e)}"
        )


@app.post("/process", response_model=AgentResponse)
async def process_request(
    request: ProcessRequestModel,
    orchestrator: OrchestratorAgent = Depends(get_orchestrator_agent)
) -> AgentResponse:
    """Process a complete request: route and execute"""
    try:
        # Convert API model to internal model
        routing_request = RoutingRequest(
            query=request.query,
            context=request.context,
            preferred_protocol=ProtocolType(request.preferred_protocol) if request.preferred_protocol else None,
            preferred_agent=request.preferred_agent,
            timeout_seconds=request.timeout_seconds
        )
        
        # Process the complete request
        response = await orchestrator.process_request(routing_request)
        
        logger.info(
            "Request processed",
            query=request.query[:50] + "..." if len(request.query) > 50 else request.query,
            success=response.success,
            agent_id=response.agent_id,
            duration=response.duration_ms
        )
        
        return response
        
    except Exception as e:
        logger.error("Request processing failed", query=request.query, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )


# Metrics and monitoring
@app.get("/metrics", response_model=OrchestrationMetrics)
async def get_metrics(
    orchestrator: OrchestratorAgent = Depends(get_orchestrator_agent)
) -> OrchestrationMetrics:
    """Get orchestration metrics and statistics"""
    try:
        return orchestrator.get_metrics()
        
    except Exception as e:
        logger.error("Failed to get metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )


# Protocol information
@app.get("/protocols")
async def list_protocols() -> Dict[str, Any]:
    """List supported protocols and their information"""
    return {
        "supported_protocols": [
            {
                "name": "ACP",
                "description": "AGNTCY Agent Connect Protocol",
                "version": "0.1",
                "status": "implemented"
            },
            {
                "name": "A2A", 
                "description": "Agent-to-Agent Communication Protocol",
                "version": "1.0",
                "status": "discovery_only"
            },
            {
                "name": "MCP",
                "description": "Model Context Protocol",
                "version": "0.1",
                "status": "discovery_only"
            },
            {
                "name": "CUSTOM",
                "description": "Custom protocol implementations",
                "version": "any",
                "status": "template_ready"
            }
        ],
        "total_protocols": 4,
        "fully_implemented": 1
    }


# Capabilities endpoint
@app.get("/capabilities")
async def list_capabilities(
    discovery: UnifiedDiscoveryService = Depends(get_discovery_service)
) -> Dict[str, Any]:
    """List all available capabilities across agents"""
    try:
        agents = await discovery.get_all_agents()
        
        capabilities = {}
        for agent in agents:
            for cap in agent.capabilities:
                if cap.name not in capabilities:
                    capabilities[cap.name] = {
                        "description": cap.description,
                        "agents": [],
                        "protocols": set(),
                        "total_agents": 0
                    }
                
                capabilities[cap.name]["agents"].append({
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "protocol": agent.protocol.value,
                    "status": agent.status.value
                })
                capabilities[cap.name]["protocols"].add(agent.protocol.value)
                capabilities[cap.name]["total_agents"] += 1
        
        # Convert sets to lists for JSON serialization
        for cap_name in capabilities:
            capabilities[cap_name]["protocols"] = list(capabilities[cap_name]["protocols"])
        
        return {
            "capabilities": capabilities,
            "total_capabilities": len(capabilities),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to list capabilities", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list capabilities: {str(e)}"
        )


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "http_error",
                "message": exc.detail,
                "status_code": exc.status_code,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """General exception handler"""
    logger.error("Unhandled exception", error=str(exc), path=str(request.url))
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "internal_error",
                "message": "An internal error occurred",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic information"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "description": "Multi-Protocol Agent Orchestrator - Intelligent routing across agent protocols",
        "endpoints": {
            "health": "/health",
            "status": "/status", 
            "agents": "/agents",
            "route": "/route",
            "process": "/process",
            "metrics": "/metrics",
            "protocols": "/protocols",
            "capabilities": "/capabilities",
            "docs": "/docs"
        },
        "protocols_supported": ["ACP", "A2A", "MCP", "CUSTOM"],
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "orchestrator.api:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        log_level=settings.log_level.lower(),
        reload=settings.debug
    )