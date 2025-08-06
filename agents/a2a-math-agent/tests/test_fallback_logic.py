#!/usr/bin/env python3
"""
Tests for LLM fallback logic and configuration scenarios
"""

import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from a2a.types import Message, TextPart

from a2a_math_agent import MathAgent, LLMService, LLMProvider


class TestFallbackLogic:
    """Test fallback logic between LLM and deterministic calculations."""
    
    @pytest.fixture
    def agent(self):
        """Create agent for testing."""
        return MathAgent()
    
    @pytest.mark.asyncio
    async def test_fallback_when_no_llm_configured(self, agent):
        """Test fallback when no LLM is configured."""
        # Ensure no LLM is configured
        agent.llm_service.is_llm_available = Mock(return_value=False)
        
        message = Message(
            message_id="test_fallback_1",
            role="user",
            parts=[TextPart(text="What is 5 + 3?")]
        )
        result = await agent._process_message(message)
        
        assert "🧮 Calc:" in result
        assert "5.0 + 3.0 = 8.0" in result
    
    @pytest.mark.asyncio
    async def test_fallback_on_llm_api_error(self, agent):
        """Test fallback when LLM API call fails."""
        # Mock LLM as available but failing
        agent.llm_service.is_llm_available = Mock(return_value=True)
        agent.llm_service.get_provider_status = Mock(return_value={
            'preferred_provider': 'openai',
            'available_providers': ['openai']
        })
        agent.llm_service.generate_response = AsyncMock(side_effect=Exception("API rate limit"))
        
        message = Message(
            message_id="test_fallback_2",
            role="user",
            parts=[TextPart(text="5 + 3")]
        )
        result = await agent._process_message(message)
        
        assert "🧮 Calc:" in result
        assert "5.0 + 3.0 = 8.0" in result
    
    @pytest.mark.asyncio
    async def test_fallback_on_llm_timeout(self, agent):
        """Test fallback when LLM times out."""
        agent.llm_service.is_llm_available = Mock(return_value=True)
        agent.llm_service.get_provider_status = Mock(return_value={
            'preferred_provider': 'openai',
            'available_providers': ['openai']
        })
        agent.llm_service.generate_response = AsyncMock(side_effect=TimeoutError("Request timeout"))
        
        message = Message(
            message_id="test_fallback_3",
            role="user",
            parts=[TextPart(text="sqrt(25)")]
        )
        result = await agent._process_message(message)
        
        assert "🧮 Calc:" in result
        assert "√25.0 = 5.0" in result
    
    @pytest.mark.asyncio
    async def test_llm_success_no_fallback(self, agent):
        """Test that successful LLM calls don't trigger fallback."""
        agent.llm_service.is_llm_available = Mock(return_value=True)
        agent.llm_service.get_provider_status = Mock(return_value={
            'preferred_provider': 'openai',  
            'available_providers': ['openai']
        })
        agent.llm_service.generate_response = AsyncMock(return_value="The derivative of x² is 2x")
        
        message = Message(
            message_id="test_fallback_4",
            role="user",
            parts=[TextPart(text="What is the derivative of x²?")]
        )
        result = await agent._process_message(message)
        
        assert "🤖 LLM:" in result
        assert "The derivative of x² is 2x" in result
        assert "🧮 Calc:" not in result
    
    @pytest.mark.asyncio
    async def test_fallback_preserves_original_query(self, agent):
        """Test that fallback preserves the original query context."""
        agent.llm_service.is_llm_available = Mock(return_value=True)
        agent.llm_service.generate_response = AsyncMock(side_effect=Exception("Network error"))
        
        message = Message(
            message_id="test_fallback_5",
            role="user",
            parts=[TextPart(text="Calculate 12 * 8 please")]
        )
        result = await agent._process_message(message)
        
        assert "🧮 Calc:" in result
        assert "12.0 * 8.0 = 96.0" in result
    
    @pytest.mark.asyncio
    async def test_fallback_with_complex_expression(self, agent):
        """Test fallback handles complex expressions appropriately."""
        agent.llm_service.is_llm_available = Mock(return_value=True)
        agent.llm_service.generate_response = AsyncMock(side_effect=Exception("Model unavailable"))
        
        # Complex expression that deterministic parser can't handle
        message = Message(
            message_id="test_fallback_6",
            role="user",
            parts=[TextPart(text="Solve the integral of x^2 dx")]
        )
        result = await agent._process_message(message)
        
        assert "🧮 Calc:" in result
        assert "I can help with basic math operations" in result
    
    @pytest.mark.asyncio
    async def test_multiple_fallback_scenarios(self, agent):
        """Test multiple different fallback scenarios."""
        test_cases = [
            ("API key invalid", Exception("Invalid API key")),
            ("Service unavailable", Exception("Service temporarily unavailable")),
            ("Rate limited", Exception("Rate limit exceeded")),
            ("Network error", ConnectionError("Network unreachable")),
            ("Timeout", TimeoutError("Request timed out"))
        ]
        
        agent.llm_service.is_llm_available = Mock(return_value=True)
        agent.llm_service.get_provider_status = Mock(return_value={
            'preferred_provider': 'openai',
            'available_providers': ['openai']
        })
        
        for error_desc, error in test_cases:
            agent.llm_service.generate_response = AsyncMock(side_effect=error)
            
            message = Message(
                message_id=f"test_fallback_multi_{error_desc.replace(' ', '_')}",
                role="user",
                parts=[TextPart(text="7 + 5")]
            )
            result = await agent._process_message(message)
            
            assert "🧮 Calc:" in result, f"Fallback failed for {error_desc}"
            assert "7.0 + 5.0 = 12.0" in result, f"Wrong calculation for {error_desc}"


