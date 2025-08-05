#!/usr/bin/env python3
"""
Integration tests for A2A Math Agent
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from a2a.types import Message, TextPart
from a2a.server.agent_execution.context import RequestContext

from a2a_math_agent import MathAgent, create_agent_card
from a2a_math_agent import LLMProvider


class TestMathAgent:
    """Test A2A Math Agent functionality."""
    
    @pytest.fixture
    def agent(self):
        """Create a test agent instance."""
        return MathAgent()
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock request context."""
        context = Mock(spec=RequestContext)
        context.send_message = AsyncMock()
        return context
    
    def test_agent_initialization(self, agent):
        """Test agent initialization."""
        assert agent.math_ops is not None
        assert agent.llm_service is not None
        assert hasattr(agent, 'logger')
    
    @pytest.mark.asyncio
    async def test_cancel_operation(self, agent, mock_context):
        """Test cancel operation."""
        # Should complete without error
        await agent.cancel(mock_context)
    
    def test_expression_evaluation_basic_arithmetic(self, agent):
        """Test basic arithmetic expression evaluation."""
        assert "5.0 + 3.0 = 8.0" in agent._evaluate_expression("5 + 3")
        assert "10.0 - 4.0 = 6.0" in agent._evaluate_expression("10 - 4")
        assert "6.0 * 7.0 = 42.0" in agent._evaluate_expression("6 * 7")
        assert "15.0 / 3.0 = 5.0" in agent._evaluate_expression("15 / 3")
    
    def test_expression_evaluation_advanced_operations(self, agent):
        """Test advanced mathematical operations."""
        assert "√16.0 = 4.0" in agent._evaluate_expression("sqrt(16)")
        assert "2.0^3.0 = 8.0" in agent._evaluate_expression("2^3")
        assert "3.0^2.0 = 9.0" in agent._evaluate_expression("3**2")
    
    def test_expression_evaluation_with_symbols(self, agent):
        """Test expressions with mathematical symbols."""
        assert "6.0 × 7.0 = 42.0" in agent._evaluate_expression("6 × 7")
        assert "15.0 ÷ 3.0 = 5.0" in agent._evaluate_expression("15 ÷ 3")
    
    def test_expression_evaluation_with_question_words(self, agent):
        """Test expressions with question words are cleaned."""
        result = agent._evaluate_expression("what is 5 + 3")
        assert "5.0 + 3.0 = 8.0" in result
        
        result = agent._evaluate_expression("calculate 10 - 4")
        assert "10.0 - 4.0 = 6.0" in result
    
    def test_expression_evaluation_invalid_format(self, agent):
        """Test invalid expression format."""
        result = agent._evaluate_expression("invalid expression")
        assert "I can help with basic math operations" in result
        
        result = agent._evaluate_expression("solve world hunger")
        assert "I can help with basic math operations" in result
    
    def test_expression_evaluation_division_by_zero(self, agent):
        """Test division by zero handling."""
        result = agent._evaluate_expression("10 / 0")
        assert "Division by zero is not allowed" in result
    
    def test_expression_evaluation_negative_sqrt(self, agent):
        """Test negative square root handling."""
        result = agent._evaluate_expression("sqrt(-4)")
        assert "Cannot calculate square root of negative number" in result
    
    def test_expression_evaluation_simple_number(self, agent):
        """Test simple number input."""
        result = agent._evaluate_expression("42")
        assert "The number is: 42" in result
        
        result = agent._evaluate_expression("3.14")
        assert "The number is: 3.14" in result
    
    @pytest.mark.asyncio
    async def test_process_message_deterministic_mode(self, agent, mock_context):
        """Test message processing in deterministic mode."""
        # Mock LLM as unavailable
        agent.llm_service.is_llm_available = Mock(return_value=False)
        
        # Create test message
        message = Message(
            message_id="test_msg_1",
            role="user",
            parts=[TextPart(text="5 + 3")]
        )
        
        result = await agent._process_message(message)
        
        assert "🧮 Calc:" in result
        assert "5.0 + 3.0 = 8.0" in result
    
    @pytest.mark.asyncio
    async def test_process_message_llm_mode_success(self, agent, mock_context):
        """Test message processing in LLM mode with success."""
        # Mock LLM as available and successful
        agent.llm_service.is_llm_available = Mock(return_value=True)
        agent.llm_service.get_provider_status = Mock(return_value={
            'preferred_provider': 'openai',
            'available_providers': ['openai']
        })
        agent.llm_service.generate_response = AsyncMock(return_value="The answer is 8")
        
        # Create test message
        message = Message(
            message_id="test_msg_2",
            role="user",
            parts=[TextPart(text="What is 5 + 3?")]
        )
        
        result = await agent._process_message(message)
        
        assert "🤖 LLM:" in result
        assert "The answer is 8" in result
        agent.llm_service.generate_response.assert_called_once_with("What is 5 + 3?")
    
    @pytest.mark.asyncio
    async def test_process_message_llm_mode_fallback(self, agent, mock_context):
        """Test message processing with LLM failure and fallback."""
        # Mock LLM as available but failing
        agent.llm_service.is_llm_available = Mock(return_value=True)
        agent.llm_service.get_provider_status = Mock(return_value={
            'preferred_provider': 'openai',
            'available_providers': ['openai']
        })
        agent.llm_service.generate_response = AsyncMock(side_effect=Exception("API Error"))
        
        # Create test message
        message = Message(
            message_id="test_msg_3",
            role="user",
            parts=[TextPart(text="5 + 3")]
        )
        
        result = await agent._process_message(message)
        
        assert "🧮 Calc:" in result
        assert "5.0 + 3.0 = 8.0" in result
    
    @pytest.mark.asyncio
    async def test_process_message_multiple_text_parts(self, agent, mock_context):
        """Test message processing with multiple text parts."""
        agent.llm_service.is_llm_available = Mock(return_value=False)
        
        # Create message with multiple parts
        message = Message(
            message_id="test_msg_4",
            role="user",
            parts=[
                TextPart(text="Calculate "),
                TextPart(text="5 + 3")
            ]
        )
        
        result = await agent._process_message(message)
        
        assert "🧮 Calc:" in result
        assert "5.0 + 3.0 = 8.0" in result
    
    @pytest.mark.asyncio
    async def test_execute_success(self, agent, mock_context):
        """Test successful execute method."""
        # Mock the request and message
        mock_request = Mock()
        mock_request.message = Message(
            message_id="test_msg_5",
            role="user",
            parts=[TextPart(text="5 + 3")]
        )
        mock_context.request = mock_request
        
        agent.llm_service.is_llm_available = Mock(return_value=False)
        
        await agent.execute(mock_context)
        
        # Verify send_message was called
        mock_context.send_message.assert_called_once()
        sent_message = mock_context.send_message.call_args[0][0]
        assert isinstance(sent_message, Message)
        assert len(sent_message.parts) == 1
        assert hasattr(sent_message.parts[0], 'root') and isinstance(sent_message.parts[0].root, TextPart)
        assert "🧮 Calc:" in sent_message.parts[0].root.text
    
    @pytest.mark.asyncio
    async def test_execute_error_handling(self, agent, mock_context):
        """Test execute method error handling."""
        # Mock the request to cause an error
        mock_context.request = Mock()
        mock_context.request.message = Mock()
        mock_context.request.message.parts = [Mock()]
        mock_context.request.message.parts[0].text = "test"
        # Make parts iteration fail
        mock_context.request.message.parts = Mock(side_effect=Exception("Test error"))
        
        await agent.execute(mock_context)
        
        # Verify error message was sent
        mock_context.send_message.assert_called_once()
        sent_message = mock_context.send_message.call_args[0][0]
        assert "Error:" in sent_message.parts[0].root.text


