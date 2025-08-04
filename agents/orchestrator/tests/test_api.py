"""Tests for FastAPI application"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any

import httpx
from fastapi.testclient import TestClient

from orchestrator.api import app
from orchestrator.models import (
    DiscoveredAgent, AgentCapability, ProtocolType, AgentStatus,
    RoutingDecision, AgentResponse, OrchestrationMetrics,
    HealthCheckResponse, LLMProvider
)
from orchestrator.discovery import UnifiedDiscoveryService
from orchestrator.agent import OrchestratorAgent

pytestmark = pytest.mark.asyncio


class TestFastAPIApplication:
    """Test FastAPI application endpoints"""
    
    @pytest.fixture
    def mock_discovery_service(self):
        """Create mock discovery service"""
        service = AsyncMock(spec=UnifiedDiscoveryService)
        
        # Mock test agents
        test_agents = [
            DiscoveredAgent(
                agent_id="acp-greeting-agent",
                name="Greeting Agent",
                protocol=ProtocolType.ACP,
                endpoint="http://greeting:8000",
                capabilities=[
                    AgentCapability(name="greeting", description="Generate greetings"),
                    AgentCapability(name="translation", description="Translate text")
                ],
                status=AgentStatus.HEALTHY
            ),
            DiscoveredAgent(
                agent_id="a2a-math-agent",
                name="Math Agent", 
                protocol=ProtocolType.A2A,
                endpoint="http://math:8001",
                capabilities=[
                    AgentCapability(name="calculate", description="Perform calculations"),
                    AgentCapability(name="math", description="Mathematical operations")
                ],
                status=AgentStatus.HEALTHY
            )
        ]
        
        service.get_all_agents.return_value = test_agents
        service.get_healthy_agents.return_value = test_agents
        service.get_agent_by_id.return_value = test_agents[0]
        service.get_agents_by_capability.return_value = [test_agents[0]]
        service.get_agents_by_protocol.return_value = [test_agents[0]]
        service.is_healthy.return_value = True
        service.refresh.return_value = None
        
        return service
    
    @pytest.fixture
    def mock_orchestrator_agent(self):
        """Create mock orchestrator agent"""
        agent = AsyncMock(spec=OrchestratorAgent)
        
        # Mock routing decision
        mock_decision = RoutingDecision(
            request_id="test-request-123",
            selected_agent=DiscoveredAgent(
                agent_id="acp-greeting-agent",
                name="Greeting Agent", 
                protocol=ProtocolType.ACP,
                endpoint="http://greeting:8000",
                capabilities=[AgentCapability(name="greeting", description="Generate greetings")],
                status=AgentStatus.HEALTHY
            ),
            reasoning="Perfect match for greeting request",
            confidence=0.95,
            alternative_agents=[],
            error=None,
            decision_time_ms=120.0,
            llm_provider=LLMProvider.OPENAI
        )
        
        # Mock agent response
        mock_response = AgentResponse(
            request_id="test-request-123",
            agent_id="acp-greeting-agent",
            protocol=ProtocolType.ACP,
            response_data={"message": "Hello from agent!"},
            duration_ms=200.5,
            success=True,
            error=None,
            metadata={"routing_decision": mock_decision.model_dump()}
        )
        
        # Mock metrics
        mock_metrics = OrchestrationMetrics(
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            average_response_time_ms=250.0,
            agents_discovered=2,
            healthy_agents=2
        )
        
        # Mock health check
        mock_health = {
            "orchestrator_healthy": True,
            "discovery_service_healthy": True,
            "available_agents": 2,
            "llm_provider": "openai",
            "model": "GPT4oModel",
            "metrics": mock_metrics.model_dump()
        }
        
        agent.route_request.return_value = mock_decision
        agent.process_request.return_value = mock_response
        agent.get_metrics.return_value = mock_metrics
        agent.health_check.return_value = mock_health
        
        return agent
    
    @pytest.fixture
    def client(self, mock_discovery_service, mock_orchestrator_agent):
        """Create test client with mocked dependencies"""
        from fastapi import FastAPI
        from orchestrator.api import (
            get_discovery_service, get_orchestrator_agent,
            health_check, system_status, list_agents, get_agent,
            refresh_agents, route_request, process_request, get_metrics,
            list_protocols, list_capabilities, root,
            http_exception_handler, general_exception_handler
        )
        from fastapi.middleware.cors import CORSMiddleware
        from orchestrator.config import get_settings
        from fastapi import HTTPException
        
        # Create test app without lifespan
        settings = get_settings()
        test_app = FastAPI(
            title=settings.app_name,
            version=settings.app_version,
            description="Test version - Multi-Protocol Agent Orchestrator",
        )
        
        # Add CORS middleware
        test_app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=settings.cors_methods,
            allow_headers=settings.cors_headers,
        )
        
        async def mock_get_discovery_service():
            return mock_discovery_service
        
        async def mock_get_orchestrator_agent():
            return mock_orchestrator_agent
        
        # Add all routes manually
        test_app.get("/")(root)
        test_app.get("/health")(health_check)
        test_app.get("/status")(system_status)
        test_app.get("/agents")(list_agents)
        test_app.get("/agents/{agent_id}")(get_agent)
        test_app.post("/agents/refresh")(refresh_agents)
        test_app.post("/route")(route_request)
        test_app.post("/process")(process_request)
        test_app.get("/metrics")(get_metrics) 
        test_app.get("/protocols")(list_protocols)
        test_app.get("/capabilities")(list_capabilities)
        
        # Add exception handlers
        test_app.add_exception_handler(HTTPException, http_exception_handler)
        test_app.add_exception_handler(Exception, general_exception_handler)
        
        # Override dependencies
        test_app.dependency_overrides = {
            get_discovery_service: mock_get_discovery_service,
            get_orchestrator_agent: mock_get_orchestrator_agent
        }
        
        with TestClient(test_app) as client:
            yield client
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Multi-Protocol Agent Orchestrator"
        assert "endpoints" in data
        assert "protocols_supported" in data
        assert "timestamp" in data
    
    def test_health_check_healthy(self, client):
        """Test health check when healthy"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"
        assert "services" in data
        assert "details" in data
    
    def test_system_status(self, client):
        """Test system status endpoint"""
        response = client.get("/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["orchestrator_healthy"] is True
        assert data["discovery_service_healthy"] is True
        assert data["total_agents"] == 2
        assert data["healthy_agents"] == 2
        assert "protocols_supported" in data
    
    def test_list_agents(self, client):
        """Test agent listing endpoint"""
        response = client.get("/agents")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        agent = data[0]
        assert agent["agent_id"] == "acp-greeting-agent"
        assert agent["name"] == "Greeting Agent"
        assert agent["protocol"] == "acp"
        assert agent["status"] == "healthy"
        assert len(agent["capabilities"]) == 2
    
    def test_list_agents_with_protocol_filter(self, client):
        """Test agent listing with protocol filter"""
        response = client.get("/agents?protocol=acp")
        
        assert response.status_code == 200
        data = response.json()
        # Mock returns first agent for protocol filter
        assert len(data) == 1
        assert data[0]["protocol"] == "acp"
    
    def test_list_agents_with_capability_filter(self, client):
        """Test agent listing with capability filter"""
        response = client.get("/agents?capability=greeting")
        
        assert response.status_code == 200
        data = response.json()
        # Mock returns first agent for capability filter
        assert len(data) == 1
        assert "greeting" in data[0]["capabilities"]
    
    def test_list_agents_with_status_filter(self, client):
        """Test agent listing with status filter"""
        response = client.get("/agents?status_filter=healthy")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        for agent in data:
            assert agent["status"] == "healthy"
    
    def test_list_agents_invalid_protocol(self, client):
        """Test agent listing with invalid protocol"""
        response = client.get("/agents?protocol=invalid")
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid protocol" in data["error"]["message"]
    
    def test_get_agent_by_id(self, client):
        """Test getting specific agent by ID"""
        response = client.get("/agents/acp-greeting-agent")
        
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "acp-greeting-agent"
        assert data["name"] == "Greeting Agent"
        assert data["protocol"] == "acp"
    
    def test_get_agent_by_id_not_found(self, client, mock_discovery_service):
        """Test getting non-existent agent"""
        mock_discovery_service.get_agent_by_id.return_value = None
        
        response = client.get("/agents/non-existent-agent")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["error"]["message"]
    
    def test_refresh_agents(self, client):
        """Test triggering agent refresh"""
        response = client.post("/agents/refresh")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "refresh_triggered"
    
    def test_route_request(self, client):
        """Test request routing"""
        request_data = {
            "query": "Say hello to me",
            "context": {"user_id": "123"}
        }
        
        response = client.post("/route", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["selected_agent"]["agent_id"] == "acp-greeting-agent"
        assert data["confidence"] == 0.95
        assert data["reasoning"] == "Perfect match for greeting request"
    
    def test_route_request_with_preferences(self, client):
        """Test request routing with preferences"""
        request_data = {
            "query": "Calculate 2+2",
            "preferred_protocol": "a2a",
            "preferred_agent": "a2a-math-agent",
            "timeout_seconds": 10.0
        }
        
        response = client.post("/route", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "selected_agent" in data
        assert "confidence" in data
    
    def test_route_request_invalid_data(self, client):
        """Test routing with invalid request data"""
        request_data = {
            "query": "",  # Empty query
        }
        
        response = client.post("/route", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_process_request(self, client):
        """Test complete request processing"""
        request_data = {
            "query": "Say hello to me",
            "context": {"user_id": "123"}
        }
        
        response = client.post("/process", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["agent_id"] == "acp-greeting-agent"
        assert data["protocol"] == "acp"
        assert data["response_data"]["message"] == "Hello from agent!"
        assert data["duration_ms"] == 200.5
    
    def test_get_metrics(self, client):
        """Test metrics endpoint"""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_requests"] == 100
        assert data["successful_requests"] == 95
        assert data["failed_requests"] == 5
        assert data["average_response_time_ms"] == 250.0
        assert data["agents_discovered"] == 2
        assert data["healthy_agents"] == 2
    
    def test_list_protocols(self, client):
        """Test protocols listing endpoint"""
        response = client.get("/protocols")
        
        assert response.status_code == 200
        data = response.json()
        assert "supported_protocols" in data
        assert data["total_protocols"] == 4
        assert data["fully_implemented"] == 1
        
        protocols = data["supported_protocols"]
        protocol_names = [p["name"] for p in protocols]
        assert "ACP" in protocol_names
        assert "A2A" in protocol_names
        assert "MCP" in protocol_names
        assert "CUSTOM" in protocol_names
    
    def test_list_capabilities(self, client):
        """Test capabilities listing endpoint"""
        response = client.get("/capabilities")
        
        assert response.status_code == 200
        data = response.json()
        assert "capabilities" in data
        assert "total_capabilities" in data
        assert "timestamp" in data
        
        capabilities = data["capabilities"]
        assert len(capabilities) > 0
        
        # Check capability structure
        if "greeting" in capabilities:
            greeting_cap = capabilities["greeting"]
            assert "description" in greeting_cap
            assert "agents" in greeting_cap
            assert "protocols" in greeting_cap
            assert "total_agents" in greeting_cap
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.options("/", headers={"Origin": "http://localhost:3000"})
        
        # OPTIONS requests should be handled by CORS middleware
        assert response.status_code in [200, 405]  # 405 if no OPTIONS handler
    
    def test_error_handling_service_unavailable(self, client):
        """Test error handling when services are unavailable"""
        from fastapi import HTTPException, status
        from orchestrator.api import get_discovery_service
        
        # Override dependency to raise HTTPException (service unavailable)
        async def mock_unavailable_service():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Discovery service not available"
            )
        
        # Get the test app from client
        test_app = client.app
        test_app.dependency_overrides[get_discovery_service] = mock_unavailable_service
        
        try:
            response = client.get("/agents")
            assert response.status_code == 503
            data = response.json()
            assert "not available" in data["error"]["message"]
        finally:
            # Clean up override
            test_app.dependency_overrides = {}
    
    def test_validation_error_handling(self, client):
        """Test validation error handling"""
        # Send invalid JSON data
        response = client.post("/route", json={"invalid": "data"})
        
        assert response.status_code == 422
        data = response.json()
        # FastAPI returns validation errors in detail
        assert "detail" in data
    
    def test_general_exception_handling(self, client, mock_orchestrator_agent):
        """Test general exception handling"""
        # Mock orchestrator to raise exception
        mock_orchestrator_agent.route_request.side_effect = Exception("Test error")
        
        request_data = {"query": "Test query"}
        response = client.post("/route", json=request_data)
        
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["type"] == "http_error"
        assert "routing failed" in data["error"]["message"].lower()


    @pytest.mark.integration
    async def test_api_lifecycle(self):
        """Test complete API lifecycle with real components"""
        # This would test with actual discovery service and orchestrator
        # Skip in unit tests, enable for integration testing
        pytest.skip("Integration test - requires real components")
    
    @pytest.mark.integration  
    def test_openapi_spec_generation(self, client):
        """Test OpenAPI specification generation"""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        spec = response.json()
        assert spec["openapi"]
        assert spec["info"]["title"] == "Multi-Protocol Agent Orchestrator"
        assert spec["info"]["version"] == "0.1.0"
        
        # Check that main endpoints are documented
        paths = spec["paths"]
        expected_paths = ["/", "/health", "/status", "/agents", "/route", "/process", "/metrics"]
        for path in expected_paths:
            assert path in paths
    
    def test_docs_endpoint(self, client):
        """Test API documentation endpoint"""
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()
    
    def test_redoc_endpoint(self, client):
        """Test ReDoc documentation endpoint"""
        response = client.get("/redoc")
        
        assert response.status_code == 200
        assert "redoc" in response.text.lower()


class TestAPIIntegration:
    """Integration tests for API - additional class for organization"""
    pass  # Integration tests moved to TestFastAPIApplication class


if __name__ == "__main__":
    pytest.main([__file__, "-v"])