"""Tests for data models"""

import pytest
import uuid
from datetime import datetime
from pydantic import ValidationError

from orchestrator.models import (
    ProtocolType,
    AgentStatus,
    LLMProvider,
    AgentCapability,
    DiscoveredAgent,
    RoutingRequest,
    RoutingDecision,
    AgentResponse,
    HealthCheckResponse,
    OrchestrationMetrics,
    AgentRegistryEntry,
)


class TestEnums:
    """Test enum definitions"""
    
    def test_protocol_type_values(self):
        """Test ProtocolType enum values"""
        assert ProtocolType.ACP == "acp"
        assert ProtocolType.A2A == "a2a"
        assert ProtocolType.MCP == "mcp"
        assert ProtocolType.CUSTOM == "custom"
    
    def test_agent_status_values(self):
        """Test AgentStatus enum values"""
        assert AgentStatus.HEALTHY == "healthy"
        assert AgentStatus.DEGRADED == "degraded"
        assert AgentStatus.UNHEALTHY == "unhealthy"
        assert AgentStatus.UNKNOWN == "unknown"
    
    def test_llm_provider_values(self):
        """Test LLMProvider enum values"""
        assert LLMProvider.OPENAI == "openai"
        assert LLMProvider.ANTHROPIC == "anthropic"


class TestAgentCapability:
    """Test AgentCapability model"""
    
    def test_valid_capability_creation(self):
        """Test creating a valid capability"""
        capability = AgentCapability(
            name="greeting",
            description="Generate greetings in multiple languages",
            input_schema={"type": "object", "properties": {"name": {"type": "string"}}},
            output_schema={"type": "object", "properties": {"message": {"type": "string"}}},
            examples=[{"input": {"name": "Alice"}, "output": {"message": "Hello, Alice!"}}],
            tags=["multilingual", "greeting"]
        )
        
        assert capability.name == "greeting"
        assert capability.description == "Generate greetings in multiple languages"
        assert capability.input_schema is not None
        assert capability.output_schema is not None
        assert len(capability.examples) == 1
        assert len(capability.tags) == 2
    
    def test_capability_name_validation(self):
        """Test capability name validation"""
        # Empty name should fail
        with pytest.raises(ValidationError):
            AgentCapability(name="", description="Test")
        
        # Whitespace-only name should fail
        with pytest.raises(ValidationError):
            AgentCapability(name="   ", description="Test")
        
        # Name should be trimmed and lowercased
        capability = AgentCapability(name="  GREETING  ", description="Test")
        assert capability.name == "greeting"
    
    def test_capability_defaults(self):
        """Test capability default values"""
        capability = AgentCapability(name="test", description="Test capability")
        
        assert capability.input_schema is None
        assert capability.output_schema is None
        assert capability.examples == []
        assert capability.tags == []


