"""Data models for the Hello World Agent."""

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import uuid
from datetime import datetime


class AuthMethod(str, Enum):
    """Supported authentication methods."""
    NONE = "none"
    API_KEY = "api_key"
    BEARER = "bearer"


class AuthInfo(BaseModel):
    """Authentication information."""
    type: AuthMethod = AuthMethod.NONE
    description: str = "No authentication required"


class HelloInput(BaseModel):
    """Input schema for hello world requests."""
    name: Optional[str] = Field(default="World", description="Name to greet")
    message: Optional[str] = Field(default=None, description="Custom greeting message")
    language: Optional[str] = Field(default="en", description="Language for greeting")


class HelloOutput(BaseModel):
    """Output schema for hello world responses."""
    greeting: str = Field(description="The generated greeting")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the greeting was generated")
    agent_id: str = Field(description="ID of the agent that generated the greeting")


class HelloConfig(BaseModel):
    """Configuration schema for the hello world agent."""
    agent_name: str = Field(default="Hello World Agent", description="Name of the agent")
    default_language: str = Field(default="en", description="Default language for greetings")
    custom_greetings: Dict[str, str] = Field(
        default_factory=lambda: {
            "en": "Hello",
            "es": "Hola", 
            "fr": "Bonjour",
            "de": "Hallo",
            "it": "Ciao"
        },
        description="Custom greeting messages by language"
    )


class AgentCapability(BaseModel):
    """Individual agent capability."""
    name: str = Field(description="Name of the capability")
    description: str = Field(description="Description of what this capability does")
    input_schema: Optional[Dict[str, Any]] = Field(default=None, description="JSON schema for input")
    output_schema: Optional[Dict[str, Any]] = Field(default=None, description="JSON schema for output")


class AgentCapabilities(BaseModel):
    """Agent capabilities response."""
    agent_id: str = Field(description="Unique identifier for the agent")
    agent_name: str = Field(description="Human-readable name of the agent")
    description: str = Field(description="Description of what the agent does")
    version: str = Field(description="Version of the agent")
    capabilities: List[AgentCapability] = Field(description="List of capabilities")
    supported_languages: List[str] = Field(description="Supported greeting languages")


class InvokeRequest(BaseModel):
    """Request schema for agent invocation."""
    input: HelloInput = Field(description="Input data for the agent")
    config: Optional[HelloConfig] = Field(default=None, description="Optional configuration override")
    stream: bool = Field(default=False, description="Whether to stream the response")


class InvokeResponse(BaseModel):
    """Response schema for agent invocation."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique run ID")
    output: HelloOutput = Field(description="Agent output")
    status: str = Field(default="completed", description="Status of the run")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ConfigRequest(BaseModel):
    """Request schema for agent configuration."""
    config: HelloConfig = Field(description="Configuration for the agent")


class ConfigResponse(BaseModel):
    """Response schema for agent configuration."""
    config_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique configuration ID")
    config: HelloConfig = Field(description="The stored configuration")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the config was created")


class SchemaDefinition(BaseModel):
    """Schema definition for input/output/config."""
    input: Dict[str, Any] = Field(description="Input schema")
    output: Dict[str, Any] = Field(description="Output schema") 
    config: Dict[str, Any] = Field(description="Configuration schema")


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str = Field(description="Error message")
    code: str = Field(description="Error code")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")