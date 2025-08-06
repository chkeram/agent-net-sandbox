"""Additional tests for discovery service to increase coverage."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from orchestrator.discovery import UnifiedDiscoveryService
from orchestrator.models import (
    DiscoveredAgent, AgentCapability, ProtocolType, AgentStatus, AgentRegistryEntry
)


class TestDiscoveryServiceLifecycle:
    """Test discovery service lifecycle and advanced features."""

    @pytest.fixture
    def discovery_service(self):
        """Create discovery service with mocked settings."""
        with patch('orchestrator.discovery.get_settings') as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.discovery_interval_seconds = 30
            mock_get_settings.return_value = mock_settings
            return UnifiedDiscoveryService()

    @pytest.mark.asyncio
    async def test_discovery_service_start_stop(self, discovery_service):
        """Test discovery service start and stop lifecycle."""
        
        # Mock refresh to avoid actual HTTP calls
        discovery_service.refresh = AsyncMock()
        
        # Start the service
        await discovery_service.start()
        
        assert discovery_service._running is True
        assert discovery_service._discovery_task is not None
        
        # Stop the service
        await discovery_service.stop()
        
        assert discovery_service._running is False
        
        # Verify refresh was called during startup
        discovery_service.refresh.assert_called()

    @pytest.mark.asyncio
    async def test_discovery_loop_with_errors(self, discovery_service):
        """Test discovery loop handles errors gracefully."""
        
        # Mock refresh to raise an error first, then succeed
        call_count = 0
        async def mock_refresh():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Discovery error")
            # Second call succeeds
            
        discovery_service.refresh = mock_refresh
        discovery_service.settings.discovery_interval_seconds = 0.001  # Very short interval
        
        # Start discovery loop
        discovery_service._running = True
        
        # Let it run for a short time
        task = asyncio.create_task(discovery_service._discovery_loop())
        await asyncio.sleep(0.01)  # Let it run a couple iterations
        
        # Stop the loop
        discovery_service._running = False
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Should have attempted refresh multiple times despite errors
        assert call_count >= 2

    @pytest.mark.asyncio
    async def test_agent_registry_update_logic(self, discovery_service):
        """Test agent registry update logic with health checks."""
        
        # Create a test agent
        test_agent = DiscoveredAgent(
            agent_id="test-agent",
            name="Test Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://test:8000",
            capabilities=[],
            status=AgentStatus.HEALTHY
        )
        
        # Mock strategy health check
        with patch('orchestrator.discovery.get_discovery_strategy') as mock_get_strategy:
            mock_strategy = AsyncMock()
            mock_strategy.health_check.return_value = AgentStatus.HEALTHY
            mock_get_strategy.return_value = mock_strategy
            
            # Update registry with the agent
            await discovery_service._update_registry([test_agent])
            
            # Verify agent was added to registry
            assert "test-agent" in discovery_service.agent_registry
            entry = discovery_service.agent_registry["test-agent"]
            assert entry.agent.agent_id == "test-agent"
            assert entry.consecutive_failures == 0

    @pytest.mark.asyncio
    async def test_agent_registry_failure_handling(self, discovery_service):
        """Test agent registry handles health check failures."""
        
        # Create a test agent
        test_agent = DiscoveredAgent(
            agent_id="failing-agent",
            name="Failing Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://failing:8000",
            capabilities=[],
            status=AgentStatus.UNKNOWN
        )
        
        # Mock strategy to fail health checks
        with patch('orchestrator.discovery.get_discovery_strategy') as mock_get_strategy:
            mock_strategy = AsyncMock()
            mock_strategy.health_check.side_effect = Exception("Health check failed")
            mock_get_strategy.return_value = mock_strategy
            
            # Update registry with the agent
            await discovery_service._update_registry([test_agent])
            
            # Verify agent was added but marked as failed
            assert "failing-agent" in discovery_service.agent_registry
            entry = discovery_service.agent_registry["failing-agent"]
            assert entry.consecutive_failures == 1
            assert entry.agent.status == AgentStatus.UNKNOWN

    def test_agent_registry_cleanup_max_failures(self, discovery_service):
        """Test registry cleanup removes agents with too many failures."""
        
        # Create agent with many failures
        failing_agent = DiscoveredAgent(
            agent_id="failed-agent",
            name="Failed Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://failed:8000",
            capabilities=[]
        )
        
        entry = AgentRegistryEntry(agent=failing_agent)
        entry.consecutive_failures = 10  # Exceed max failures
        
        discovery_service.agent_registry = {"failed-agent": entry}
        
        # Run cleanup
        discovery_service._cleanup_registry()
        
        # Agent should be removed
        assert "failed-agent" not in discovery_service.agent_registry

    def test_agent_registry_cleanup_old_agents(self, discovery_service):
        """Test registry cleanup removes very old agents."""
        
        # Create agent with old timestamp
        old_agent = DiscoveredAgent(
            agent_id="old-agent",
            name="Old Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://old:8000",
            capabilities=[]
        )
        
        entry = AgentRegistryEntry(agent=old_agent)
        entry.last_seen = datetime.utcnow() - timedelta(hours=2)  # Very old
        
        discovery_service.agent_registry = {"old-agent": entry}
        
        # Run cleanup
        discovery_service._cleanup_registry()
        
        # Old agent should be removed
        assert "old-agent" not in discovery_service.agent_registry

    def test_agent_registry_cleanup_keeps_recent(self, discovery_service):
        """Test registry cleanup keeps recent healthy agents."""
        
        # Create recent healthy agent
        recent_agent = DiscoveredAgent(
            agent_id="recent-agent",
            name="Recent Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://recent:8000",
            capabilities=[],
            status=AgentStatus.HEALTHY
        )
        
        entry = AgentRegistryEntry(agent=recent_agent)
        entry.last_seen = datetime.utcnow() - timedelta(minutes=5)  # Recent
        entry.consecutive_failures = 0  # No failures
        
        discovery_service.agent_registry = {"recent-agent": entry}
        
        # Run cleanup
        discovery_service._cleanup_registry()
        
        # Recent agent should be kept
        assert "recent-agent" in discovery_service.agent_registry

    @pytest.mark.asyncio
    async def test_get_agent_by_id(self, discovery_service):
        """Test getting agent by ID."""
        
        # Create test agent
        test_agent = DiscoveredAgent(
            agent_id="test-agent",
            name="Test Agent",
            protocol=ProtocolType.A2A,
            endpoint="http://test:8002",
            capabilities=[]
        )
        
        entry = AgentRegistryEntry(agent=test_agent)
        discovery_service.agent_registry = {"test-agent": entry}
        
        # Test getting existing agent
        found_agent = await discovery_service.get_agent_by_id("test-agent")
        assert found_agent is not None
        assert found_agent.agent_id == "test-agent"
        
        # Test getting non-existing agent
        not_found = await discovery_service.get_agent_by_id("non-existent")
        assert not_found is None

    @pytest.mark.asyncio
    async def test_get_agents_by_protocol(self, discovery_service):
        """Test getting agents by protocol type."""
        
        # Create agents with different protocols
        acp_agent = DiscoveredAgent(
            agent_id="acp-agent",
            name="ACP Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://acp:8000",
            capabilities=[]
        )
        
        a2a_agent = DiscoveredAgent(
            agent_id="a2a-agent",
            name="A2A Agent",
            protocol=ProtocolType.A2A,
            endpoint="http://a2a:8002",
            capabilities=[]
        )
        
        discovery_service.agent_registry = {
            "acp-agent": AgentRegistryEntry(agent=acp_agent),
            "a2a-agent": AgentRegistryEntry(agent=a2a_agent)
        }
        
        # Test getting ACP agents
        acp_agents = await discovery_service.get_agents_by_protocol(ProtocolType.ACP)
        assert len(acp_agents) == 1
        assert acp_agents[0].agent_id == "acp-agent"
        
        # Test getting A2A agents
        a2a_agents = await discovery_service.get_agents_by_protocol(ProtocolType.A2A)
        assert len(a2a_agents) == 1
        assert a2a_agents[0].agent_id == "a2a-agent"
        
        # Test getting MCP agents (should be empty)
        mcp_agents = await discovery_service.get_agents_by_protocol(ProtocolType.MCP)
        assert len(mcp_agents) == 0

    @pytest.mark.asyncio
    async def test_mark_agent_request(self, discovery_service):
        """Test marking agent requests."""
        
        # Create test agent
        test_agent = DiscoveredAgent(
            agent_id="test-agent",
            name="Test Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://test:8000",
            capabilities=[]
        )
        
        entry = AgentRegistryEntry(agent=test_agent)
        discovery_service.agent_registry = {"test-agent": entry}
        
        # Mark request
        await discovery_service.mark_agent_request("test-agent")
        
        # Verify request was marked
        assert entry.request_count == 1
        assert entry.last_request is not None
        
        # Mark another request
        await discovery_service.mark_agent_request("test-agent")
        assert entry.request_count == 2

    @pytest.mark.asyncio
    async def test_mark_agent_request_nonexistent(self, discovery_service):
        """Test marking request for non-existent agent."""
        
        # Should not raise error for non-existent agent
        await discovery_service.mark_agent_request("non-existent")
        
        # Registry should still be empty
        assert len(discovery_service.agent_registry) == 0

    def test_registry_stats_comprehensive(self, discovery_service):
        """Test comprehensive registry statistics."""
        
        # Create agents with various statuses and protocols
        agents = [
            DiscoveredAgent(
                agent_id="healthy-acp",
                name="Healthy ACP",
                protocol=ProtocolType.ACP,
                endpoint="http://acp1:8000",
                capabilities=[],
                status=AgentStatus.HEALTHY
            ),
            DiscoveredAgent(
                agent_id="healthy-a2a",
                name="Healthy A2A",
                protocol=ProtocolType.A2A,
                endpoint="http://a2a1:8002",
                capabilities=[],
                status=AgentStatus.HEALTHY
            ),
            DiscoveredAgent(
                agent_id="degraded-acp",
                name="Degraded ACP",
                protocol=ProtocolType.ACP,
                endpoint="http://acp2:8000",
                capabilities=[],
                status=AgentStatus.DEGRADED
            ),
            DiscoveredAgent(
                agent_id="unhealthy-mcp",
                name="Unhealthy MCP",
                protocol=ProtocolType.MCP,
                endpoint="http://mcp:8001",
                capabilities=[],
                status=AgentStatus.UNHEALTHY
            )
        ]
        
        discovery_service.agent_registry = {
            agent.agent_id: AgentRegistryEntry(agent=agent)
            for agent in agents
        }
        
        stats = discovery_service.get_registry_stats()
        
        assert stats["total_agents"] == 4
        assert stats["healthy_agents"] == 2
        assert stats["degraded_agents"] == 1
        assert stats["unhealthy_agents"] == 1
        assert stats["by_protocol"]["acp"] == 2
        assert stats["by_protocol"]["a2a"] == 1
        assert stats["by_protocol"]["mcp"] == 1

    @pytest.mark.asyncio
    async def test_discovery_refresh_error_handling(self, discovery_service):
        """Test discovery refresh handles errors gracefully."""
        
        # Mock _discover_agents_http to raise an error
        discovery_service._discover_agents_http = AsyncMock(side_effect=Exception("Discovery failed"))
        
        # Should not raise exception
        await discovery_service.refresh()
        
        # Registry should remain empty
        assert len(discovery_service.agent_registry) == 0