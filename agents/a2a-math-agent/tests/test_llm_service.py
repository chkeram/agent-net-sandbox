#!/usr/bin/env python3
"""
Unit tests for LLM Service
"""

import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from a2a_math_agent import LLMService, LLMConfig, LLMProvider


class TestLLMConfig:
    """Test LLM configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        # Clear environment to ensure we test actual defaults, not env values
        with patch.dict(os.environ, {}, clear=True):
            config = LLMConfig()
            assert config.preferred_provider == LLMProvider.NONE
            assert config.max_tokens == 150
            assert config.temperature == 0.1
            assert config.openai_model == "gpt-4o-mini"
            assert config.anthropic_model == "claude-3-haiku-20240307"
            assert config.gemini_model == "gemini-1.5-flash"  # Actual default from code
    
    def test_environment_override(self):
        """Test configuration from environment variables."""
        with patch.dict(os.environ, {
            'LLM_PROVIDER': 'openai',
            'LLM_MAX_TOKENS': '200',
            'LLM_TEMPERATURE': '0.5',
            'OPENAI_MODEL': 'gpt-4',
            'OPENAI_API_KEY': 'test-key'
        }):
            config = LLMConfig()
            assert config.preferred_provider == LLMProvider.OPENAI
            assert config.max_tokens == 200
            assert config.temperature == 0.5
            assert config.openai_model == "gpt-4"
            assert config.openai_api_key == "test-key"
    
    def test_provider_configuration_detection(self):
        """Test provider configuration detection."""
        # Mock the availability checks and clear environment
        with patch('a2a_math_agent.llm_service.OPENAI_AVAILABLE', True), \
             patch('a2a_math_agent.llm_service.ANTHROPIC_AVAILABLE', True), \
             patch('a2a_math_agent.llm_service.GEMINI_AVAILABLE', True), \
             patch.dict(os.environ, {}, clear=True):
            
            config = LLMConfig()
            
            # No API keys - should not be configured
            assert not config.is_provider_configured(LLMProvider.OPENAI)
            assert not config.is_provider_configured(LLMProvider.ANTHROPIC)
            assert not config.is_provider_configured(LLMProvider.GEMINI)
            
            # Set API keys
            config.openai_api_key = "test-openai-key"
            config.anthropic_api_key = "test-anthropic-key"
            config.gemini_api_key = "test-gemini-key"
            
            assert config.is_provider_configured(LLMProvider.OPENAI)
            assert config.is_provider_configured(LLMProvider.ANTHROPIC)
            assert config.is_provider_configured(LLMProvider.GEMINI)
    
    def test_get_available_providers(self):
        """Test getting list of available providers."""
        with patch('a2a_math_agent.llm_service.OPENAI_AVAILABLE', True), \
             patch('a2a_math_agent.llm_service.ANTHROPIC_AVAILABLE', False), \
             patch('a2a_math_agent.llm_service.GEMINI_AVAILABLE', True):
            
            config = LLMConfig()
            config.openai_api_key = "test-key"
            config.gemini_api_key = "test-key"
            
            available = config.get_available_providers()
            assert LLMProvider.OPENAI in available
            assert LLMProvider.ANTHROPIC not in available
            assert LLMProvider.GEMINI in available


class TestLLMService:
    """Test LLM service functionality."""
    
    def test_initialization_without_providers(self):
        """Test service initialization without LLM providers."""
        with patch('a2a_math_agent.llm_service.OPENAI_AVAILABLE', False), \
             patch('a2a_math_agent.llm_service.ANTHROPIC_AVAILABLE', False), \
             patch('a2a_math_agent.llm_service.GEMINI_AVAILABLE', False):
            
            service = LLMService()
            assert not service.is_llm_available()
            assert service.openai_client is None
            assert service.anthropic_client is None
            assert service.gemini_model is None
    
    def test_initialization_with_openai(self):
        """Test service initialization with OpenAI."""
        with patch('a2a_math_agent.llm_service.OPENAI_AVAILABLE', True), \
             patch('a2a_math_agent.llm_service.OpenAI') as mock_openai, \
             patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            
            service = LLMService()
            assert service.is_llm_available()
            mock_openai.assert_called_once_with(api_key='test-key')
    
    def test_initialization_with_anthropic(self):
        """Test service initialization with Anthropic."""
        with patch('a2a_math_agent.llm_service.ANTHROPIC_AVAILABLE', True), \
             patch('a2a_math_agent.llm_service.Anthropic') as mock_anthropic, \
             patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            
            service = LLMService()
            assert service.is_llm_available()
            mock_anthropic.assert_called_once_with(api_key='test-key')
    
    def test_initialization_with_gemini(self):
        """Test service initialization with Gemini."""
        with patch('a2a_math_agent.llm_service.GEMINI_AVAILABLE', True), \
             patch('a2a_math_agent.llm_service.genai') as mock_genai, \
             patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}):
            
            service = LLMService()
            assert service.is_llm_available()
            mock_genai.configure.assert_called_once_with(api_key='test-key')
            mock_genai.GenerativeModel.assert_called_once()
    
    def test_provider_status(self):
        """Test provider status reporting."""
        with patch('a2a_math_agent.llm_service.OPENAI_AVAILABLE', True), \
             patch('a2a_math_agent.llm_service.ANTHROPIC_AVAILABLE', False), \
             patch('a2a_math_agent.llm_service.GEMINI_AVAILABLE', False), \
             patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key', 'LLM_PROVIDER': 'openai'}, clear=True):
            
            service = LLMService()
            status = service.get_provider_status()
            
            assert status['preferred_provider'] == 'openai'
            assert 'openai' in status['available_providers']
            assert status['openai_configured'] is True
            assert status['anthropic_configured'] is False
            assert status['gemini_configured'] is False
            assert status['fallback_enabled'] is True
    
    @pytest.mark.asyncio
    async def test_openai_call_success(self):
        """Test successful OpenAI API call."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('a2a_math_agent.llm_service.OPENAI_AVAILABLE', True), \
             patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            
            service = LLMService()
            service.openai_client = mock_client
            
            result = await service._call_openai("Test prompt")
            assert result == "Test response"
            
            mock_client.chat.completions.create.assert_called_once()
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]['model'] == 'gpt-4o-mini'
            assert call_args[1]['max_tokens'] == 150
            assert call_args[1]['temperature'] == 0.1
    
    @pytest.mark.asyncio
    async def test_openai_call_failure(self):
        """Test OpenAI API call failure."""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        service = LLMService()
        service.openai_client = mock_client
        
        with pytest.raises(Exception, match="API Error"):
            await service._call_openai("Test prompt")
    
    @pytest.mark.asyncio
    async def test_anthropic_call_success(self):
        """Test successful Anthropic API call."""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Test response"
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        
        with patch('a2a_math_agent.llm_service.ANTHROPIC_AVAILABLE', True), \
             patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            
            service = LLMService()
            service.anthropic_client = mock_client
            
            result = await service._call_anthropic("Test prompt")
            assert result == "Test response"
            
            mock_client.messages.create.assert_called_once()
            call_args = mock_client.messages.create.call_args
            assert call_args[1]['model'] == 'claude-3-haiku-20240307'
            assert call_args[1]['max_tokens'] == 150
            assert call_args[1]['temperature'] == 0.1
    
    @pytest.mark.asyncio
    async def test_gemini_call_success(self):
        """Test successful Gemini API call."""
        mock_response = Mock()
        mock_response.text = "Test response"
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        
        service = LLMService()
        service.gemini_model = mock_model
        
        result = await service._call_gemini("Test prompt")
        assert result == "Test response"
        
        mock_model.generate_content.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_response_no_providers(self):
        """Test generate_response with no providers available."""
        service = LLMService()
        # Force no providers
        service.config.get_available_providers = Mock(return_value=[])
        
        with pytest.raises(ValueError, match="No LLM providers are configured"):
            await service.generate_response("Test prompt")
    
    @pytest.mark.asyncio
    async def test_generate_response_with_fallback(self):
        """Test generate_response with provider fallback."""
        # Mock a service with multiple providers where first fails
        service = LLMService()
        service.config.preferred_provider = LLMProvider.OPENAI
        service.config.get_available_providers = Mock(return_value=[LLMProvider.OPENAI, LLMProvider.ANTHROPIC])
        
        # First provider fails
        service._call_openai = AsyncMock(side_effect=Exception("OpenAI Error"))
        # Second provider succeeds
        service._call_anthropic = AsyncMock(return_value="Fallback response")
        
        result = await service.generate_response("Test prompt")
        assert result == "Fallback response"
        
        service._call_openai.assert_called_once()
        service._call_anthropic.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_response_all_providers_fail(self):
        """Test generate_response when all providers fail."""
        service = LLMService()
        service.config.preferred_provider = LLMProvider.OPENAI
        service.config.get_available_providers = Mock(return_value=[LLMProvider.OPENAI, LLMProvider.ANTHROPIC])
        
        # Both providers fail
        openai_error = Exception("OpenAI Error")
        service._call_openai = AsyncMock(side_effect=openai_error)
        service._call_anthropic = AsyncMock(side_effect=Exception("Anthropic Error"))
        
        with pytest.raises(Exception, match="OpenAI Error"):
            await service.generate_response("Test prompt")
    
    @pytest.mark.asyncio
    async def test_generate_response_specific_provider(self):
        """Test generate_response with specific provider override."""
        service = LLMService()
        service.config.preferred_provider = LLMProvider.OPENAI
        service.config.get_available_providers = Mock(return_value=[LLMProvider.OPENAI, LLMProvider.ANTHROPIC])
        
        service._call_anthropic = AsyncMock(return_value="Anthropic response")
        
        # Request specific provider
        result = await service.generate_response("Test prompt", LLMProvider.ANTHROPIC)
        assert result == "Anthropic response"
        
        service._call_anthropic.assert_called_once()
    
    def test_client_initialization_error_handling(self):
        """Test error handling during client initialization."""
        with patch('a2a_math_agent.llm_service.OPENAI_AVAILABLE', True), \
             patch('a2a_math_agent.llm_service.OpenAI', side_effect=Exception("Init error")), \
             patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            
            # Should not raise exception, just log error
            service = LLMService()
            assert service.openai_client is None