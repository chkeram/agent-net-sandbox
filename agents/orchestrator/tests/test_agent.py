"""Tests for orchestrator agent"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from orchestrator.agent import OrchestratorAgent, OrchestratorContext
from orchestrator.models import (
    RoutingRequest, DiscoveredAgent, AgentCapability, 
    ProtocolType, AgentStatus, LLMProvider
)
from orchestrator.discovery import UnifiedDiscoveryService

pytestmark = pytest.mark.asyncio


class TestOrchestratorAgent:
    """Test orchestrator agent functionality"""
    
    @pytest.fixture
    def mock_discovery_service(self):
        """Create mock discovery service"""
        service = AsyncMock(spec=UnifiedDiscoveryService)
        
        # Mock healthy agents
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
        
        service.get_healthy_agents.return_value = test_agents
        service.get_agents_by_capability.return_value = []
        service.get_agents_by_protocol.return_value = []
        service.mark_agent_request.return_value = None
        service.is_healthy.return_value = True
        
        return service
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing"""
        settings = MagicMock()
        settings.llm_provider = LLMProvider.OPENAI
        settings.openai_api_key = "test-openai-key"
        settings.anthropic_api_key = None
        return settings
    
    @pytest.fixture
    def orchestrator_agent(self, mock_discovery_service, mock_settings):
        """Create orchestrator agent with mocked dependencies"""
        with patch('orchestrator.agent.get_settings', return_value=mock_settings), \
             patch('orchestrator.agent.infer_model') as mock_infer_model:
            
            # Mock the inferred model
            mock_model = MagicMock()
            mock_infer_model.return_value = mock_model
            
            agent = OrchestratorAgent(mock_discovery_service)
            
            # Mock the Pydantic AI agent
            agent.agent = AsyncMock()
            
            return agent
    
    def test_orchestrator_context_creation(self, mock_discovery_service):
        """Test OrchestratorContext creation"""
        request = RoutingRequest(query="Hello world")
        context = OrchestratorContext(mock_discovery_service, request)
        
        assert context.discovery_service == mock_discovery_service
        assert context.request == request
        assert context.available_agents == []
        assert isinstance(context.routing_start_time, datetime)
    
    def test_model_creation_openai(self, mock_discovery_service):
        """Test OpenAI model creation"""
        mock_settings = MagicMock()
        mock_settings.llm_provider = LLMProvider.OPENAI
        mock_settings.openai_api_key = "test-key"
        mock_settings.anthropic_api_key = None
        
        with patch('orchestrator.agent.get_settings', return_value=mock_settings), \
             patch('orchestrator.agent.infer_model') as mock_infer_model:
            
            mock_model = MagicMock()
            mock_infer_model.return_value = mock_model
            
            agent = OrchestratorAgent(mock_discovery_service)
            
            mock_infer_model.assert_called_once_with('openai:gpt-4o')
            assert agent.model == mock_model
    
    def test_model_creation_anthropic(self, mock_discovery_service):
        """Test Anthropic model creation"""
        mock_settings = MagicMock()
        mock_settings.llm_provider = LLMProvider.ANTHROPIC
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = "test-anthropic-key"
        
        with patch('orchestrator.agent.get_settings', return_value=mock_settings), \
             patch('orchestrator.agent.infer_model') as mock_infer_model:
            
            mock_model = MagicMock()
            mock_infer_model.return_value = mock_model
            
            agent = OrchestratorAgent(mock_discovery_service)
            
            mock_infer_model.assert_called_once_with('anthropic:claude-3-5-sonnet-20241022')
            assert agent.model == mock_model
    
    
    def test_model_creation_missing_api_key(self, mock_discovery_service):
        """Test error when API key is missing"""
        mock_settings = MagicMock()
        mock_settings.llm_provider = LLMProvider.OPENAI
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        
        with patch('orchestrator.agent.get_settings', return_value=mock_settings):
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                OrchestratorAgent(mock_discovery_service)
    
    @pytest.mark.asyncio
    async def test_route_request_success(self, orchestrator_agent, mock_discovery_service):
        """Test successful request routing"""
        from orchestrator.models import RoutingDecision
        
        request = RoutingRequest(query="Say hello to me")
        
        # Mock the AI agent response
        mock_result = MagicMock()
        mock_agent = DiscoveredAgent(
            agent_id="acp-greeting-agent",
            name="Greeting Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://greeting:8000",
            capabilities=[AgentCapability(name="greeting", description="Generate greetings")],
            status=AgentStatus.HEALTHY
        )
        mock_result.data = RoutingDecision(
            request_id="test-request-123",
            selected_agent=mock_agent,
            confidence=0.95,
            reasoning="This is a greeting request, perfect for the greeting agent",
            alternative_agents=[]
        )
        
        orchestrator_agent.agent.run.return_value = mock_result
        
        # Execute routing
        decision = await orchestrator_agent.route_request(request)
        
        # Verify results
        assert decision.selected_agent.agent_id == "acp-greeting-agent"
        assert decision.confidence == 0.95
        assert "greeting request" in decision.reasoning
        
        # Verify agent was marked as used
        mock_discovery_service.mark_agent_request.assert_called_once_with("acp-greeting-agent")
    
    @pytest.mark.asyncio
    async def test_route_request_failure(self, orchestrator_agent):
        """Test request routing failure handling"""
        request = RoutingRequest(query="Complex query")
        
        # Mock AI agent failure
        orchestrator_agent.agent.run.side_effect = Exception("AI model unavailable")
        
        # Execute routing
        decision = await orchestrator_agent.route_request(request)
        
        # Verify fallback response
        assert decision.selected_agent is None
        assert decision.confidence == 0.0
        assert "Routing failed due to error" in decision.reasoning
    
    @pytest.mark.asyncio
    async def test_execute_on_agent(self, orchestrator_agent):
        """Test agent execution simulation"""
        agent = DiscoveredAgent(
            agent_id="test-agent",
            name="Test Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://test:8000",
            capabilities=[AgentCapability(name="test", description="Test capability")]
        )
        
        request = RoutingRequest(query="Test query")
        
        # Execute on agent
        response_data = await orchestrator_agent._execute_on_agent(agent, request)
        
        # Verify response structure
        assert response_data["message"] == "Response from Test Agent"
        assert response_data["query"] == "Test query"
        assert response_data["agent_id"] == "test-agent"
        assert response_data["protocol"] == "acp"
        assert response_data["simulated"] is True
        assert "timestamp" in response_data
    
    @pytest.mark.asyncio
    async def test_process_request_success(self, orchestrator_agent, mock_discovery_service):
        """Test complete request processing"""
        from orchestrator.models import RoutingDecision
        
        request = RoutingRequest(query="Calculate 2+2")
        
        # Mock routing decision
        mock_agent = DiscoveredAgent(
            agent_id="a2a-math-agent",
            name="Math Agent",
            protocol=ProtocolType.A2A,
            endpoint="http://math:8001",
            capabilities=[AgentCapability(name="calculate", description="Perform calculations")],
            status=AgentStatus.HEALTHY
        )
        routing_decision = RoutingDecision(
            request_id="test-request-123",
            selected_agent=mock_agent,
            confidence=0.9,
            reasoning="Math calculation request",
            alternative_agents=[]
        )
        
        # Mock orchestrator agent methods
        orchestrator_agent.route_request = AsyncMock(return_value=routing_decision)
        
        # Execute processing
        response = await orchestrator_agent.process_request(request)
        
        # Verify response
        assert response.success is True
        assert response.agent_id == "a2a-math-agent"
        assert response.error is None
        assert "routing_decision" in response.metadata
        assert response.metadata["agent_protocol"] == "a2a"
    
    @pytest.mark.asyncio
    async def test_process_request_no_agent_selected(self, orchestrator_agent):
        """Test request processing when no agent is selected"""
        from orchestrator.models import RoutingDecision
        
        request = RoutingRequest(query="Unsupported query")
        
        # Mock routing decision with no agent
        routing_decision = RoutingDecision(
            request_id="test-request-123",
            selected_agent=None,
            confidence=0.0,
            reasoning="No suitable agent found",
            alternative_agents=[]
        )
        
        orchestrator_agent.route_request = AsyncMock(return_value=routing_decision)
        
        # Execute processing
        response = await orchestrator_agent.process_request(request)
        
        # Verify error response
        assert response.success is False
        assert response.agent_id == "none"
        assert "No suitable agent found" in response.error
        assert response.metadata["reason"] == "no_agent_selected"
    
    @pytest.mark.asyncio
    async def test_process_request_agent_not_available(self, orchestrator_agent, mock_discovery_service):
        """Test request processing when selected agent is not available"""
        from orchestrator.models import RoutingDecision
        
        request = RoutingRequest(query="Test query")
        
        # Mock routing decision with non-existent agent  
        mock_agent = DiscoveredAgent(
            agent_id="non-existent-agent",
            name="Non-existent Agent",
            protocol=ProtocolType.ACP,
            endpoint="http://nonexistent:8000",
            capabilities=[],
            status=AgentStatus.UNHEALTHY
        )
        routing_decision = RoutingDecision(
            request_id="test-request-123",
            selected_agent=mock_agent,
            confidence=0.8,
            reasoning="Selected non-existent agent",
            alternative_agents=[]
        )
        
        orchestrator_agent.route_request = AsyncMock(return_value=routing_decision)
        
        # Execute processing
        response = await orchestrator_agent.process_request(request)
        
        # Verify error response
        assert response.success is False
        assert response.agent_id == "non-existent-agent"
        assert "is no longer available" in response.error
        assert response.metadata["reason"] == "agent_not_available"
    
    def test_get_metrics(self, orchestrator_agent):
        """Test metrics retrieval"""
        # Modify some metrics
        orchestrator_agent.metrics.total_requests = 10
        orchestrator_agent.metrics.successful_requests = 8
        orchestrator_agent.metrics.failed_requests = 2
        
        metrics = orchestrator_agent.get_metrics()
        
        assert metrics.total_requests == 10
        assert metrics.successful_requests == 8
        assert metrics.failed_requests == 2
    
    @pytest.mark.asyncio
    async def test_health_check(self, orchestrator_agent, mock_discovery_service):
        """Test orchestrator health check"""
        # Mock discovery service health
        mock_discovery_service.is_healthy.return_value = True
        mock_discovery_service.get_healthy_agents.return_value = [
            MagicMock(), MagicMock()  # 2 healthy agents
        ]
        
        health = await orchestrator_agent.health_check()
        
        assert health["orchestrator_healthy"] is True
        assert health["discovery_service_healthy"] is True
        assert health["available_agents"] == 2
        assert health["llm_provider"] == LLMProvider.OPENAI.value
        assert "metrics" in health
    
    def test_system_prompt_content(self, orchestrator_agent):
        """Test system prompt contains expected content"""
        prompt = orchestrator_agent._get_system_prompt()
        
        # Check for key concepts
        assert "agent orchestrator" in prompt
        assert "routing" in prompt
        assert "capabilities" in prompt
        assert "confidence scores" in prompt
        assert "ACP, A2A, MCP" in prompt