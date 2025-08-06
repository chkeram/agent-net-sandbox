"""Tests for the orchestrator agent functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from orchestrator.agent import OrchestratorAgent, OrchestratorContext
from orchestrator.models import (
    RoutingRequest, DiscoveredAgent, AgentCapability, 
    ProtocolType, AgentStatus, LLMProvider, RoutingDecision
)


class TestOrchestratorAgent:
    """Test orchestrator agent functionality."""

    @pytest.fixture
    def mock_discovery_service(self):
        """Create mock discovery service."""
        service = AsyncMock()
        service.get_healthy_agents.return_value = []
        service.get_agents_by_capability.return_value = []
        service.mark_agent_request.return_value = None
        service.is_healthy.return_value = True
        return service

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        settings = MagicMock()
        settings.llm_provider = LLMProvider.OPENAI
        settings.openai_api_key = "test-openai-key"
        settings.anthropic_api_key = None
        return settings

    def test_orchestrator_context_creation(self, mock_discovery_service):
        """Test OrchestratorContext creation."""
        request = RoutingRequest(query="Test query")
        context = OrchestratorContext(mock_discovery_service, request)
        
        assert context.discovery_service == mock_discovery_service
        assert context.request == request
        assert context.available_agents == []
        assert isinstance(context.routing_start_time, datetime)

    def test_orchestrator_context_available_agents_property(self, mock_discovery_service):
        """Test OrchestratorContext available_agents property."""
        request = RoutingRequest(query="Test query")
        context = OrchestratorContext(mock_discovery_service, request)
        
        # available_agents should start as empty list
        assert context.available_agents == []
        assert isinstance(context.available_agents, list)
        
        # Can add agents to the list
        test_agent = DiscoveredAgent(
            agent_id="test-agent",
            name="Test Agent", 
            protocol=ProtocolType.ACP,
            endpoint="http://test:8000",
            capabilities=[]
        )
        
        context.available_agents.append(test_agent)
        assert len(context.available_agents) == 1
        assert context.available_agents[0].agent_id == "test-agent"

    def test_orchestrator_context_properties(self, mock_discovery_service):
        """Test OrchestratorContext properties."""
        request = RoutingRequest(query="Test query with context")
        context = OrchestratorContext(mock_discovery_service, request)
        
        # Test that all properties are accessible
        assert context.discovery_service == mock_discovery_service
        assert context.request.query == "Test query with context"
        assert isinstance(context.routing_start_time, datetime)
        assert isinstance(context.available_agents, list)

    def test_orchestrator_context_timing(self, mock_discovery_service):
        """Test OrchestratorContext timing functionality."""
        import time
        
        request = RoutingRequest(query="Timing test query")
        start_time = datetime.utcnow()
        
        # Small delay to ensure different timestamps
        time.sleep(0.001)
        
        context = OrchestratorContext(mock_discovery_service, request)
        
        # routing_start_time should be after our start_time
        assert context.routing_start_time > start_time

    def test_orchestrator_agent_initialization_openai(self, mock_discovery_service, mock_settings):
        """Test OrchestratorAgent initialization with OpenAI."""
        with patch('orchestrator.agent.get_settings', return_value=mock_settings), \
             patch('orchestrator.agent.infer_model') as mock_infer_model, \
             patch('orchestrator.agent.Agent') as mock_agent_class:
            
            mock_model = MagicMock()
            mock_infer_model.return_value = mock_model
            mock_agent_instance = MagicMock()
            mock_agent_class.return_value = mock_agent_instance
            
            orchestrator = OrchestratorAgent(mock_discovery_service)
            
            assert orchestrator.discovery_service == mock_discovery_service
            assert orchestrator.model == mock_model
            assert orchestrator.agent == mock_agent_instance
            
            mock_infer_model.assert_called_once_with('openai:gpt-4o')

    def test_orchestrator_agent_initialization_anthropic(self, mock_discovery_service):
        """Test OrchestratorAgent initialization with Anthropic."""
        mock_settings = MagicMock()
        mock_settings.llm_provider = LLMProvider.ANTHROPIC
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = "test-anthropic-key"
        
        with patch('orchestrator.agent.get_settings', return_value=mock_settings), \
             patch('orchestrator.agent.infer_model') as mock_infer_model, \
             patch('orchestrator.agent.Agent') as mock_agent_class:
            
            mock_model = MagicMock()
            mock_infer_model.return_value = mock_model
            mock_agent_instance = MagicMock()
            mock_agent_class.return_value = mock_agent_instance
            
            orchestrator = OrchestratorAgent(mock_discovery_service)
            
            mock_infer_model.assert_called_once_with('anthropic:claude-3-5-sonnet-20241022')

    def test_orchestrator_agent_missing_api_key(self, mock_discovery_service):
        """Test OrchestratorAgent initialization fails with missing API key."""
        mock_settings = MagicMock()
        mock_settings.llm_provider = LLMProvider.OPENAI
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        
        with patch('orchestrator.agent.get_settings', return_value=mock_settings):
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                OrchestratorAgent(mock_discovery_service)

    def test_orchestrator_agent_missing_anthropic_key(self, mock_discovery_service):
        """Test OrchestratorAgent initialization fails with missing Anthropic key."""
        mock_settings = MagicMock()
        mock_settings.llm_provider = LLMProvider.ANTHROPIC
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        
        with patch('orchestrator.agent.get_settings', return_value=mock_settings):
            with pytest.raises(ValueError, match="Anthropic API key is required"):
                OrchestratorAgent(mock_discovery_service)

    def test_get_system_prompt(self, mock_discovery_service, mock_settings):
        """Test system prompt generation."""
        with patch('orchestrator.agent.get_settings', return_value=mock_settings), \
             patch('orchestrator.agent.infer_model') as mock_infer_model, \
             patch('orchestrator.agent.Agent'):
            
            mock_model = MagicMock()
            mock_infer_model.return_value = mock_model
            
            orchestrator = OrchestratorAgent(mock_discovery_service)
            prompt = orchestrator._get_system_prompt()
            
            # Check for key concepts in the prompt
            assert "agent orchestrator" in prompt
            assert "routing decisions" in prompt
            assert "capabilities" in prompt
            assert "ACP, A2A, MCP" in prompt
            assert "confidence" in prompt

    @pytest.mark.asyncio
    async def test_route_request_success(self, mock_discovery_service, mock_settings):
        """Test successful request routing."""
        with patch('orchestrator.agent.get_settings', return_value=mock_settings), \
             patch('orchestrator.agent.infer_model') as mock_infer_model, \
             patch('orchestrator.agent.Agent') as mock_agent_class:
            
            mock_model = MagicMock()
            mock_infer_model.return_value = mock_model
            mock_agent_instance = AsyncMock()
            mock_agent_class.return_value = mock_agent_instance
            
            # Create test agent
            test_agent = DiscoveredAgent(
                agent_id="greeting-agent",
                name="Greeting Agent",
                protocol=ProtocolType.ACP,
                endpoint="http://greeting:8000",
                capabilities=[AgentCapability(name="greeting", description="Generate greetings")]
            )
            
            # Mock AI agent response
            mock_result = MagicMock()
            mock_result.data = RoutingDecision(
                request_id="test-request-123",
                selected_agent=test_agent,
                confidence=0.9,
                reasoning="This is a greeting request",
                alternative_agents=[]
            )
            mock_agent_instance.run.return_value = mock_result
            
            orchestrator = OrchestratorAgent(mock_discovery_service)
            request = RoutingRequest(query="Hello there!")
            
            decision = await orchestrator.route_request(request)
            
            assert decision.selected_agent.agent_id == "greeting-agent"
            assert decision.confidence == 0.9
            assert "greeting request" in decision.reasoning
            
            # Verify agent was marked as used
            mock_discovery_service.mark_agent_request.assert_called_once_with("greeting-agent")

    @pytest.mark.asyncio
    async def test_route_request_failure(self, mock_discovery_service, mock_settings):
        """Test request routing failure handling."""
        with patch('orchestrator.agent.get_settings', return_value=mock_settings), \
             patch('orchestrator.agent.infer_model') as mock_infer_model, \
             patch('orchestrator.agent.Agent') as mock_agent_class:
            
            mock_model = MagicMock()
            mock_infer_model.return_value = mock_model
            mock_agent_instance = AsyncMock()
            mock_agent_class.return_value = mock_agent_instance
            
            # Mock AI agent failure
            mock_agent_instance.run.side_effect = Exception("AI model unavailable")
            
            orchestrator = OrchestratorAgent(mock_discovery_service)
            request = RoutingRequest(query="Complex query")
            
            decision = await orchestrator.route_request(request)
            
            # Verify fallback response
            assert decision.selected_agent is None
            assert decision.confidence == 0.0
            assert "Routing failed due to error" in decision.reasoning

    @pytest.mark.asyncio
    async def test_execute_on_agent_acp(self, mock_discovery_service, mock_settings):
        """Test execution on ACP agent."""
        with patch('orchestrator.agent.get_settings', return_value=mock_settings), \
             patch('orchestrator.agent.infer_model'), \
             patch('orchestrator.agent.Agent'):
            
            orchestrator = OrchestratorAgent(mock_discovery_service)
            
            agent = DiscoveredAgent(
                agent_id="test-acp-agent",
                name="Test ACP Agent",
                protocol=ProtocolType.ACP,
                endpoint="http://test:8000",
                capabilities=[]
            )
            
            request = RoutingRequest(query="Test query")
            
            response_data = await orchestrator._execute_on_agent(agent, request)
            
            assert response_data["message"] == "Response from Test ACP Agent (ACP protocol)"
            assert response_data["query"] == "Test query"
            assert response_data["agent_id"] == "test-acp-agent"
            assert response_data["protocol"] == "acp"
            assert response_data["simulated"] is True

    @pytest.mark.asyncio
    async def test_execute_on_agent_a2a(self, mock_discovery_service, mock_settings):
        """Test execution on A2A agent."""
        with patch('orchestrator.agent.get_settings', return_value=mock_settings), \
             patch('orchestrator.agent.infer_model'), \
             patch('orchestrator.agent.Agent'), \
             patch('orchestrator.protocols.a2a_client.A2AProtocolClient') as mock_a2a_client:
            
            # Mock A2A client
            mock_client_instance = AsyncMock()
            mock_a2a_client.return_value = mock_client_instance
            mock_client_instance.send_query.return_value = {
                "text": "The result is 42",
                "message_id": "msg_123",
                "role": "agent"
            }
            
            orchestrator = OrchestratorAgent(mock_discovery_service)
            
            agent = DiscoveredAgent(
                agent_id="test-a2a-agent",
                name="Test A2A Agent",
                protocol=ProtocolType.A2A,
                endpoint="http://test:8002",
                capabilities=[]
            )
            
            request = RoutingRequest(query="What is 6 * 7?")
            
            response_data = await orchestrator._execute_on_agent(agent, request)
            
            assert "The result is 42" in response_data["message"]
            assert response_data["query"] == "What is 6 * 7?"
            assert response_data["agent_id"] == "test-a2a-agent"
            assert response_data["protocol"] == "a2a"
            assert response_data["simulated"] is False
            
            mock_client_instance.send_query.assert_called_once_with("http://test:8002", "What is 6 * 7?")

    @pytest.mark.asyncio
    async def test_process_request_success(self, mock_discovery_service, mock_settings):
        """Test complete request processing."""
        with patch('orchestrator.agent.get_settings', return_value=mock_settings), \
             patch('orchestrator.agent.infer_model'), \
             patch('orchestrator.agent.Agent'):
            
            orchestrator = OrchestratorAgent(mock_discovery_service)
            
            # Mock successful routing
            test_agent = DiscoveredAgent(
                agent_id="test-agent",
                name="Test Agent",
                protocol=ProtocolType.ACP,
                endpoint="http://test:8000",
                capabilities=[],
                status=AgentStatus.HEALTHY  # Make sure agent is healthy
            )
            
            routing_decision = RoutingDecision(
                request_id="test-request-123",
                selected_agent=test_agent,
                confidence=0.8,
                reasoning="Good match",
                alternative_agents=[]
            )
            
            # Mock that the agent is available in healthy agents list
            mock_discovery_service.get_healthy_agents.return_value = [test_agent]
            
            orchestrator.route_request = AsyncMock(return_value=routing_decision)
            
            request = RoutingRequest(query="Test query")
            response = await orchestrator.process_request(request)
            
            assert response.success is True
            assert response.agent_id == "test-agent"
            assert response.error is None
            assert "routing_decision" in response.metadata

    @pytest.mark.asyncio
    async def test_process_request_no_agent_selected(self, mock_discovery_service, mock_settings):
        """Test request processing when no agent is selected."""
        with patch('orchestrator.agent.get_settings', return_value=mock_settings), \
             patch('orchestrator.agent.infer_model'), \
             patch('orchestrator.agent.Agent'):
            
            orchestrator = OrchestratorAgent(mock_discovery_service)
            
            # Mock no agent selected
            routing_decision = RoutingDecision(
                request_id="test-request-123",
                selected_agent=None,
                confidence=0.0,
                reasoning="No suitable agent found",
                alternative_agents=[]
            )
            
            orchestrator.route_request = AsyncMock(return_value=routing_decision)
            
            request = RoutingRequest(query="Unsupported query")
            response = await orchestrator.process_request(request)
            
            assert response.success is False
            assert response.agent_id == "none"
            assert "No suitable agent found" in response.error

    @pytest.mark.asyncio
    async def test_health_check(self, mock_discovery_service, mock_settings):
        """Test orchestrator health check."""
        with patch('orchestrator.agent.get_settings', return_value=mock_settings), \
             patch('orchestrator.agent.infer_model'), \
             patch('orchestrator.agent.Agent'):
            
            orchestrator = OrchestratorAgent(mock_discovery_service)
            
            # Mock discovery service health
            mock_discovery_service.is_healthy.return_value = True
            mock_discovery_service.get_healthy_agents.return_value = [MagicMock(), MagicMock()]
            
            health = await orchestrator.health_check()
            
            assert health["orchestrator_healthy"] is True
            assert health["discovery_service_healthy"] is True
            assert health["available_agents"] == 2
            assert health["llm_provider"] == LLMProvider.OPENAI.value
            assert "metrics" in health

    def test_get_metrics(self, mock_discovery_service, mock_settings):
        """Test metrics retrieval."""
        with patch('orchestrator.agent.get_settings', return_value=mock_settings), \
             patch('orchestrator.agent.infer_model'), \
             patch('orchestrator.agent.Agent'):
            
            orchestrator = OrchestratorAgent(mock_discovery_service)
            
            # Modify some metrics
            orchestrator.metrics.total_requests = 5
            orchestrator.metrics.successful_requests = 4
            orchestrator.metrics.failed_requests = 1
            
            metrics = orchestrator.get_metrics()
            
            assert metrics.total_requests == 5
            assert metrics.successful_requests == 4
            assert metrics.failed_requests == 1
            assert metrics.success_rate == 80.0