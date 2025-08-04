"""Data models for the Multi-Protocol Agent Orchestrator"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Dict, Any, List, Literal, Union
from datetime import datetime
from enum import Enum
import uuid


class ProtocolType(str, Enum):
    """Supported protocol types"""
    ACP = "acp"
    A2A = "a2a"
    MCP = "mcp"
    CUSTOM = "custom"


class AgentStatus(str, Enum):
    """Agent health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class AgentCapability(BaseModel):
    """Represents a capability that an agent provides"""
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., description="Capability name", min_length=1)
    description: str = Field(..., description="What this capability does")
    input_schema: Optional[Dict[str, Any]] = Field(None, description="Expected input format")
    output_schema: Optional[Dict[str, Any]] = Field(None, description="Expected output format")
    examples: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Usage examples"
    )
    tags: List[str] = Field(default_factory=list, description="Capability tags")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Capability name cannot be empty")
        return v.strip().lower()


class DiscoveredAgent(BaseModel):
    """Represents a discovered agent in the system"""
    model_config = ConfigDict(from_attributes=True)
    
    agent_id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Human-readable agent name")
    protocol: ProtocolType = Field(..., description="Communication protocol")
    endpoint: str = Field(..., description="Agent endpoint URL")
    capabilities: List[AgentCapability] = Field(
        default_factory=list,
        description="Agent capabilities"
    )
    status: AgentStatus = Field(AgentStatus.UNKNOWN, description="Current health status")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Protocol-specific metadata"
    )
    discovered_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the agent was discovered"
    )
    last_health_check: Optional[datetime] = Field(
        None,
        description="Last health check timestamp"
    )
    container_id: Optional[str] = Field(None, description="Docker container ID")
    version: Optional[str] = Field(None, description="Agent version")
    
    @field_validator('agent_id')
    @classmethod
    def validate_agent_id(cls, v):
        if not v or not v.strip():
            raise ValueError("Agent ID cannot be empty")
        return v.strip()
    
    @field_validator('endpoint')
    @classmethod
    def validate_endpoint(cls, v):
        if not v or not v.startswith(('http://', 'https://')):
            raise ValueError("Endpoint must be a valid HTTP/HTTPS URL")
        return v.strip()
    
    def get_capability_names(self) -> List[str]:
        """Get list of capability names"""
        return [cap.name for cap in self.capabilities]
    
    def has_capability(self, capability_name: str) -> bool:
        """Check if agent has a specific capability"""
        return capability_name.lower() in self.get_capability_names()
    
    def is_healthy(self) -> bool:
        """Check if agent is in healthy state"""
        return self.status == AgentStatus.HEALTHY


class RoutingRequest(BaseModel):
    """Request to route to an appropriate agent"""
    model_config = ConfigDict(from_attributes=True)
    
    request_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique request identifier"
    )
    query: str = Field(..., description="User's request to be routed", min_length=1)
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context for the request"
    )
    preferred_protocol: Optional[ProtocolType] = Field(
        None,
        description="Preferred protocol for routing"
    )
    preferred_agent: Optional[str] = Field(
        None,
        description="Preferred agent ID for routing"
    )
    timeout_seconds: Optional[float] = Field(
        None,
        description="Request timeout in seconds",
        gt=0
    )
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class RoutingDecision(BaseModel):
    """AI agent's routing decision"""
    model_config = ConfigDict(from_attributes=True)
    
    request_id: str = Field(..., description="Request identifier")
    selected_agent: Optional[DiscoveredAgent] = Field(
        None,
        description="Selected agent for handling the request"
    )
    reasoning: str = Field(..., description="Explanation of routing decision")
    confidence: float = Field(
        ...,
        description="Confidence in the routing decision",
        ge=0.0,
        le=1.0
    )
    alternative_agents: List[DiscoveredAgent] = Field(
        default_factory=list,
        description="Alternative agents that could handle the request"
    )
    error: Optional[str] = Field(None, description="Error message if routing failed")
    decision_time_ms: Optional[float] = Field(
        None,
        description="Time taken to make the decision in milliseconds"
    )
    llm_provider: Optional[LLMProvider] = Field(
        None,
        description="Which LLM provider made the decision"
    )
    
    def is_successful(self) -> bool:
        """Check if routing decision was successful"""
        return self.selected_agent is not None and self.error is None


class AgentResponse(BaseModel):
    """Response from an agent after executing a request"""
    model_config = ConfigDict(from_attributes=True)
    
    request_id: str = Field(..., description="Original request identifier")
    agent_id: str = Field(..., description="ID of the agent that handled the request")
    protocol: ProtocolType = Field(..., description="Protocol used for communication")
    response_data: Any = Field(..., description="Actual response data from the agent")
    duration_ms: float = Field(..., description="Execution time in milliseconds", ge=0)
    success: bool = Field(..., description="Whether the request was successful")
    error: Optional[str] = Field(None, description="Error message if request failed")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the response"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )
    
    def is_successful(self) -> bool:
        """Check if the agent response was successful"""
        return self.success and self.error is None


class HealthCheckResponse(BaseModel):
    """Health check response"""
    model_config = ConfigDict(from_attributes=True)
    
    status: Literal["healthy", "degraded", "unhealthy"] = Field(
        ...,
        description="Overall health status"
    )
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Health check timestamp"
    )
    services: Dict[str, str] = Field(
        default_factory=dict,
        description="Status of individual services"
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional health details"
    )


class OrchestrationMetrics(BaseModel):
    """Metrics about orchestration performance"""
    model_config = ConfigDict(from_attributes=True)
    
    total_requests: int = Field(0, description="Total number of requests processed")
    successful_requests: int = Field(0, description="Number of successful requests")
    failed_requests: int = Field(0, description="Number of failed requests")
    average_response_time_ms: float = Field(0.0, description="Average response time")
    agents_discovered: int = Field(0, description="Number of agents currently discovered")
    healthy_agents: int = Field(0, description="Number of healthy agents")
    by_protocol: Dict[str, int] = Field(
        default_factory=dict,
        description="Request counts by protocol"
    )
    by_agent: Dict[str, int] = Field(
        default_factory=dict,
        description="Request counts by agent"
    )
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100.0


class AgentRegistryEntry(BaseModel):
    """Internal registry entry for discovered agents"""
    model_config = ConfigDict(from_attributes=True)
    
    agent: DiscoveredAgent = Field(..., description="The discovered agent")
    last_seen: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last time agent was seen during discovery"
    )
    consecutive_failures: int = Field(
        0,
        description="Number of consecutive health check failures"
    )
    request_count: int = Field(0, description="Number of requests routed to this agent")
    last_request: Optional[datetime] = Field(
        None,
        description="Timestamp of last request"
    )
    
    def mark_request(self) -> None:
        """Mark that a request was sent to this agent"""
        self.request_count += 1
        self.last_request = datetime.utcnow()
    
    def mark_failure(self) -> None:
        """Mark a health check failure"""
        self.consecutive_failures += 1
    
    def mark_success(self) -> None:
        """Mark a successful health check"""
        self.consecutive_failures = 0
        self.last_seen = datetime.utcnow()
    
    def should_remove(self, max_failures: int = 5) -> bool:
        """Check if agent should be removed from registry"""
        return self.consecutive_failures >= max_failures


# Type aliases for convenience
AgentRegistry = Dict[str, AgentRegistryEntry]
CapabilityMap = Dict[str, List[str]]  # capability_name -> [agent_ids]