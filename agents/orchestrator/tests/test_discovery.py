"""Tests for unified discovery service"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import aiohttp

from orchestrator.discovery import UnifiedDiscoveryService
from orchestrator.models import ProtocolType, AgentStatus, AgentCapability, DiscoveredAgent, AgentRegistryEntry

pytestmark = pytest.mark.asyncio


class TestUnifiedDiscoveryService:
    """Test unified discovery service"""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing"""
        settings = MagicMock()
        settings.discovery_interval_seconds = 60
        settings.discovery_timeout_seconds = 5
        return settings
    
    @pytest.fixture
    def discovery_service(self, mock_settings):
        """Create discovery service with mocked settings"""
        with patch('orchestrator.discovery.get_settings', return_value=mock_settings):
            service = UnifiedDiscoveryService()
            return service
    
    async def test_start_and_stop(self, discovery_service):
        """Test starting and stopping the discovery service"""
        # Mock refresh to avoid actual HTTP discovery
        with patch.object(discovery_service, 'refresh', new_callable=AsyncMock):
            await discovery_service.start()
            
            assert discovery_service._running is True
            assert discovery_service._discovery_task is not None
            assert len(discovery_service.agent_registry) == 0  # No agents discovered yet
            
            await discovery_service.stop()
            
            assert discovery_service._running is False
    
    async def test_http_discovery_success(self, discovery_service):
        """Test successful HTTP-based agent discovery"""
        # Mock HTTP responses for known endpoints
        mock_agents = [
            DiscoveredAgent(
                agent_id="acp-hello-world",
                name="Hello World Agent",
                protocol=ProtocolType.ACP,
                endpoint="http://localhost:8000",
                capabilities=[
                    AgentCapability(name="greeting", description="Generate greetings")
                ],
                status=AgentStatus.HEALTHY,
                discovered_at=datetime.utcnow(),
                last_seen=datetime.utcnow()
            )
        ]
        
        with patch.object(discovery_service, '_discover_agents_http', 
                         new_callable=AsyncMock, return_value=mock_agents):
            await discovery_service.refresh()
            
            assert len(discovery_service.agent_registry) == 1
            assert "acp-hello-world" in discovery_service.agent_registry
    
    async def test_http_discovery_failure(self, discovery_service):
        """Test HTTP discovery with connection failures"""
        with patch.object(discovery_service, '_discover_agents_http', 
                         new_callable=AsyncMock, side_effect=aiohttp.ClientError("Connection failed")):
            # Should not raise exception, just log error
            await discovery_service.refresh()
            
            assert len(discovery_service.agent_registry) == 0
    
    async def test_update_registry_new_agent(self, discovery_service):
        """Test updating registry with a new agent"""
        agent = DiscoveredAgent(
            agent_id="new-agent",
            name="New Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://localhost:8001",
            capabilities=[AgentCapability(name="test", description="Test capability")],
            status=AgentStatus.HEALTHY,
            discovered_at=datetime.utcnow(),
            last_seen=datetime.utcnow()
        )
        
        await discovery_service._update_registry([agent])
        
        assert len(discovery_service.agent_registry) == 1
        assert "new-agent" in discovery_service.agent_registry
        assert discovery_service.agent_registry["new-agent"].last_seen is not None
    
    async def test_update_registry_existing_agent(self, discovery_service):
        """Test updating registry with existing agent"""
        agent = DiscoveredAgent(
            agent_id="existing-agent",
            name="Existing Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://localhost:8002",
            capabilities=[AgentCapability(name="test", description="Test capability")],
            status=AgentStatus.HEALTHY,
            discovered_at=datetime.utcnow()
        )
        
        # Add agent to registry first as AgentRegistryEntry
        old_time = datetime.utcnow() - timedelta(minutes=5)
        registry_entry = AgentRegistryEntry(agent=agent, last_seen=old_time)
        discovery_service.agent_registry["existing-agent"] = registry_entry
        
        # Update with newer agent
        updated_agent = DiscoveredAgent(
            agent_id="existing-agent",
            name="Existing Agent Updated",
            protocol=ProtocolType.ACP,
            endpoint="http://localhost:8002",
            capabilities=[AgentCapability(name="test", description="Test capability")],
            status=AgentStatus.HEALTHY,
            discovered_at=datetime.utcnow()
        )
        
        await discovery_service._update_registry([updated_agent])
        
        assert len(discovery_service.agent_registry) == 1
        registry_entry = discovery_service.agent_registry["existing-agent"]
        assert registry_entry.last_seen > old_time
        assert registry_entry.agent.name == "Existing Agent Updated"
    
    async def test_get_healthy_agents(self, discovery_service):
        """Test getting healthy agents from registry"""
        healthy_agent = DiscoveredAgent(
            agent_id="healthy-agent",
            name="Healthy Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://localhost:8001",
            capabilities=[],
            status=AgentStatus.HEALTHY,
            discovered_at=datetime.utcnow()
        )
        
        unhealthy_agent = DiscoveredAgent(
            agent_id="unhealthy-agent", 
            name="Unhealthy Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://localhost:8002",
            capabilities=[],
            status=AgentStatus.UNHEALTHY,
            discovered_at=datetime.utcnow()
        )
        
        discovery_service.agent_registry["healthy-agent"] = AgentRegistryEntry(agent=healthy_agent)
        discovery_service.agent_registry["unhealthy-agent"] = AgentRegistryEntry(agent=unhealthy_agent)
        
        healthy_agents = await discovery_service.get_healthy_agents()
        
        assert len(healthy_agents) == 1
        assert healthy_agents[0].agent_id == "healthy-agent"
    
    async def test_get_agents_by_protocol(self, discovery_service):
        """Test filtering agents by protocol"""
        acp_agent = DiscoveredAgent(
            agent_id="acp-agent",
            name="ACP Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://localhost:8001",
            capabilities=[],
            status=AgentStatus.HEALTHY,
            discovered_at=datetime.utcnow()
        )
        
        mcp_agent = DiscoveredAgent(
            agent_id="mcp-agent",
            name="MCP Agent", 
            protocol=ProtocolType.MCP,
            endpoint="http://localhost:8002",
            capabilities=[],
            status=AgentStatus.HEALTHY,
            discovered_at=datetime.utcnow()
        )
        
        discovery_service.agent_registry["acp-agent"] = AgentRegistryEntry(agent=acp_agent)
        discovery_service.agent_registry["mcp-agent"] = AgentRegistryEntry(agent=mcp_agent)
        
        acp_agents = await discovery_service.get_agents_by_protocol(ProtocolType.ACP)
        
        assert len(acp_agents) == 1
        assert acp_agents[0].agent_id == "acp-agent"
    
    async def test_get_agents_by_capability(self, discovery_service):
        """Test filtering agents by capability"""
        agent_with_greeting = DiscoveredAgent(
            agent_id="greeting-agent",
            name="Greeting Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://localhost:8001",
            capabilities=[
                AgentCapability(name="greeting", description="Generate greetings"),
                AgentCapability(name="translation", description="Translate text")
            ],
            status=AgentStatus.HEALTHY,
            discovered_at=datetime.utcnow()
        )
        
        agent_without_greeting = DiscoveredAgent(
            agent_id="other-agent",
            name="Other Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://localhost:8002",
            capabilities=[
                AgentCapability(name="calculation", description="Perform calculations")
            ],
            status=AgentStatus.HEALTHY,
            discovered_at=datetime.utcnow()
        )
        
        discovery_service.agent_registry["greeting-agent"] = AgentRegistryEntry(agent=agent_with_greeting)
        discovery_service.agent_registry["other-agent"] = AgentRegistryEntry(agent=agent_without_greeting)
        
        greeting_agents = await discovery_service.get_agents_by_capability("greeting")
        
        assert len(greeting_agents) == 1
        assert greeting_agents[0].agent_id == "greeting-agent"
    
    async def test_cleanup_registry(self, discovery_service):
        """Test cleanup of stale agents"""
        # Create agents with different last_seen times
        recent_agent = DiscoveredAgent(
            agent_id="recent-agent",
            name="Recent Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://localhost:8001",
            capabilities=[],
            status=AgentStatus.HEALTHY,
            discovered_at=datetime.utcnow()
        )
        
        stale_agent = DiscoveredAgent(
            agent_id="stale-agent",
            name="Stale Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://localhost:8002",
            capabilities=[],
            status=AgentStatus.HEALTHY,
            discovered_at=datetime.utcnow()
        )
        
        # Add entries with different last_seen times
        discovery_service.agent_registry["recent-agent"] = AgentRegistryEntry(
            agent=recent_agent, 
            last_seen=datetime.utcnow()  # Recent
        )
        discovery_service.agent_registry["stale-agent"] = AgentRegistryEntry(
            agent=stale_agent, 
            last_seen=datetime.utcnow() - timedelta(hours=2)  # Stale
        )
        
        # Cleanup uses hardcoded 1 hour threshold 
        discovery_service._cleanup_registry()
        
        # Only recent agent should remain
        assert len(discovery_service.agent_registry) == 1
        assert "recent-agent" in discovery_service.agent_registry
        assert "stale-agent" not in discovery_service.agent_registry
    
    async def test_mark_agent_request(self, discovery_service):
        """Test marking agent request for metrics"""
        agent = DiscoveredAgent(
            agent_id="test-agent",
            name="Test Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://localhost:8001",
            capabilities=[],
            status=AgentStatus.HEALTHY,
            discovered_at=datetime.utcnow()
        )
        
        discovery_service.agent_registry["test-agent"] = AgentRegistryEntry(agent=agent)
        
        await discovery_service.mark_agent_request("test-agent")
        
        # Check that agent's request count was updated
        registry_entry = discovery_service.agent_registry["test-agent"]
        assert registry_entry.request_count == 1
        assert registry_entry.last_request is not None
    
    async def test_is_healthy(self, discovery_service):
        """Test discovery service health check"""
        # The is_healthy method checks if discovery service itself is healthy
        discovery_service._running = True
        
        assert await discovery_service.is_healthy() is True
        
        discovery_service._running = False
        assert await discovery_service.is_healthy() is False
    
    def test_get_registry_stats(self, discovery_service):
        """Test getting registry statistics"""
        # Add some mock agents
        agent1 = DiscoveredAgent(
            agent_id="agent1",
            name="Agent 1",
            protocol=ProtocolType.ACP,
            endpoint="http://localhost:8001",
            capabilities=[],
            status=AgentStatus.HEALTHY,
            discovered_at=datetime.utcnow()
        )
        
        agent2 = DiscoveredAgent(
            agent_id="agent2",
            name="Agent 2",
            protocol=ProtocolType.MCP,
            endpoint="http://localhost:8002",
            capabilities=[],
            status=AgentStatus.UNHEALTHY,
            discovered_at=datetime.utcnow()
        )
        
        discovery_service.agent_registry["agent1"] = AgentRegistryEntry(agent=agent1)
        discovery_service.agent_registry["agent2"] = AgentRegistryEntry(agent=agent2)
        
        stats = discovery_service.get_registry_stats()
        
        assert stats["total_agents"] == 2
        assert stats["healthy_agents"] == 1
        assert stats["by_protocol"]["acp"] == 1
        assert stats["by_protocol"]["mcp"] == 1