class TestConfigurationScenarios:
    """Test different configuration scenarios."""
    
    def test_no_environment_variables(self):
        """Test behavior with no LLM environment variables."""
        # Clear all LLM-related environment variables
        llm_env_vars = [
            'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GEMINI_API_KEY',
            'LLM_PROVIDER', 'OPENAI_MODEL', 'ANTHROPIC_MODEL', 'GEMINI_MODEL'
        ]
        
        with patch.dict(os.environ, {}, clear=True):
            for var in llm_env_vars:
                os.environ.pop(var, None)
            
            service = LLMService()
            assert not service.is_llm_available()
            
            status = service.get_provider_status()
            assert status['preferred_provider'] == 'none'
            assert len(status['available_providers']) == 0
            assert not status['openai_configured']
            assert not status['anthropic_configured']
            assert not status['gemini_configured']
    
    def test_openai_only_configuration(self):
        """Test configuration with only OpenAI."""
        with patch('a2a_math_agent.llm_service.OPENAI_AVAILABLE', True), \
             patch('a2a_math_agent.llm_service.ANTHROPIC_AVAILABLE', False), \
             patch('a2a_math_agent.llm_service.GEMINI_AVAILABLE', False), \
             patch.dict(os.environ, {
                 'OPENAI_API_KEY': 'test-openai-key',
                 'LLM_PROVIDER': 'openai'
             }, clear=True):
            
            service = LLMService()
            assert service.is_llm_available()
            
            status = service.get_provider_status()
            assert status['preferred_provider'] == 'openai'
            assert status['available_providers'] == ['openai']
            assert status['openai_configured']
            assert not status['anthropic_configured']
            assert not status['gemini_configured']
    
    def test_multiple_providers_configuration(self):
        """Test configuration with multiple providers."""
        with patch('a2a_math_agent.llm_service.OPENAI_AVAILABLE', True), \
             patch('a2a_math_agent.llm_service.ANTHROPIC_AVAILABLE', True), \
             patch('a2a_math_agent.llm_service.GEMINI_AVAILABLE', True), \
             patch.dict(os.environ, {
                 'OPENAI_API_KEY': 'test-openai-key',
                 'ANTHROPIC_API_KEY': 'test-anthropic-key',
                 'GEMINI_API_KEY': 'test-gemini-key',
                 'LLM_PROVIDER': 'anthropic'
             }, clear=True):
            
            service = LLMService()
            assert service.is_llm_available()
            
            status = service.get_provider_status()
            assert status['preferred_provider'] == 'anthropic'
            assert set(status['available_providers']) == {'openai', 'anthropic', 'gemini'}
            assert status['openai_configured']
            assert status['anthropic_configured']
            assert status['gemini_configured']
    
    def test_invalid_provider_preference(self):
        """Test behavior with invalid provider preference."""
        with patch('a2a_math_agent.llm_service.OPENAI_AVAILABLE', True), \
             patch.dict(os.environ, {
                 'OPENAI_API_KEY': 'test-key',
                 'LLM_PROVIDER': 'invalid_provider'
             }, clear=True):
            
            # Invalid provider should raise ValueError during initialization
            with pytest.raises(ValueError, match="'invalid_provider' is not a valid LLMProvider"):
                service = LLMService()
    
    def test_missing_api_key_with_provider_set(self):
        """Test behavior when provider is set but API key is missing."""
        with patch.dict(os.environ, {
             'LLM_PROVIDER': 'openai'
             # No OPENAI_API_KEY
         }, clear=True):
            
            service = LLMService()
            assert not service.is_llm_available()
            
            status = service.get_provider_status()
            assert status['preferred_provider'] == 'openai'
            assert len(status['available_providers']) == 0
            assert not status['openai_configured']
    
    def test_custom_model_configuration(self):
        """Test custom model configuration."""
        with patch('a2a_math_agent.llm_service.OPENAI_AVAILABLE', True), \
             patch.dict(os.environ, {
                 'OPENAI_API_KEY': 'test-key',
                 'OPENAI_MODEL': 'gpt-4',
                 'LLM_MAX_TOKENS': '300',
                 'LLM_TEMPERATURE': '0.7'
             }, clear=True):
            
            service = LLMService()
            
            assert service.config.openai_model == 'gpt-4'
            assert service.config.max_tokens == 300
            assert service.config.temperature == 0.7
    
    @pytest.mark.asyncio
    async def test_environment_changes_during_runtime(self):
        """Test that environment changes during runtime don't affect initialized service."""
        with patch('a2a_math_agent.llm_service.OPENAI_AVAILABLE', True), \
             patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}, clear=True):
            
            service = LLMService()
            assert service.is_llm_available()
            
            # Change environment after initialization
            os.environ.pop('OPENAI_API_KEY', None)
            
            # Service should still report as available (uses config from initialization)
            assert service.is_llm_available()
    
    def test_library_not_available(self):
        """Test behavior when LLM libraries are not available."""
        with patch('a2a_math_agent.llm_service.OPENAI_AVAILABLE', False), \
             patch('a2a_math_agent.llm_service.ANTHROPIC_AVAILABLE', False), \
             patch('a2a_math_agent.llm_service.GEMINI_AVAILABLE', False), \
             patch.dict(os.environ, {
                 'OPENAI_API_KEY': 'test-key',
                 'ANTHROPIC_API_KEY': 'test-key',
                 'GEMINI_API_KEY': 'test-key'
             }):
            
            service = LLMService()
            assert not service.is_llm_available()
            
            status = service.get_provider_status()
            assert len(status['available_providers']) == 0
            assert not status['openai_configured']
            assert not status['anthropic_configured']
            assert not status['gemini_configured']