class TestDiscoveredAgent:
    """Test DiscoveredAgent model"""
    
    def test_valid_agent_creation(self):
        """Test creating a valid discovered agent"""
        capability = AgentCapability(name="greeting", description="Test")
        
        agent = DiscoveredAgent(
            agent_id="test-agent",
            name="Test Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://test:8000",
            capabilities=[capability],
            status=AgentStatus.HEALTHY,
            metadata={"version": "1.0"},
            container_id="container-123",
            version="1.0.0"
        )
        
        assert agent.agent_id == "test-agent"
        assert agent.name == "Test Agent"
        assert agent.protocol == ProtocolType.ACP
        assert agent.endpoint == "http://test:8000"
        assert len(agent.capabilities) == 1
        assert agent.status == AgentStatus.HEALTHY
        assert agent.metadata["version"] == "1.0"
        assert agent.container_id == "container-123"
        assert agent.version == "1.0.0"
        assert isinstance(agent.discovered_at, datetime)
    
    def test_agent_id_validation(self):
        """Test agent ID validation"""
        # Empty agent ID should fail
        with pytest.raises(ValidationError):
            DiscoveredAgent(
                agent_id="",
                name="Test",
                protocol=ProtocolType.ACP,
                endpoint="http://test:8000"
            )
        
        # Whitespace-only agent ID should fail
        with pytest.raises(ValidationError):
            DiscoveredAgent(
                agent_id="   ",
                name="Test",
                protocol=ProtocolType.ACP,
                endpoint="http://test:8000"
            )
        
        # Agent ID should be trimmed
        agent = DiscoveredAgent(
            agent_id="  test-agent  ",
            name="Test",
            protocol=ProtocolType.ACP,
            endpoint="http://test:8000"
        )
        assert agent.agent_id == "test-agent"
    
    def test_endpoint_validation(self):
        """Test endpoint URL validation"""
        # Invalid URLs should fail
        with pytest.raises(ValidationError):
            DiscoveredAgent(
                agent_id="test",
                name="Test",
                protocol=ProtocolType.ACP,
                endpoint="invalid-url"
            )
        
        with pytest.raises(ValidationError):
            DiscoveredAgent(
                agent_id="test",
                name="Test",
                protocol=ProtocolType.ACP,
                endpoint="ftp://test:8000"
            )
        
        # Valid URLs should work
        agent = DiscoveredAgent(
            agent_id="test",
            name="Test",
            protocol=ProtocolType.ACP,
            endpoint="https://test:8000"
        )
        assert agent.endpoint == "https://test:8000"
    
    def test_agent_methods(self):
        """Test agent utility methods"""
        capability1 = AgentCapability(name="greeting", description="Test")
        capability2 = AgentCapability(name="math", description="Test")
        
        agent = DiscoveredAgent(
            agent_id="test",
            name="Test",
            protocol=ProtocolType.ACP,
            endpoint="http://test:8000",
            capabilities=[capability1, capability2],
            status=AgentStatus.HEALTHY
        )
        
        # Test get_capability_names
        names = agent.get_capability_names()
        assert "greeting" in names
        assert "math" in names
        assert len(names) == 2
        
        # Test has_capability
        assert agent.has_capability("greeting") is True
        assert agent.has_capability("GREETING") is True  # Case insensitive
        assert agent.has_capability("nonexistent") is False
        
        # Test is_healthy
        assert agent.is_healthy() is True
        
        agent.status = AgentStatus.DEGRADED
        assert agent.is_healthy() is False


class TestRoutingRequest:
    """Test RoutingRequest model"""
    
    def test_valid_request_creation(self):
        """Test creating a valid routing request"""
        request = RoutingRequest(
            query="Hello, world!",
            context={"user": "test"},
            preferred_protocol=ProtocolType.ACP,
            preferred_agent="test-agent",
            timeout_seconds=30.0
        )
        
        assert request.query == "Hello, world!"
        assert request.context["user"] == "test"
        assert request.preferred_protocol == ProtocolType.ACP
        assert request.preferred_agent == "test-agent"
        assert request.timeout_seconds == 30.0
        assert isinstance(uuid.UUID(request.request_id), uuid.UUID)
    
    def test_query_validation(self):
        """Test query validation"""
        # Empty query should fail
        with pytest.raises(ValidationError):
            RoutingRequest(query="")
        
        # Whitespace-only query should fail
        with pytest.raises(ValidationError):
            RoutingRequest(query="   ")
        
        # Query should be trimmed
        request = RoutingRequest(query="  Hello, world!  ")
        assert request.query == "Hello, world!"
    
    def test_timeout_validation(self):
        """Test timeout validation"""
        # Negative timeout should fail
        with pytest.raises(ValidationError):
            RoutingRequest(query="test", timeout_seconds=-1.0)
        
        # Zero timeout should fail
        with pytest.raises(ValidationError):
            RoutingRequest(query="test", timeout_seconds=0.0)
        
        # Positive timeout should work
        request = RoutingRequest(query="test", timeout_seconds=30.0)
        assert request.timeout_seconds == 30.0
    
    def test_defaults(self):
        """Test default values"""
        request = RoutingRequest(query="test")
        
        assert request.context is None
        assert request.preferred_protocol is None
        assert request.preferred_agent is None
        assert request.timeout_seconds is None


