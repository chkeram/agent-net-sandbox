"""Tests for A2A discovery strategy"""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from orchestrator.protocols.a2a_discovery import A2ADiscoveryStrategy
from orchestrator.models import ProtocolType, AgentStatus
from tests.fixtures import (
    create_container_info,
    create_a2a_agent_info_response,
    create_health_response
)

pytestmark = pytest.mark.asyncio


class TestA2ADiscoveryStrategy:
    """Test A2A discovery strategy"""
    
    @pytest.fixture
    def strategy(self):
        """Create A2A discovery strategy"""
        return A2ADiscoveryStrategy()
    
    async def test_extract_base_info(self, strategy):
        """Test extracting base information from container"""
        container_info = create_container_info(
            container_id="test-container-456",
            name="a2a-agent",
            protocol="a2a",
            agent_type="math",
            port=9000
        )
        
        base_info = await strategy.extract_base_info(container_info)
        
        assert base_info["container_id"] == "test-container-456"
        assert base_info["container_name"] == "a2a-agent"
        assert base_info["protocol"] == "a2a"
        assert base_info["agent_type"] == "math"
        assert base_info["version"] == "1.0.0"
        assert base_info["port"] == 9000
    
    async def test_discover_no_port(self, strategy):
        """Test discovery when container has no port"""
        container_info = create_container_info(port=None)
        # Remove port information
        container_info["Ports"] = []
        container_info["NetworkSettings"]["Ports"] = {}
        
        agent = await strategy.discover(container_info)
        
        # Should return None when no port is found
        assert agent is None
    
    async def test_successful_discovery(self, strategy):
        """Test successful A2A agent discovery"""
        container_info = create_container_info(protocol="a2a")
        
        # Mock the HTTP responses
        agent_info_data = create_a2a_agent_info_response()
        
        agent_info_response = MagicMock()
        agent_info_response.status_code = 200
        agent_info_response.json.return_value = agent_info_data
        
        mock_http_client = AsyncMock()
        
        # Create async mock for get method
        async def mock_get_func(url):
            return agent_info_response
        
        mock_http_client.get = mock_get_func
        
        # Mock httpx.AsyncClient context manager
        with patch('orchestrator.protocols.a2a_discovery.httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_http_client
            mock_client_class.return_value.__aexit__.return_value = None
            
            agent = await strategy.discover(container_info)
        
        # Verify agent was discovered correctly
        assert agent is not None
        assert agent.agent_id == "a2a-math-agent"
        assert agent.name == "A2A Math Agent"
        assert agent.protocol == ProtocolType.A2A
        assert agent.endpoint.startswith("http://")
        assert agent.status == AgentStatus.HEALTHY
        
        # Check capabilities
        assert len(agent.capabilities) >= 1
        calc_cap = next((cap for cap in agent.capabilities if cap.name == "calculate"), None)
        assert calc_cap is not None
        assert calc_cap.description == "Perform mathematical calculations"
        
        # Check metadata
        assert agent.metadata["protocol_version"] == "1.0"
        assert agent.metadata["supports_peer_discovery"] is True
        assert agent.metadata["discovery_method"] == "a2a_native"
    
    async def test_discovery_fallback(self, strategy):
        """Test fallback discovery when HTTP fails"""
        container_info = create_container_info(protocol="a2a")
        
        # Mock HTTP failure
        with patch('orchestrator.protocols.a2a_discovery.httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.side_effect = httpx.RequestError("Connection failed")
            
            agent = await strategy.discover(container_info)
        
        # Should fall back to label-based discovery
        assert agent is not None
        assert agent.metadata["discovery_method"] == "fallback"
        assert agent.metadata["fallback_reason"] == "native_discovery_failed"
    
    async def test_health_check_healthy(self, strategy):
        """Test health check with healthy agent"""
        from orchestrator.models import DiscoveredAgent, AgentCapability
        
        agent = DiscoveredAgent(
            agent_id="test-agent",
            name="Test Agent",
            protocol=ProtocolType.A2A,
            endpoint="http://test:8000",
            capabilities=[AgentCapability(name="test", description="Test")]
        )
        
        # Mock successful health response
        health_response = MagicMock()
        health_response.status_code = 200
        health_response.json.return_value = create_health_response("healthy")
        
        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=health_response)
        
        with patch('orchestrator.protocols.a2a_discovery.httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_http_client
            mock_client_class.return_value.__aexit__.return_value = None
            status = await strategy.health_check(agent)
        
        assert status == AgentStatus.HEALTHY
    
    async def test_health_check_failure(self, strategy):
        """Test health check when request fails"""
        from orchestrator.models import DiscoveredAgent, AgentCapability
        
        agent = DiscoveredAgent(
            agent_id="test-agent",
            name="Test Agent",
            protocol=ProtocolType.A2A,
            endpoint="http://test:8000",
            capabilities=[AgentCapability(name="test", description="Test")]
        )
        
        with patch('orchestrator.protocols.a2a_discovery.httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.side_effect = httpx.RequestError("Connection failed")
            status = await strategy.health_check(agent)
        
        assert status == AgentStatus.UNKNOWN