class TestAgentCard:
    """Test agent card creation."""
    
    def test_create_agent_card_without_llm(self):
        """Test agent card creation without LLM."""
        with patch('a2a_math_agent.math_agent.LLMService') as mock_llm_service:
            mock_service = Mock()
            mock_service.is_llm_available.return_value = False
            mock_service.get_provider_status.return_value = {
                'available_providers': []
            }
            mock_llm_service.return_value = mock_service
            
            card = create_agent_card()
            
            assert card.name == "A2A Math Operations Agent"
            assert "deterministic mathematical calculations" in card.description
            assert len(card.skills) == 2  # Basic + Advanced
            assert card.version == "0.1.0"
            assert card.default_input_modes == ["text"]
            assert card.default_output_modes == ["text"]
    
    def test_create_agent_card_with_llm(self):
        """Test agent card creation with LLM available."""
        with patch('a2a_math_agent.math_agent.LLMService') as mock_llm_service:
            mock_service = Mock()
            mock_service.is_llm_available.return_value = True
            mock_service.get_provider_status.return_value = {
                'available_providers': ['openai', 'anthropic']
            }
            mock_llm_service.return_value = mock_service
            
            card = create_agent_card()
            
            assert card.name == "A2A Math Operations Agent"
            assert "AI-powered problem solving" in card.description
            assert "openai, anthropic" in card.description
            assert len(card.skills) == 3  # Basic + Advanced + LLM
            
            # Check LLM skill
            llm_skill = next(skill for skill in card.skills if skill.id == "llm_math")
            assert llm_skill.name == "LLM-Powered Mathematics"
            assert "openai" in llm_skill.tags
            assert "anthropic" in llm_skill.tags
            assert len(llm_skill.examples) == 4
    
    def test_agent_card_skills_structure(self):
        """Test agent card skills have proper structure."""
        card = create_agent_card()
        
        for skill in card.skills:
            assert skill.id is not None
            assert skill.name is not None
            assert skill.description is not None
            assert isinstance(skill.tags, list)
            assert len(skill.tags) > 0
            if hasattr(skill, 'examples'):
                assert isinstance(skill.examples, list)
    
    def test_agent_card_required_fields(self):
        """Test agent card has all required fields."""
        card = create_agent_card()
        
        assert card.name is not None
        assert card.description is not None
        assert card.version is not None
        assert card.skills is not None
        assert card.capabilities is not None
        assert card.default_input_modes is not None
        assert card.default_output_modes is not None
        assert card.url is not None