class TestRoutingDecision:
    """Test RoutingDecision model"""
    
    def test_valid_decision_creation(self, sample_discovered_agent):
        """Test creating a valid routing decision"""
        decision = RoutingDecision(
            request_id="test-request",
            selected_agent=sample_discovered_agent,
            reasoning="This agent can handle the request",
            confidence=0.9,
            alternative_agents=[],
            decision_time_ms=150.0,
            llm_provider=LLMProvider.OPENAI
        )
        
        assert decision.request_id == "test-request"
        assert decision.selected_agent == sample_discovered_agent
        assert decision.reasoning == "This agent can handle the request"
        assert decision.confidence == 0.9
        assert decision.alternative_agents == []
        assert decision.error is None
        assert decision.decision_time_ms == 150.0
        assert decision.llm_provider == LLMProvider.OPENAI
    
    def test_confidence_validation(self):
        """Test confidence score validation"""
        # Confidence below 0 should fail
        with pytest.raises(ValidationError):
            RoutingDecision(
                request_id="test",
                reasoning="test",
                confidence=-0.1
            )
        
        # Confidence above 1 should fail
        with pytest.raises(ValidationError):
            RoutingDecision(
                request_id="test",
                reasoning="test",
                confidence=1.1
            )
        
        # Valid confidence should work
        decision = RoutingDecision(
            request_id="test",
            reasoning="test",
            confidence=0.5
        )
        assert decision.confidence == 0.5
    
    def test_is_successful_method(self, sample_discovered_agent):
        """Test is_successful method"""
        # Successful decision
        decision = RoutingDecision(
            request_id="test",
            selected_agent=sample_discovered_agent,
            reasoning="test",
            confidence=0.9
        )
        assert decision.is_successful() is True
        
        # Failed decision (no agent)
        decision = RoutingDecision(
            request_id="test",
            selected_agent=None,
            reasoning="No suitable agent found",
            confidence=0.0
        )
        assert decision.is_successful() is False
        
        # Failed decision (error)
        decision = RoutingDecision(
            request_id="test",
            selected_agent=sample_discovered_agent,
            reasoning="test",
            confidence=0.9,
            error="Something went wrong"
        )
        assert decision.is_successful() is False


class TestAgentResponse:
    """Test AgentResponse model"""
    
    def test_valid_response_creation(self):
        """Test creating a valid agent response"""
        response = AgentResponse(
            request_id="test-request",
            agent_id="test-agent",
            protocol=ProtocolType.ACP,
            response_data={"message": "Hello, world!"},
            duration_ms=250.0,
            success=True,
            metadata={"version": "1.0"}
        )
        
        assert response.request_id == "test-request"
        assert response.agent_id == "test-agent"
        assert response.protocol == ProtocolType.ACP
        assert response.response_data["message"] == "Hello, world!"
        assert response.duration_ms == 250.0
        assert response.success is True
        assert response.error is None
        assert response.metadata["version"] == "1.0"
        assert isinstance(response.timestamp, datetime)
    
    def test_duration_validation(self):
        """Test duration validation"""
        # Negative duration should fail
        with pytest.raises(ValidationError):
            AgentResponse(
                request_id="test",
                agent_id="test",
                protocol=ProtocolType.ACP,
                response_data={},
                duration_ms=-1.0,
                success=True
            )
    
    def test_is_successful_method(self):
        """Test is_successful method"""
        # Successful response
        response = AgentResponse(
            request_id="test",
            agent_id="test",
            protocol=ProtocolType.ACP,
            response_data={},
            duration_ms=100.0,
            success=True
        )
        assert response.is_successful() is True
        
        # Failed response (success=False)
        response = AgentResponse(
            request_id="test",
            agent_id="test",
            protocol=ProtocolType.ACP,
            response_data={},
            duration_ms=100.0,
            success=False
        )
        assert response.is_successful() is False
        
        # Failed response (with error)
        response = AgentResponse(
            request_id="test",
            agent_id="test",
            protocol=ProtocolType.ACP,
            response_data={},
            duration_ms=100.0,
            success=True,
            error="Something went wrong"
        )
        assert response.is_successful() is False


