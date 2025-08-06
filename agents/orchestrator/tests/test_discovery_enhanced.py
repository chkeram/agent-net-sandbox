"""Tests for enhanced discovery service features including tag-based capability matching."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import aiohttp

from orchestrator.discovery import UnifiedDiscoveryService
from orchestrator.models import (
    DiscoveredAgent, AgentCapability, ProtocolType, AgentStatus
)


class TestEnhancedDiscoveryService:
    """Test enhanced discovery service features."""

    @pytest.fixture
    def discovery_service(self):
        """Create discovery service with mocked settings."""
        with patch('orchestrator.discovery.get_settings') as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.discovery_interval_seconds = 30
            mock_get_settings.return_value = mock_settings
            return UnifiedDiscoveryService()

    def test_a2a_capabilities_from_agent_card_data(self):
        """Test conversion of A2A skills to capabilities with tags."""
        
        # Test data that would come from A2A agent card
        skills_data = [
            {
                "id": "basic_arithmetic",
                "name": "Basic Arithmetic", 
                "description": "Perform basic arithmetic operations",
                "tags": ["math", "arithmetic", "calculation"]
            },
            {
                "id": "advanced_math",
                "name": "Advanced Mathematics",
                "description": "Solve complex mathematical problems", 
                "tags": ["math", "algebra", "calculus"]
            }
        ]
        
        # Convert skills to capabilities (same logic as in discovery.py)
        capabilities = []
        for skill in skills_data:
            capabilities.append(AgentCapability(
                name=skill.get('name', skill.get('id', 'unknown')),
                description=skill.get('description', f"A2A skill: {skill.get('name', 'unknown')}"),
                tags=skill.get('tags', [])
            ))
        
        # Verify capabilities were created correctly
        assert len(capabilities) == 2
        
        # Check first capability
        basic_cap = capabilities[0]
        assert basic_cap.name == "basic arithmetic"  # name gets lowercased
        assert basic_cap.description == "Perform basic arithmetic operations"
        assert "math" in basic_cap.tags
        assert "arithmetic" in basic_cap.tags
        assert "calculation" in basic_cap.tags
        
        # Check second capability  
        advanced_cap = capabilities[1]
        assert advanced_cap.name == "advanced mathematics"  # name gets lowercased
        assert advanced_cap.description == "Solve complex mathematical problems"
        assert "math" in advanced_cap.tags
        assert "algebra" in advanced_cap.tags
        assert "calculus" in advanced_cap.tags

    def test_acp_capabilities_from_capabilities_data(self):
        """Test conversion of ACP capabilities data to AgentCapability objects."""
        
        # Test data that would come from ACP /capabilities endpoint
        capabilities_data = [
            {
                "name": "greeting",
                "description": "Generate personalized greetings",
                "tags": ["greeting", "hello", "welcome"]
            },
            "translation"  # String capability
        ]
        
        # Convert capabilities (same logic as in discovery.py)
        capabilities = []
        for cap in capabilities_data:
            if isinstance(cap, str):
                capabilities.append(AgentCapability(
                    name=cap,
                    description=f"Agent capability: {cap}"
                ))
            elif isinstance(cap, dict):
                capabilities.append(AgentCapability(**cap))
        
        # Verify capabilities were created correctly
        assert len(capabilities) == 2
        
        # Check parsed capability with tags
        greeting_cap = next(cap for cap in capabilities if cap.name == "greeting")
        assert greeting_cap.description == "Generate personalized greetings"
        assert "greeting" in greeting_cap.tags
        assert "hello" in greeting_cap.tags  
        assert "welcome" in greeting_cap.tags
        
        # Check string capability conversion
        translation_cap = next(cap for cap in capabilities if cap.name == "translation")
        assert translation_cap.description == "Agent capability: translation"
        assert translation_cap.tags == []  # String caps have no tags

    def test_tag_based_capability_matching(self):
        """Test that agents can be found by capability tags."""
        
        # Create agent with capabilities that have tags
        agent = DiscoveredAgent(
            agent_id="test-math-agent",
            name="Test Math Agent",
            protocol=ProtocolType.A2A,
            endpoint="http://test:8002",
            capabilities=[
                AgentCapability(
                    name="basic arithmetic",
                    description="Basic math operations",
                    tags=["math", "arithmetic", "calculation", "numbers"]
                ),
                AgentCapability(
                    name="advanced mathematics",
                    description="Complex math problems",
                    tags=["math", "algebra", "calculus", "advanced"]
                )
            ],
            status=AgentStatus.HEALTHY
        )
        
        # Test exact name matches
        assert agent.has_capability("basic arithmetic")
        assert agent.has_capability("advanced mathematics")
        
        # Test tag-based matches
        assert agent.has_capability("math")
        assert agent.has_capability("arithmetic")
        assert agent.has_capability("calculation")
        assert agent.has_capability("numbers")
        assert agent.has_capability("algebra")
        assert agent.has_capability("calculus")
        assert agent.has_capability("advanced")
        
        # Test case insensitive matching
        assert agent.has_capability("MATH")
        assert agent.has_capability("Math")
        assert agent.has_capability("ARITHMETIC")
        assert agent.has_capability("Calculus")
        
        # Test non-matching capabilities
        assert not agent.has_capability("greeting")
        assert not agent.has_capability("translation")
        assert not agent.has_capability("nonexistent")

    @pytest.mark.asyncio
    async def test_get_agents_by_capability_with_tags(self, discovery_service):
        """Test getting agents by capability using tag matching."""
        
        # Create test agents with different capabilities and tags
        math_agent = DiscoveredAgent(
            agent_id="math-agent",
            name="Math Agent",
            protocol=ProtocolType.A2A,
            endpoint="http://math:8002",
            capabilities=[
                AgentCapability(
                    name="arithmetic operations",
                    description="Basic arithmetic",
                    tags=["math", "arithmetic", "calculation"]
                )
            ],
            status=AgentStatus.HEALTHY
        )
        
        greeting_agent = DiscoveredAgent(
            agent_id="greeting-agent",
            name="Greeting Agent", 
            protocol=ProtocolType.ACP,
            endpoint="http://greeting:8000",
            capabilities=[
                AgentCapability(
                    name="generate greetings",
                    description="Create personalized greetings",
                    tags=["greeting", "hello", "welcome"]
                )
            ],
            status=AgentStatus.HEALTHY
        )
        
        # Add agents to discovery service registry
        from orchestrator.models import AgentRegistryEntry
        discovery_service.agent_registry = {
            "math-agent": AgentRegistryEntry(agent=math_agent),
            "greeting-agent": AgentRegistryEntry(agent=greeting_agent)
        }
        
        # Test finding agents by tag
        math_agents = await discovery_service.get_agents_by_capability("math")
        assert len(math_agents) == 1
        assert math_agents[0].agent_id == "math-agent"
        
        greeting_agents = await discovery_service.get_agents_by_capability("greeting")
        assert len(greeting_agents) == 1
        assert greeting_agents[0].agent_id == "greeting-agent"
        
        # Test case insensitive matching
        math_agents_caps = await discovery_service.get_agents_by_capability("MATH")
        assert len(math_agents_caps) == 1
        assert math_agents_caps[0].agent_id == "math-agent"
        
        # Test non-matching capability
        no_agents = await discovery_service.get_agents_by_capability("nonexistent")
        assert len(no_agents) == 0

    def test_endpoint_fallback_logic(self):
        """Test the endpoint fallback logic used in HTTP discovery."""
        
        # Test the agent key generation logic that prevents duplicate discoveries
        known_endpoints = [
            {"url": "http://acp-hello-world-agent:8000", "protocol": "acp", "name": "hello-world"},
            {"url": "http://localhost:8000", "protocol": "acp", "name": "hello-world"},  # fallback
            {"url": "http://a2a-math-agent:8002", "protocol": "a2a", "name": "math"},
            {"url": "http://localhost:8002", "protocol": "a2a", "name": "math"},  # fallback
        ]
        
        agents_tried = set()
        discovered_agents = []
        
        # Simulate discovery loop logic
        for endpoint in known_endpoints:
            agent_key = f"{endpoint['protocol']}-{endpoint['name']}"
            
            # Skip if we already successfully discovered this agent
            if agent_key in agents_tried:
                continue
                
            # Simulate successful discovery for localhost endpoints
            if "localhost" in endpoint['url']:
                mock_agent = DiscoveredAgent(
                    agent_id=agent_key,
                    name=endpoint['name'],
                    protocol=ProtocolType(endpoint['protocol']),
                    endpoint=endpoint['url'],
                    capabilities=[],
                    status=AgentStatus.HEALTHY
                )
                discovered_agents.append(mock_agent)
                agents_tried.add(agent_key)
        
        # Should discover exactly 2 agents (one ACP, one A2A) via localhost fallback
        assert len(discovered_agents) == 2
        assert len(agents_tried) == 2
        assert "acp-hello-world" in agents_tried
        assert "a2a-math" in agents_tried

    @pytest.mark.asyncio
    async def test_discovery_error_handling(self, discovery_service):
        """Test discovery service error handling."""
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session_class.return_value.__aexit__.return_value = None
            
            # Mock connection error
            mock_session.get.side_effect = aiohttp.ClientConnectionError("Connection failed")
            
            # Run HTTP discovery - should handle errors gracefully
            agents = await discovery_service._discover_agents_http()
            
            # Should return empty list without crashing
            assert agents == []

    def test_registry_cleanup_logic(self, discovery_service):
        """Test agent registry cleanup removes stale agents."""
        
        from orchestrator.models import AgentRegistryEntry
        from datetime import timedelta
        
        # Create agents with different ages
        old_time = datetime.utcnow() - timedelta(hours=2)  # Very old
        recent_time = datetime.utcnow() - timedelta(minutes=5)  # Recent
        
        old_agent = DiscoveredAgent(
            agent_id="old-agent",
            name="Old Agent", 
            protocol=ProtocolType.ACP,
            endpoint="http://old:8000",
            capabilities=[]
        )
        
        recent_agent = DiscoveredAgent(
            agent_id="recent-agent",
            name="Recent Agent",
            protocol=ProtocolType.A2A, 
            endpoint="http://recent:8002",
            capabilities=[]
        )
        
        old_entry = AgentRegistryEntry(agent=old_agent)
        old_entry.last_seen = old_time
        
        recent_entry = AgentRegistryEntry(agent=recent_agent)
        recent_entry.last_seen = recent_time
        
        discovery_service.agent_registry = {
            "old-agent": old_entry,
            "recent-agent": recent_entry
        }
        
        # Run cleanup
        discovery_service._cleanup_registry()
        
        # Old agent should be removed, recent agent should remain
        assert "old-agent" not in discovery_service.agent_registry
        assert "recent-agent" in discovery_service.agent_registry
        assert len(discovery_service.agent_registry) == 1

    @pytest.mark.asyncio
    async def test_discovery_service_health_check(self, discovery_service):
        """Test discovery service health check functionality."""
        
        # Service not running yet
        discovery_service._running = False
        assert not await discovery_service.is_healthy()
        
        # Service running with agents
        discovery_service._running = True
        from orchestrator.models import AgentRegistryEntry
        
        test_agent = DiscoveredAgent(
            agent_id="test-agent",
            name="Test Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://test:8000",
            capabilities=[],
            status=AgentStatus.HEALTHY
        )
        
        discovery_service.agent_registry = {
            "test-agent": AgentRegistryEntry(agent=test_agent)
        }
        
        assert await discovery_service.is_healthy()

    def test_registry_stats_calculation(self, discovery_service):
        """Test registry statistics calculation."""
        
        from orchestrator.models import AgentRegistryEntry
        
        # Create agents with different statuses
        healthy_agent = DiscoveredAgent(
            agent_id="healthy-agent",
            name="Healthy Agent",
            protocol=ProtocolType.A2A,
            endpoint="http://healthy:8002",
            capabilities=[],
            status=AgentStatus.HEALTHY
        )
        
        degraded_agent = DiscoveredAgent(
            agent_id="degraded-agent", 
            name="Degraded Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://degraded:8000",
            capabilities=[],
            status=AgentStatus.DEGRADED
        )
        
        unhealthy_agent = DiscoveredAgent(
            agent_id="unhealthy-agent",
            name="Unhealthy Agent", 
            protocol=ProtocolType.A2A,
            endpoint="http://unhealthy:8002",
            capabilities=[],
            status=AgentStatus.UNHEALTHY
        )
        
        discovery_service.agent_registry = {
            "healthy-agent": AgentRegistryEntry(agent=healthy_agent),
            "degraded-agent": AgentRegistryEntry(agent=degraded_agent), 
            "unhealthy-agent": AgentRegistryEntry(agent=unhealthy_agent)
        }
        
        stats = discovery_service.get_registry_stats()
        
        assert stats["total_agents"] == 3
        assert stats["healthy_agents"] == 1
        assert stats["degraded_agents"] == 1
        assert stats["unhealthy_agents"] == 1
        assert stats["by_protocol"]["a2a"] == 2
        assert stats["by_protocol"]["acp"] == 1