"""Tests for configuration management"""

import pytest
import os
from pydantic import ValidationError

from orchestrator.config import Settings, get_settings, get_settings_for_testing


class TestSettings:
    """Test Settings class"""
    
    def test_default_settings(self):
        """Test default settings creation"""
        settings = get_settings_for_testing(
            llm_provider="openai",
            openai_api_key="test-key"
        )
        
        assert settings.app_name == "Multi-Protocol Agent Orchestrator"
        assert settings.app_version == "0.1.0"
        assert settings.host == "0.0.0.0"
        assert settings.port == 8004
        assert settings.llm_provider.value == "openai"
        assert settings.default_model_temperature == 0.7
        assert settings.discovery_interval_seconds == 30  # Default value
        assert settings.max_retries == 3
    
    def test_environment_variable_override(self):
        """Test that environment variables override defaults"""
        settings = get_settings_for_testing(
            app_name="Test Orchestrator",
            port=9000,
            debug=True,
            llm_provider="openai",
            default_model_temperature=0.5
        )
        
        assert settings.app_name == "Test Orchestrator"
        assert settings.port == 9000
        assert settings.debug is True
        assert settings.llm_provider == "openai"
        assert settings.default_model_temperature == 0.5
    
    def test_openai_configuration(self):
        """Test OpenAI configuration handling"""
        settings = get_settings_for_testing(
            openai_api_key="test-key",
            llm_provider="openai"
        )
        
        assert settings.has_openai_config is True
        assert settings.has_anthropic_config is False
        
        config = settings.get_openai_config()
        assert config["api_key"] == "test-key"
        assert config["model"] == "gpt-4o"
        assert config["temperature"] == 0.7
        assert config["max_tokens"] == 4096
    
    def test_anthropic_configuration(self):
        """Test Anthropic configuration handling"""
        settings = get_settings_for_testing(
            anthropic_api_key="test-key",
            llm_provider="anthropic"
        )
        
        assert settings.has_anthropic_config is True
        assert settings.has_openai_config is False
        
        config = settings.get_anthropic_config()
        assert config["api_key"] == "test-key"
        assert config["model"] == "claude-3-5-sonnet-20240620"
        assert config["temperature"] == 0.7
        assert config["max_tokens"] == 4096
    
    def test_anthropic_provider_configuration(self):
        """Test configuration with Anthropic provider"""
        settings = get_settings_for_testing(
            anthropic_api_key="anthropic-key",
            llm_provider="anthropic"
        )
        
        assert settings.has_openai_config is False
        assert settings.has_anthropic_config is True
    
    def test_validation_errors(self):
        """Test configuration validation errors"""
        
        # Invalid temperature
        with pytest.raises(ValueError, match="Temperature must be between 0.0 and 2.0"):
            get_settings_for_testing(
                llm_provider="openai",
                openai_api_key="test-key",
                default_model_temperature=3.0
            )
        
        # Invalid discovery interval
        with pytest.raises(ValueError, match="Discovery interval must be at least 10 seconds"):
            get_settings_for_testing(
                llm_provider="openai", 
                openai_api_key="test-key",
                discovery_interval_seconds=5
            )
        
        # Negative retries
        with pytest.raises(ValueError, match="Max retries cannot be negative"):
            get_settings_for_testing(
                llm_provider="openai",
                openai_api_key="test-key",
                max_retries=-1
            )
    
    def test_production_validation(self):
        """Test production environment validation"""
        
        # Missing OpenAI key in production
        with pytest.raises(ValueError, match="OpenAI API key is required for OpenAI provider"):
            get_settings_for_testing(
                environment="production",
                llm_provider="openai",
                openai_api_key=None
            )
        
        # Missing Anthropic key in production
        with pytest.raises(ValueError, match="Anthropic API key is required for Anthropic provider"):
            get_settings_for_testing(
                environment="production",
                llm_provider="anthropic",
                anthropic_api_key=None
            )
        
    
    def test_http_discovery_settings(self):
        """Test HTTP-based discovery configuration"""
        settings = get_settings_for_testing(
            llm_provider="openai",
            openai_api_key="test-key",
            discovery_interval_seconds=60,
            discovery_timeout_seconds=10
        )
        
        assert settings.discovery_interval_seconds == 60
        assert settings.discovery_timeout_seconds == 10
    
    def test_provider_config_errors(self):
        """Test provider configuration error handling"""
        # Test with OpenAI provider but no key
        settings_openai = get_settings_for_testing(
            openai_api_key=None,
            llm_provider="openai"
        )
        with pytest.raises(ValueError, match="OpenAI configuration not available"):
            settings_openai.get_openai_config()
        
        # Test with Anthropic provider but no key
        settings_anthropic = get_settings_for_testing(
            anthropic_api_key=None,
            llm_provider="anthropic"
        )
        with pytest.raises(ValueError, match="Anthropic configuration not available"):
            settings_anthropic.get_anthropic_config()
    
    def test_settings_caching(self):
        """Test settings caching behavior"""
        # For production get_settings, we need to mock environment
        import os
        old_key = os.environ.get('OPENAI_API_KEY')
        os.environ['OPENAI_API_KEY'] = 'test-key'
        try:
            # get_settings should return the same instance
            settings1 = get_settings()
            settings2 = get_settings()
            assert settings1 is settings2
        finally:
            if old_key is not None:
                os.environ['OPENAI_API_KEY'] = old_key
            else:
                os.environ.pop('OPENAI_API_KEY', None)
        
        # get_settings_for_testing should return new instances
        test_settings1 = get_settings_for_testing(
            llm_provider="openai",
            openai_api_key="test-key",
            debug=True
        )
        test_settings2 = get_settings_for_testing(
            llm_provider="openai", 
            openai_api_key="test-key",
            debug=True
        )
        assert test_settings1 is not test_settings2
    
    def test_enum_validation(self):
        """Test enum field validation"""
        # Valid values
        settings = get_settings_for_testing(
            llm_provider="openai",
            openai_api_key="test-key",
            environment="production",
            log_level="DEBUG"
        )
        assert settings.llm_provider.value == "openai"
        assert settings.environment == "production"
        assert settings.log_level == "DEBUG"
        
        # Invalid values should raise ValidationError
        with pytest.raises(ValidationError):
            get_settings_for_testing(
                llm_provider="invalid_provider",
                openai_api_key="test-key"
            )
        
        with pytest.raises(ValidationError):
            get_settings_for_testing(
                llm_provider="openai",
                openai_api_key="test-key",
                environment="invalid_env"
            )
        
        with pytest.raises(ValidationError):
            get_settings_for_testing(
                llm_provider="openai",
                openai_api_key="test-key",
                log_level="INVALID_LEVEL"
            )
    
    def test_cors_configuration(self):
        """Test CORS configuration"""
        settings = get_settings_for_testing(
            llm_provider="openai",
            openai_api_key="test-key",
            cors_origins=["http://localhost:3000", "https://example.com"],
            cors_methods=["GET", "POST"],
            cors_headers=["Content-Type", "Authorization"]
        )
        
        assert "http://localhost:3000" in settings.cors_origins
        assert "https://example.com" in settings.cors_origins
        assert "GET" in settings.cors_methods
        assert "POST" in settings.cors_methods
        assert "Content-Type" in settings.cors_headers
        assert "Authorization" in settings.cors_headers