class TestOrchestrationMetrics:
    """Test OrchestrationMetrics model"""
    
    def test_metrics_creation(self):
        """Test creating orchestration metrics"""
        metrics = OrchestrationMetrics(
            total_requests=100,
            successful_requests=90,
            failed_requests=10,
            average_response_time_ms=250.0,
            agents_discovered=5,
            healthy_agents=4,
            by_protocol={"acp": 60, "a2a": 40},
            by_agent={"agent1": 50, "agent2": 50}
        )
        
        assert metrics.total_requests == 100
        assert metrics.successful_requests == 90
        assert metrics.failed_requests == 10
        assert metrics.average_response_time_ms == 250.0
        assert metrics.agents_discovered == 5
        assert metrics.healthy_agents == 4
        assert metrics.by_protocol["acp"] == 60
        assert metrics.by_agent["agent1"] == 50
    
    def test_success_rate_calculation(self):
        """Test success rate calculation"""
        # Normal case
        metrics = OrchestrationMetrics(
            total_requests=100,
            successful_requests=90
        )
        assert metrics.success_rate == 90.0
        
        # Zero requests
        metrics = OrchestrationMetrics(
            total_requests=0,
            successful_requests=0
        )
        assert metrics.success_rate == 0.0
        
        # Perfect success rate
        metrics = OrchestrationMetrics(
            total_requests=50,
            successful_requests=50
        )
        assert metrics.success_rate == 100.0


class TestAgentRegistryEntry:
    """Test AgentRegistryEntry model"""
    
    def test_registry_entry_creation(self, sample_discovered_agent):
        """Test creating a registry entry"""
        entry = AgentRegistryEntry(agent=sample_discovered_agent)
        
        assert entry.agent == sample_discovered_agent
        assert isinstance(entry.last_seen, datetime)
        assert entry.consecutive_failures == 0
        assert entry.request_count == 0
        assert entry.last_request is None
    
    def test_mark_request(self, sample_discovered_agent):
        """Test marking a request"""
        entry = AgentRegistryEntry(agent=sample_discovered_agent)
        
        entry.mark_request()
        assert entry.request_count == 1
        assert isinstance(entry.last_request, datetime)
        
        entry.mark_request()
        assert entry.request_count == 2
    
    def test_mark_failure(self, sample_discovered_agent):
        """Test marking failures"""
        entry = AgentRegistryEntry(agent=sample_discovered_agent)
        
        entry.mark_failure()
        assert entry.consecutive_failures == 1
        
        entry.mark_failure()
        assert entry.consecutive_failures == 2
    
    def test_mark_success(self, sample_discovered_agent):
        """Test marking success"""
        entry = AgentRegistryEntry(agent=sample_discovered_agent)
        
        # Mark some failures first
        entry.mark_failure()
        entry.mark_failure()
        assert entry.consecutive_failures == 2
        
        # Mark success should reset failures
        entry.mark_success()
        assert entry.consecutive_failures == 0
        assert isinstance(entry.last_seen, datetime)
    
    def test_should_remove(self, sample_discovered_agent):
        """Test should_remove logic"""
        entry = AgentRegistryEntry(agent=sample_discovered_agent)
        
        # Initially should not be removed
        assert entry.should_remove() is False
        
        # Add failures
        for _ in range(4):
            entry.mark_failure()
        assert entry.should_remove() is False
        
        # Fifth failure should trigger removal
        entry.mark_failure()
        assert entry.should_remove() is True
        
        # Custom threshold
        entry = AgentRegistryEntry(agent=sample_discovered_agent)
        for _ in range(3):
            entry.mark_failure()
        assert entry.should_remove(max_failures=3) is True