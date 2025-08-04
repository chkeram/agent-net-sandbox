"""Pytest configuration and fixtures for orchestrator tests"""

import pytest
import asyncio
import os
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock

from orchestrator.config import Settings, get_settings_for_testing
from orchestrator.models import (
    DiscoveredAgent,
    AgentCapability,
    ProtocolType,
    AgentStatus,
)


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings with safe defaults"""
    return get_settings_for_testing(
        debug=True,
        environment="development",
        openai_api_key="test-openai-key",
        anthropic_api_key="test-anthropic-key",
        llm_provider="openai",
        discovery_interval_seconds=60,  # Longer for tests
        discovery_timeout_seconds=3,
        docker_network="test-agent-network",
        enable_metrics=False,  # Disable for tests
        log_level="DEBUG",
    )


@pytest.fixture
def mock_docker_client():
    """Mock Docker client for testing"""
    mock_client = MagicMock()
    mock_container = MagicMock()
    mock_container.id = "test-container-id"
    mock_container.name = "test-agent"
    mock_container.attrs = {
        "Id": "test-container-id",
        "Names": ["/test-agent"],
        "Config": {
            "Labels": {
                "agent.protocol": "acp",
                "agent.type": "test",
                "agent.version": "1.0.0",
                "agent.capabilities": "greeting,testing",
            }
        },
        "NetworkSettings": {
            "Networks": {
                "test-agent-network": {
                    "IPAddress": "172.18.0.2"
                }
            }
        },
        "Ports": [{"PublicPort": 8000, "PrivatePort": 8000}]
    }
    
    mock_client.containers.list.return_value = [mock_container]
    return mock_client


@pytest.fixture
def sample_capability() -> AgentCapability:
    """Create a sample agent capability for testing"""
    return AgentCapability(
        name="greeting",
        description="Generate greetings in multiple languages",
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "language": {"type": "string", "default": "en"}
            },
            "required": ["name"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "language": {"type": "string"}
            }
        },
        examples=[
            {"input": {"name": "Alice", "language": "en"}, "output": {"message": "Hello, Alice!", "language": "en"}},
            {"input": {"name": "Bob", "language": "es"}, "output": {"message": "¡Hola, Bob!", "language": "es"}},
        ],
        tags=["multilingual", "greeting"]
    )


@pytest.fixture
def sample_discovered_agent(sample_capability) -> DiscoveredAgent:
    """Create a sample discovered agent for testing"""
    return DiscoveredAgent(
        agent_id="acp-hello-world",
        name="ACP Hello World Agent",
        protocol=ProtocolType.ACP,
        endpoint="http://test-agent:8000",
        capabilities=[sample_capability],
        status=AgentStatus.HEALTHY,
        metadata={
            "acp_version": "0.1",
            "auth_required": False,
            "streaming_supported": True
        },
        container_id="test-container-id",
        version="1.0.0"
    )


@pytest.fixture
def multiple_discovered_agents(sample_capability) -> list[DiscoveredAgent]:
    """Create multiple discovered agents for testing"""
    agents = []
    
    # ACP Agent
    agents.append(DiscoveredAgent(
        agent_id="acp-hello-world",
        name="ACP Hello World Agent",
        protocol=ProtocolType.ACP,
        endpoint="http://acp-agent:8000",
        capabilities=[sample_capability],
        status=AgentStatus.HEALTHY,
        metadata={"acp_version": "0.1"},
        container_id="acp-container-id",
        version="1.0.0"
    ))
    
    # A2A Agent
    math_capability = AgentCapability(
        name="mathematics",
        description="Perform mathematical calculations",
        input_schema={"type": "object", "properties": {"expression": {"type": "string"}}},
        output_schema={"type": "object", "properties": {"result": {"type": "number"}}},
        tags=["math", "calculation"]
    )
    
    agents.append(DiscoveredAgent(
        agent_id="a2a-math-agent",
        name="A2A Math Agent",
        protocol=ProtocolType.A2A,
        endpoint="http://a2a-agent:8000",
        capabilities=[math_capability],
        status=AgentStatus.HEALTHY,
        metadata={"a2a_version": "1.0"},
        container_id="a2a-container-id",
        version="1.0.0"
    ))
    
    # Unhealthy agent
    agents.append(DiscoveredAgent(
        agent_id="unhealthy-agent",
        name="Unhealthy Agent",
        protocol=ProtocolType.CUSTOM,
        endpoint="http://unhealthy-agent:8000",
        capabilities=[],
        status=AgentStatus.UNHEALTHY,
        metadata={},
        container_id="unhealthy-container-id",
        version="1.0.0"
    ))
    
    return agents


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for HTTP requests"""
    mock_client = AsyncMock()
    
    # Mock successful health check
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "healthy"}
    
    mock_client.get.return_value = mock_response
    mock_client.post.return_value = mock_response
    
    return mock_client


@pytest.fixture
def mock_pydantic_ai_agent():
    """Mock Pydantic AI agent for testing"""
    mock_agent = AsyncMock()
    
    # Mock successful run
    mock_result = AsyncMock()
    mock_result.data = {
        "selected_agent": "acp-hello-world",
        "reasoning": "This agent can handle greeting requests",
        "confidence": 0.9,
        "alternative_agents": []
    }
    
    mock_agent.run.return_value = mock_result
    return mock_agent


@pytest.fixture
def env_vars() -> Dict[str, str]:
    """Environment variables for testing"""
    return {
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "ORCHESTRATOR_LLM_PROVIDER": "openai",
        "ORCHESTRATOR_DEBUG": "true",
        "ORCHESTRATOR_ENVIRONMENT": "development",
        "ORCHESTRATOR_DISCOVERY_INTERVAL_SECONDS": "60",
        "ORCHESTRATOR_ENABLE_METRICS": "false",
    }


@pytest.fixture(autouse=True)
def setup_test_env(env_vars):
    """Automatically set up test environment variables"""
    original_env = {}
    
    # Set test environment variables
    for key, value in env_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Restore original environment
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@pytest.fixture
def mock_logger():
    """Mock logger for testing"""
    return MagicMock()


# Markers for different test types
pytestmark = pytest.mark.asyncio