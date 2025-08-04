"""Tests for unified discovery service"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from orchestrator.discovery import UnifiedDiscoveryService
from orchestrator.models import ProtocolType, AgentStatus, AgentCapability, DiscoveredAgent
from tests.fixtures import create_container_info, create_mock_container

pytestmark = pytest.mark.asyncio


class TestUnifiedDiscoveryService:
    """Test unified discovery service"""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing"""
        settings = MagicMock()
        settings.docker_available = True
        settings.discovery_interval_seconds = 60
        settings.docker_network = "test-network"
        return settings
    
    @pytest.fixture
    def mock_docker_client(self):
        """Mock Docker client"""
        client = MagicMock()
        return client
    
    @pytest.fixture
    def discovery_service(self, mock_settings):
        """Create discovery service with mocked settings"""
        with patch('orchestrator.discovery.get_settings', return_value=mock_settings):
            service = UnifiedDiscoveryService()
            return service
    
    async def test_start_and_stop(self, discovery_service, mock_docker_client):
        """Test starting and stopping the discovery service"""
        with patch('docker.from_env', return_value=mock_docker_client):
            # Mock refresh to avoid actual discovery
            with patch.object(discovery_service, 'refresh', new_callable=AsyncMock):
                await discovery_service.start()
                
                assert discovery_service._running is True
                assert discovery_service.docker_client is not None
                assert discovery_service._discovery_task is not None
                
                await discovery_service.stop()
                
                assert discovery_service._running is False
    
    async def test_start_without_docker(self, discovery_service):
        """Test starting when Docker is not available"""
        discovery_service.settings.docker_available = False
        
        with patch.object(discovery_service, 'refresh', new_callable=AsyncMock):
            await discovery_service.start()
            
            assert discovery_service._running is True
            assert discovery_service.docker_client is None
    
    async def test_get_agent_containers(self, discovery_service, mock_docker_client):
        """Test getting agent containers from Docker"""
        # Create mock containers
        agent_container = create_mock_container(create_container_info(protocol="acp"))
        non_agent_container = create_mock_container({
            "Id": "non-agent-123",
            "Names": ["/regular-container"],
            "Config": {"Labels": {"some.label": "value"}}
        })
        
        mock_docker_client.containers.list.return_value = [
            agent_container,
            non_agent_container
        ]
        
        discovery_service.docker_client = mock_docker_client
        
        containers = discovery_service._get_agent_containers()
        
        # Should only return containers with agent labels
        assert len(containers) == 1
        assert containers[0] == agent_container
        
        # Verify Docker API was called correctly
        mock_docker_client.containers.list.assert_called_once_with(
            filters={"network": "test-network"}
        )
    
    async def test_discover_container_acp(self, discovery_service):
        """Test discovering an ACP container"""
        container_info = create_container_info(protocol="acp")
        mock_container = create_mock_container(container_info)
        
        # Mock the ACP discovery strategy
        mock_agent = DiscoveredAgent(
            agent_id="acp-test-agent",
            name="Test ACP Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://test:8000",
            capabilities=[AgentCapability(name="test", description="Test")]
        )
        
        with patch('orchestrator.discovery.get_discovery_strategy') as mock_get_strategy:
            mock_strategy = AsyncMock()
            mock_strategy.discover.return_value = mock_agent
            mock_get_strategy.return_value = mock_strategy
            
            agent = await discovery_service._discover_container(mock_container)
            
            assert agent is not None
            assert agent.agent_id == "acp-test-agent"
            assert agent.protocol == ProtocolType.ACP
            
            # Verify strategy was called correctly
            mock_get_strategy.assert_called_once_with("acp")
            mock_strategy.discover.assert_called_once_with(container_info)
    
    async def test_discover_container_skip_orchestrator(self, discovery_service):
        """Test that orchestrator containers are skipped"""
        container_info = create_container_info(protocol="orchestrator")
        mock_container = create_mock_container(container_info)
        
        agent = await discovery_service._discover_container(mock_container)
        
        # Should return None for orchestrator containers
        assert agent is None
    
    async def test_discover_container_unknown_protocol(self, discovery_service):
        """Test discovering container with unknown protocol"""
        container_info = create_container_info(protocol="unknown")
        mock_container = create_mock_container(container_info)
        
        # Mock the generic discovery strategy
        mock_agent = DiscoveredAgent(
            agent_id="generic-test-agent",
            name="Test Generic Agent",
            protocol=ProtocolType.CUSTOM,
            endpoint="http://test:8000",
            capabilities=[]
        )
        
        with patch('orchestrator.discovery.get_discovery_strategy') as mock_get_strategy:
            mock_strategy = AsyncMock()
            mock_strategy.discover.return_value = mock_agent
            mock_get_strategy.return_value = mock_strategy
            
            agent = await discovery_service._discover_container(mock_container)
            
            assert agent is not None
            assert agent.protocol == ProtocolType.CUSTOM
    
    async def test_update_registry_new_agent(self, discovery_service):
        """Test updating registry with a new agent"""
        agent = DiscoveredAgent(
            agent_id="new-agent",
            name="New Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://test:8000",
            capabilities=[]
        )
        
        # Mock health check
        with patch('orchestrator.discovery.get_discovery_strategy') as mock_get_strategy:
            mock_strategy = AsyncMock()
            mock_strategy.health_check.return_value = AgentStatus.HEALTHY
            mock_get_strategy.return_value = mock_strategy
            
            await discovery_service._update_registry([agent])
            
            assert len(discovery_service.agent_registry) == 1
            assert "new-agent" in discovery_service.agent_registry
            
            entry = discovery_service.agent_registry["new-agent"]
            assert entry.agent.agent_id == "new-agent"
            assert entry.agent.status == AgentStatus.HEALTHY
            assert entry.consecutive_failures == 0
    
    async def test_update_registry_existing_agent(self, discovery_service):
        """Test updating registry with an existing agent"""
        # Create existing registry entry
        from orchestrator.models import AgentRegistryEntry
        
        old_agent = DiscoveredAgent(
            agent_id="existing-agent",
            name="Old Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://test:8000",
            capabilities=[]
        )
        
        entry = AgentRegistryEntry(agent=old_agent)
        entry.mark_failure()  # Add some failures
        entry.mark_failure()
        discovery_service.agent_registry["existing-agent"] = entry
        
        # Update with new agent info
        new_agent = DiscoveredAgent(
            agent_id="existing-agent",
            name="Updated Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://test:8000",
            capabilities=[]
        )
        
        # Mock health check
        with patch('orchestrator.discovery.get_discovery_strategy') as mock_get_strategy:
            mock_strategy = AsyncMock()
            mock_strategy.health_check.return_value = AgentStatus.HEALTHY
            mock_get_strategy.return_value = mock_strategy
            
            await discovery_service._update_registry([new_agent])
            
            # Should update existing entry and reset failures
            assert len(discovery_service.agent_registry) == 1
            entry = discovery_service.agent_registry["existing-agent"]
            assert entry.agent.name == "Updated Agent"
            assert entry.consecutive_failures == 0
    
    async def test_get_healthy_agents(self, discovery_service):
        """Test getting only healthy agents"""
        from orchestrator.models import AgentRegistryEntry
        
        # Create agents with different health statuses
        healthy_agent = DiscoveredAgent(
            agent_id="healthy-agent",
            name="Healthy Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://test:8000",
            capabilities=[],
            status=AgentStatus.HEALTHY
        )
        
        unhealthy_agent = DiscoveredAgent(
            agent_id="unhealthy-agent",
            name="Unhealthy Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://test:8001",
            capabilities=[],
            status=AgentStatus.UNHEALTHY
        )
        
        discovery_service.agent_registry = {
            "healthy-agent": AgentRegistryEntry(agent=healthy_agent),
            "unhealthy-agent": AgentRegistryEntry(agent=unhealthy_agent)
        }
        
        healthy_agents = await discovery_service.get_healthy_agents()
        
        assert len(healthy_agents) == 1
        assert healthy_agents[0].agent_id == "healthy-agent"
    
    async def test_get_agents_by_protocol(self, discovery_service):
        """Test getting agents by protocol type"""
        from orchestrator.models import AgentRegistryEntry
        
        acp_agent = DiscoveredAgent(
            agent_id="acp-agent",
            name="ACP Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://test:8000",
            capabilities=[]
        )
        
        a2a_agent = DiscoveredAgent(
            agent_id="a2a-agent",
            name="A2A Agent",
            protocol=ProtocolType.A2A,
            endpoint="http://test:8001",
            capabilities=[]
        )
        
        discovery_service.agent_registry = {
            "acp-agent": AgentRegistryEntry(agent=acp_agent),
            "a2a-agent": AgentRegistryEntry(agent=a2a_agent)
        }
        
        acp_agents = await discovery_service.get_agents_by_protocol(ProtocolType.ACP)
        
        assert len(acp_agents) == 1
        assert acp_agents[0].agent_id == "acp-agent"
    
    async def test_get_agents_by_capability(self, discovery_service):
        """Test getting agents by capability"""
        from orchestrator.models import AgentRegistryEntry
        
        greeting_cap = AgentCapability(name="greeting", description="Greeting capability")
        math_cap = AgentCapability(name="math", description="Math capability")
        
        agent1 = DiscoveredAgent(
            agent_id="agent1",
            name="Agent 1",
            protocol=ProtocolType.ACP,
            endpoint="http://test:8000",
            capabilities=[greeting_cap, math_cap]
        )
        
        agent2 = DiscoveredAgent(
            agent_id="agent2",
            name="Agent 2", 
            protocol=ProtocolType.A2A,
            endpoint="http://test:8001",
            capabilities=[math_cap]
        )
        
        discovery_service.agent_registry = {
            "agent1": AgentRegistryEntry(agent=agent1),
            "agent2": AgentRegistryEntry(agent=agent2)
        }
        
        math_agents = await discovery_service.get_agents_by_capability("math")
        
        assert len(math_agents) == 2
        
        greeting_agents = await discovery_service.get_agents_by_capability("greeting")
        
        assert len(greeting_agents) == 1
        assert greeting_agents[0].agent_id == "agent1"
    
    async def test_cleanup_registry(self, discovery_service):
        """Test cleanup of old/failed agents"""
        from orchestrator.models import AgentRegistryEntry
        
        # Create old agent (should be removed)
        old_agent = DiscoveredAgent(
            agent_id="old-agent",
            name="Old Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://test:8000",
            capabilities=[]
        )
        old_entry = AgentRegistryEntry(agent=old_agent)
        old_entry.last_seen = datetime.utcnow() - timedelta(hours=2)
        
        # Create failed agent (should be removed)
        failed_agent = DiscoveredAgent(
            agent_id="failed-agent",
            name="Failed Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://test:8001",
            capabilities=[]
        )
        failed_entry = AgentRegistryEntry(agent=failed_agent)
        for _ in range(6):  # Exceed default max failures
            failed_entry.mark_failure()
        
        # Create healthy agent (should be kept)
        healthy_agent = DiscoveredAgent(
            agent_id="healthy-agent",
            name="Healthy Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://test:8002",
            capabilities=[]
        )
        healthy_entry = AgentRegistryEntry(agent=healthy_agent)
        
        discovery_service.agent_registry = {
            "old-agent": old_entry,
            "failed-agent": failed_entry,
            "healthy-agent": healthy_entry
        }
        
        discovery_service._cleanup_registry()
        
        # Only healthy agent should remain
        assert len(discovery_service.agent_registry) == 1
        assert "healthy-agent" in discovery_service.agent_registry
    
    def test_get_registry_stats(self, discovery_service):
        """Test getting registry statistics"""
        from orchestrator.models import AgentRegistryEntry
        
        # Create agents with different statuses
        agents = [
            DiscoveredAgent(
                agent_id="healthy-acp",
                name="Healthy ACP",
                protocol=ProtocolType.ACP,
                endpoint="http://test:8000",
                capabilities=[],
                status=AgentStatus.HEALTHY
            ),
            DiscoveredAgent(
                agent_id="degraded-a2a",
                name="Degraded A2A",
                protocol=ProtocolType.A2A,
                endpoint="http://test:8001",
                capabilities=[],
                status=AgentStatus.DEGRADED
            ),
            DiscoveredAgent(
                agent_id="unhealthy-acp",
                name="Unhealthy ACP",
                protocol=ProtocolType.ACP,
                endpoint="http://test:8002",
                capabilities=[],
                status=AgentStatus.UNHEALTHY
            )
        ]
        
        discovery_service.agent_registry = {
            agent.agent_id: AgentRegistryEntry(agent=agent)
            for agent in agents
        }
        
        stats = discovery_service.get_registry_stats()
        
        assert stats["total_agents"] == 3
        assert stats["healthy_agents"] == 1
        assert stats["degraded_agents"] == 1
        assert stats["unhealthy_agents"] == 1
        assert stats["by_protocol"]["acp"] == 2
        assert stats["by_protocol"]["a2a"] == 1
    
    async def test_mark_agent_request(self, discovery_service):
        """Test marking agent request"""
        from orchestrator.models import AgentRegistryEntry
        
        agent = DiscoveredAgent(
            agent_id="test-agent",
            name="Test Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://test:8000",
            capabilities=[]
        )
        
        entry = AgentRegistryEntry(agent=agent)
        discovery_service.agent_registry["test-agent"] = entry
        
        await discovery_service.mark_agent_request("test-agent")
        
        assert entry.request_count == 1
        assert entry.last_request is not None
    
    async def test_is_healthy(self, discovery_service, mock_docker_client):
        """Test health check of discovery service"""
        # Service not running
        assert await discovery_service.is_healthy() is False
        
        # Service running with Docker client
        discovery_service._running = True
        discovery_service.docker_client = mock_docker_client
        assert await discovery_service.is_healthy() is True
        
        # Service running without Docker client
        discovery_service.docker_client = None
        assert await discovery_service.is_healthy() is True  # Still healthy, just limited