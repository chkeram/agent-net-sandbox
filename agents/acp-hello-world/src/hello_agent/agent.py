"""Hello World Agent implementation."""

import uuid
from datetime import datetime
from typing import Dict, Optional, Any
from .models import (
    HelloInput, HelloOutput, HelloConfig, 
    InvokeRequest, InvokeResponse, 
    ConfigRequest, ConfigResponse,
    AgentCapabilities, AgentCapability
)


class HelloWorldAgent:
    """A simple hello world agent implementation."""
    
    def __init__(self):
        self.agent_id = "hello-world-agent"
        self.agent_name = "Hello World Agent"
        self.version = "0.1.0"
        self.description = "A simple agent that generates greetings in multiple languages"
        self.configs: Dict[str, HelloConfig] = {}
        self.default_config = HelloConfig()
        
    def get_capabilities(self) -> AgentCapabilities:
        """Get agent capabilities."""
        hello_capability = AgentCapability(
            name="generate_greeting",
            description="Generate a personalized greeting message",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name to greet"},
                    "message": {"type": "string", "description": "Custom greeting message"},
                    "language": {"type": "string", "description": "Language for greeting"}
                }
            },
            output_schema={
                "type": "object", 
                "properties": {
                    "greeting": {"type": "string", "description": "The generated greeting"},
                    "timestamp": {"type": "string", "description": "When the greeting was generated"},
                    "agent_id": {"type": "string", "description": "ID of the agent"}
                },
                "required": ["greeting", "timestamp", "agent_id"]
            }
        )
        
        return AgentCapabilities(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            description=self.description,
            version=self.version,
            capabilities=[hello_capability],
            supported_languages=list(self.default_config.custom_greetings.keys())
        )
    
    def store_config(self, config: HelloConfig) -> ConfigResponse:
        """Store a configuration and return config ID."""
        config_id = str(uuid.uuid4())
        self.configs[config_id] = config
        
        return ConfigResponse(
            config_id=config_id,
            config=config,
            created_at=datetime.utcnow()
        )
    
    def get_config(self, config_id: str) -> Optional[HelloConfig]:
        """Get a stored configuration."""
        return self.configs.get(config_id)
    
    def generate_greeting(self, input_data: HelloInput, config: Optional[HelloConfig] = None) -> HelloOutput:
        """Generate a greeting based on input and configuration."""
        # Use provided config or default
        active_config = config or self.default_config
        
        # Get the appropriate greeting
        if input_data.message:
            # Use custom message if provided
            greeting_base = input_data.message
        else:
            # Use language-specific greeting
            language = input_data.language or active_config.default_language
            greeting_base = active_config.custom_greetings.get(language, "Hello")
        
        # Create the full greeting
        name = input_data.name or "World"
        full_greeting = f"{greeting_base}, {name}!"
        
        return HelloOutput(
            greeting=full_greeting,
            timestamp=datetime.utcnow(),
            agent_id=self.agent_id
        )
    
    def invoke(self, request: InvokeRequest) -> InvokeResponse:
        """Invoke the agent with the given request."""
        # Get configuration if config_id is provided in metadata
        config = request.config or self.default_config
        
        # Generate the greeting
        output = self.generate_greeting(request.input, config)
        
        # Create response
        response = InvokeResponse(
            output=output,
            status="completed",
            metadata={
                "agent_name": self.agent_name,
                "version": self.version,
                "processing_time_ms": 1  # Minimal processing time for hello world
            }
        )
        
        return response
    
    def get_schemas(self) -> Dict[str, Any]:
        """Get JSON schemas for input, output, and config."""
        return {
            "input": HelloInput.model_json_schema(),
            "output": HelloOutput.model_json_schema(), 
            "config": HelloConfig.model_json_schema()
        }