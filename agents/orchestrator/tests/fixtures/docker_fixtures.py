"""Docker-related test fixtures"""

from typing import Dict, Any, List


def create_container_info(
    container_id: str = "test-container-123",
    name: str = "test-agent",
    protocol: str = "acp",
    agent_type: str = "test",
    port: int = 8000,
    labels: Dict[str, str] = None
) -> Dict[str, Any]:
    """Create mock container info for testing"""
    
    default_labels = {
        "agent.protocol": protocol,
        "agent.type": agent_type,
        "agent.version": "1.0.0",
        "agent.capabilities": "greeting,testing",
        "agent.name": f"{protocol.upper()} Test Agent"
    }
    
    if labels:
        default_labels.update(labels)
    
    return {
        "Id": container_id,
        "Names": [f"/{name}"],
        "Config": {
            "Labels": default_labels
        },
        "NetworkSettings": {
            "Networks": {
                "agent-network": {
                    "IPAddress": "172.18.0.2"
                }
            },
            "Ports": {
                f"{port}/tcp": [{"HostPort": str(port)}]
            }
        },
        "Ports": [
            {
                "PrivatePort": port,
                "PublicPort": port,
                "Type": "tcp"
            }
        ]
    }


def create_acp_capabilities_response() -> Dict[str, Any]:
    """Create mock ACP capabilities response"""
    return {
        "name": "ACP Test Agent",
        "acp_version": "0.1",
        "capabilities": [
            {
                "name": "greeting",
                "description": "Generate greetings in multiple languages",
                "examples": [
                    {"input": {"name": "Alice"}, "output": {"message": "Hello, Alice!"}}
                ]
            },
            "testing"  # String capability
        ],
        "auth": {"required": False},
        "streaming": True
    }


def create_acp_schema_response() -> Dict[str, Any]:
    """Create mock ACP schema response"""
    return {
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "language": {"type": "string", "default": "en"}
            },
            "required": ["name"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "language": {"type": "string"}
            }
        }
    }


def create_a2a_agent_info_response() -> Dict[str, Any]:
    """Create mock A2A agent info response"""
    return {
        "agent_id": "a2a-math-agent",
        "name": "A2A Math Agent",
        "protocol_version": "1.0",
        "supports_peer_discovery": True,
        "message_formats": ["json", "msgpack"],
        "services": [
            {
                "name": "calculate",
                "description": "Perform mathematical calculations",
                "input_format": {"type": "object", "properties": {"expression": {"type": "string"}}},
                "output_format": {"type": "object", "properties": {"result": {"type": "number"}}},
                "examples": [
                    {"input": {"expression": "2 + 2"}, "output": {"result": 4}}
                ]
            }
        ],
        "supported_actions": ["calculate", "validate_expression"]
    }


def create_mcp_tools_response() -> List[Dict[str, Any]]:
    """Create mock MCP tools response"""
    return [
        {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "units": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                },
                "required": ["location"]
            },
            "returns": {
                "type": "object",
                "properties": {
                    "temperature": {"type": "number"},
                    "description": {"type": "string"}
                }
            }
        }
    ]


def create_mcp_resources_response() -> List[Dict[str, Any]]:
    """Create mock MCP resources response"""
    return [
        {
            "name": "weather_data",
            "description": "Historical weather data resource",
            "schema": {
                "type": "object",
                "properties": {
                    "date": {"type": "string"},
                    "temperature": {"type": "number"},
                    "conditions": {"type": "string"}
                }
            }
        }
    ]


def create_mcp_server_info_response() -> Dict[str, Any]:
    """Create mock MCP server info response"""
    return {
        "name": "MCP Weather Agent",
        "version": "1.0.0",
        "supports_streaming": False
    }


def create_health_response(status: str = "healthy") -> Dict[str, str]:
    """Create mock health response"""
    return {"status": status}


def create_mock_container(container_info: Dict[str, Any]):
    """Create mock Docker container object"""
    class MockContainer:
        def __init__(self, attrs):
            self.attrs = attrs
            self.id = attrs["Id"]
    
    return MockContainer(container_info)