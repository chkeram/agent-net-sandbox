"""Tests for ACP discovery strategy"""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from orchestrator.protocols.acp_discovery import ACPDiscoveryStrategy
from orchestrator.models import ProtocolType, AgentStatus
from tests.fixtures import (
    create_container_info,
    create_acp_capabilities_response,
    create_acp_schema_response,
    create_health_response
)

pytestmark = pytest.mark.asyncio


class TestACPDiscoveryStrategy:
    """Test ACP discovery strategy"""
    
    @pytest.fixture
    def strategy(self):
        """Create ACP discovery strategy"""
        return ACPDiscoveryStrategy()
    
    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client for testing"""
        client = AsyncMock()
        return client
    
    async def test_successful_discovery(self, strategy, mock_http_client):
        """Test successful ACP agent discovery"""
        # Setup mock responses
        capabilities_data = create_acp_capabilities_response()
        schema_data = create_acp_schema_response()
        
        capabilities_response = MagicMock()
        capabilities_response.status_code = 200
        capabilities_response.json.return_value = capabilities_data
        
        schema_response = MagicMock()
        schema_response.status_code = 200
        schema_response.json.return_value = schema_data
        
        # Create async mock for get method
        async def mock_get_func(url):
            if "capabilities" in url:
                return capabilities_response
            elif "schema" in url:
                return schema_response
            return capabilities_response
        
        mock_http_client.get = mock_get_func
        
        # Mock httpx.AsyncClient context manager
        with patch('orchestrator.protocols.acp_discovery.httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_http_client
            mock_client_class.return_value.__aexit__.return_value = None
            container_info = create_container_info(protocol="acp")
            agent = await strategy.discover(container_info)
        
        # Verify agent was discovered correctly
        assert agent is not None
        assert agent.agent_id == "acp-test-agent"
        assert agent.name == "ACP Test Agent"
        assert agent.protocol == ProtocolType.ACP
        assert agent.endpoint == "http://test-agent:8000"
        assert agent.status == AgentStatus.HEALTHY
        
        # Check capabilities
        assert len(agent.capabilities) == 2
        greeting_cap = next((cap for cap in agent.capabilities if cap.name == "greeting"), None)
        assert greeting_cap is not None
        assert greeting_cap.description == "Generate greetings in multiple languages"
        
        # Check metadata
        assert agent.metadata["acp_version"] == "0.1"
        assert agent.metadata["auth_required"] is False
        assert agent.metadata["streaming_supported"] is True
        assert agent.metadata["discovery_method"] == "acp_native"
    
    async def test_discovery_with_missing_capabilities(self, strategy, mock_http_client):
        """Test discovery when capabilities endpoint fails"""
        # Setup mock responses - capabilities fails, schema succeeds
        capabilities_response = AsyncMock()
        capabilities_response.status_code = 404
        
        schema_response = AsyncMock()
        schema_response.status_code = 200
        schema_response.json.return_value = create_acp_schema_response()
        
        mock_http_client.get.side_effect = [capabilities_response, schema_response]
        
        with patch('orchestrator.protocols.acp_discovery.httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_http_client
            mock_client_class.return_value.__aexit__.return_value = None
            container_info = create_container_info(protocol="acp")
            agent = await strategy.discover(container_info)
        
        # Should fall back to label-based discovery
        assert agent is not None
        assert agent.agent_id == "acp-test-agent"
        assert agent.metadata["discovery_method"] == "fallback"
        assert len(agent.capabilities) == 2  # From container labels
    
    async def test_discovery_complete_failure(self, strategy):
        """Test discovery when all HTTP requests fail"""
        with patch('orchestrator.protocols.acp_discovery.httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.side_effect = httpx.RequestError("Connection failed")
            container_info = create_container_info(protocol="acp")
            agent = await strategy.discover(container_info)
        
        # Should fall back to label-based discovery
        assert agent is not None
        assert agent.metadata["discovery_method"] == "fallback"
        assert agent.metadata["fallback_reason"] == "native_discovery_failed"
    
    async def test_discovery_no_port(self, strategy):
        """Test discovery when container has no port"""
        container_info = create_container_info(port=None)
        # Remove port information
        container_info["Ports"] = []
        container_info["NetworkSettings"]["Ports"] = {}
        
        agent = await strategy.discover(container_info)
        
        # Should return None when no port is found
        assert agent is None
    
    async def test_health_check_healthy(self, strategy):
        """Test health check with healthy agent"""
        from orchestrator.models import DiscoveredAgent, AgentCapability
        
        agent = DiscoveredAgent(
            agent_id="test-agent",
            name="Test Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://test:8000",
            capabilities=[AgentCapability(name="test", description="Test")]
        )
        
        # Mock successful health response
        health_response = MagicMock()
        health_response.status_code = 200
        health_response.json.return_value = create_health_response("healthy")
        
        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=health_response)
        
        with patch('orchestrator.protocols.acp_discovery.httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_http_client
            mock_client_class.return_value.__aexit__.return_value = None
            status = await strategy.health_check(agent)
        
        assert status == AgentStatus.HEALTHY
    
    async def test_health_check_degraded(self, strategy):
        """Test health check with degraded agent"""
        from orchestrator.models import DiscoveredAgent, AgentCapability
        
        agent = DiscoveredAgent(
            agent_id="test-agent",
            name="Test Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://test:8000",
            capabilities=[AgentCapability(name="test", description="Test")]
        )
        
        # Mock degraded health response
        health_response = MagicMock()
        health_response.status_code = 200
        health_response.json.return_value = create_health_response("degraded")
        
        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=health_response)
        
        with patch('orchestrator.protocols.acp_discovery.httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_http_client
            mock_client_class.return_value.__aexit__.return_value = None
            status = await strategy.health_check(agent)
        
        assert status == AgentStatus.DEGRADED
    
    async def test_health_check_failure(self, strategy):
        """Test health check when request fails"""
        from orchestrator.models import DiscoveredAgent, AgentCapability
        
        agent = DiscoveredAgent(
            agent_id="test-agent",
            name="Test Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://test:8000",
            capabilities=[AgentCapability(name="test", description="Test")]
        )
        
        with patch('orchestrator.protocols.acp_discovery.httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.side_effect = httpx.RequestError("Connection failed")
            status = await strategy.health_check(agent)
        
        assert status == AgentStatus.UNKNOWN
    
    async def test_parse_acp_capabilities_with_mixed_types(self, strategy):
        """Test parsing capabilities with mixed dict/string types"""
        capabilities_data = {
            "capabilities": [
                {
                    "name": "greeting",
                    "description": "Generate greetings",
                    "examples": [{"input": {"name": "test"}, "output": {"message": "Hello, test!"}}]
                },
                "simple_capability"  # String capability
            ]
        }
        
        schema_data = {
            "input_schema": {"type": "object"},
            "output_schema": {"type": "object"}
        }
        
        capabilities = strategy._parse_acp_capabilities(capabilities_data, schema_data)
        
        assert len(capabilities) == 2
        
        # Check dict capability
        dict_cap = next((cap for cap in capabilities if cap.name == "greeting"), None)
        assert dict_cap is not None
        assert dict_cap.description == "Generate greetings"
        assert len(dict_cap.examples) == 1
        
        # Check string capability
        str_cap = next((cap for cap in capabilities if cap.name == "simple_capability"), None)
        assert str_cap is not None
        assert str_cap.description == "ACP capability: simple_capability"
        assert "string-capability" in str_cap.tags
    
    async def test_fallback_discovery_with_capabilities(self, strategy):
        """Test fallback discovery with capabilities in labels"""
        base_info = {
            "container_id": "test-123",
            "container_name": "test-agent",
            "protocol": "acp",
            "agent_type": "test",
            "version": "1.0.0",
            "port": 8000,
            "labels": {
                "agent.protocol": "acp",
                "agent.capabilities": "greeting,translation,testing",
                "agent.name": "Fallback Test Agent"
            }
        }
        
        endpoint = "http://test:8000"
        agent = strategy._fallback_discovery(base_info, endpoint)
        
        assert agent is not None
        assert agent.name == "Fallback Test Agent"
        assert len(agent.capabilities) == 3
        
        cap_names = [cap.name for cap in agent.capabilities]
        assert "greeting" in cap_names
        assert "translation" in cap_names
        assert "testing" in cap_names
        
        # All capabilities should be tagged as fallback
        for cap in agent.capabilities:
            assert "label-fallback" in cap.tags
    
    async def test_extract_base_info(self, strategy):
        """Test extracting base information from container"""
        container_info = create_container_info(
            container_id="test-container-456",
            name="custom-agent",
            protocol="acp",
            agent_type="custom",
            port=9000
        )
        
        base_info = await strategy.extract_base_info(container_info)
        
        assert base_info["container_id"] == "test-container-456"
        assert base_info["container_name"] == "custom-agent"
        assert base_info["protocol"] == "acp"
        assert base_info["agent_type"] == "custom"
        assert base_info["version"] == "1.0.0"
        assert base_info["port"] == 9000