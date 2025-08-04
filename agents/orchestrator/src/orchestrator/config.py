"""Configuration management for the Multi-Protocol Agent Orchestrator"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Literal, List
from functools import lru_cache
import os

from .models import LLMProvider


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application settings
    app_name: str = "Multi-Protocol Agent Orchestrator"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    
    # LLM Provider settings
    llm_provider: LLMProvider = LLMProvider.OPENAI
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    default_model_temperature: float = 0.7
    
    # OpenAI specific
    openai_model: str = "gpt-4o"
    openai_max_tokens: int = 4096
    openai_timeout: float = 30.0
    
    # Anthropic specific
    anthropic_model: str = "claude-3-5-sonnet-20240620"
    anthropic_max_tokens: int = 4096
    anthropic_timeout: float = 30.0
    
    # Discovery settings
    discovery_interval_seconds: int = 30
    discovery_timeout_seconds: int = 5
    docker_network: str = "agent-network"
    docker_socket_path: str = "/var/run/docker.sock"
    
    # Routing settings
    routing_timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    enable_fallback_routing: bool = True
    
    # Monitoring and metrics
    enable_metrics: bool = True
    metrics_port: int = 9090
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    structured_logging: bool = True
    
    # Security
    cors_origins: List[str] = ["*"]
    cors_methods: List[str] = ["GET", "POST", "PUT", "DELETE"]
    cors_headers: List[str] = ["*"]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_settings()
    
    def _validate_settings(self) -> None:
        """Validate settings and ensure required configurations are present"""
        
        # Validate LLM provider configuration
        if self.llm_provider in ["openai", "both"]:
            if not self.openai_api_key:
                if self.environment == "production":
                    raise ValueError("OpenAI API key is required in production")
                
        if self.llm_provider in ["anthropic", "both"]:
            if not self.anthropic_api_key:
                if self.environment == "production":
                    raise ValueError("Anthropic API key is required in production")
        
        # Validate LLM provider configuration
        if self.llm_provider == LLMProvider.OPENAI and not self.openai_api_key:
            if self.environment == "production":
                raise ValueError("OpenAI API key is required for OpenAI provider")
        elif self.llm_provider == LLMProvider.ANTHROPIC and not self.anthropic_api_key:
            if self.environment == "production":
                raise ValueError("Anthropic API key is required for Anthropic provider")
        
        # Validate numeric ranges
        if not 0.0 <= self.default_model_temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        
        if self.discovery_interval_seconds < 10:
            raise ValueError("Discovery interval must be at least 10 seconds")
        
        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")
    
    @property
    def has_openai_config(self) -> bool:
        """Check if OpenAI configuration is available"""
        return bool(self.openai_api_key) and self.llm_provider in ["openai", "both"]
    
    @property
    def has_anthropic_config(self) -> bool:
        """Check if Anthropic configuration is available"""
        return bool(self.anthropic_api_key) and self.llm_provider in ["anthropic", "both"]
    
    @property
    def docker_available(self) -> bool:
        """Check if Docker socket is available"""
        return os.path.exists(self.docker_socket_path)
    
    def get_openai_config(self) -> dict:
        """Get OpenAI client configuration"""
        if not self.has_openai_config:
            raise ValueError("OpenAI configuration not available")
        
        return {
            "api_key": self.openai_api_key,
            "model": self.openai_model,
            "temperature": self.default_model_temperature,
            "max_tokens": self.openai_max_tokens,
            "timeout": self.openai_timeout
        }
    
    def get_anthropic_config(self) -> dict:
        """Get Anthropic client configuration"""
        if not self.has_anthropic_config:
            raise ValueError("Anthropic configuration not available")
        
        return {
            "api_key": self.anthropic_api_key,
            "model": self.anthropic_model,
            "temperature": self.default_model_temperature,
            "max_tokens": self.anthropic_max_tokens,
            "timeout": self.anthropic_timeout
        }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


def get_settings_for_testing(**overrides) -> Settings:
    """Get settings instance for testing with overrides"""
    # Don't use cache for testing
    return Settings(**overrides)