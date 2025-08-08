# Part 2: Configuration & Discovery

## 🎯 Learning Objectives

By the end of this tutorial, you will:
- Master the `agent-manifest.yaml` structure and its role
- Understand the `acp-descriptor.json` for protocol compliance
- Learn how agents advertise capabilities for discovery
- Implement proper metadata and tagging strategies
- Integrate your agent with discovery services

## 📚 Prerequisites

- Completed [Part 1: Understanding ACP Fundamentals](./01-understanding-acp.md)
- Basic understanding of YAML and JSON formats
- Familiarity with service discovery concepts

## 🗂️ Configuration Files Overview

ACP agents use two primary configuration files that serve different purposes:

1. **`agent-manifest.yaml`** - Comprehensive agent definition (AGNTCY-specific)
2. **`acp-descriptor.json`** - Protocol compliance descriptor (ACP standard)

Let's explore each in detail using our real implementation.

## 📋 The Agent Manifest (agent-manifest.yaml)

The agent manifest is the complete blueprint of your agent. Here's our actual manifest:

```yaml
# From agents/acp-hello-world/agent-manifest.yaml

apiVersion: agntcy.org/v1
kind: AgentManifest
metadata:
  name: hello-world-agent
  version: "0.1.0"
  description: "A simple hello world agent demonstrating AGNTCY Internet of Agents protocol"
  author: "AGNTCY Community"
  license: "Apache-2.0"
  tags:
    - hello-world
    - demo
    - agntcy
    - acp
```

### Metadata Section

The metadata section identifies your agent:

```yaml
metadata:
  name: hello-world-agent          # Unique identifier
  version: "0.1.0"                 # Semantic versioning
  description: "..."               # Clear, concise description
  author: "AGNTCY Community"       # Creator attribution
  license: "Apache-2.0"            # License type
  tags:                            # Discovery tags
    - hello-world
    - demo
    - agntcy
    - acp
```

**Best Practices:**
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Choose descriptive, unique names
- Add relevant tags for discovery
- Include proper licensing

### Specification Section

The spec section defines agent behavior:

```yaml
spec:
  agent:
    id: hello-world-agent
    name: "Hello World Agent"
    description: "A simple agent that generates greetings in multiple languages"
    version: "0.1.0"
```

### Capabilities Definition

This is where you declare what your agent can do:

```yaml
capabilities:
  - name: generate_greeting
    description: "Generate a personalized greeting message"
    inputSchema:
      type: object
      properties:
        name:
          type: string
          description: "Name to greet"
          default: "World"
        language:
          type: string
          description: "Language for greeting"
          default: "en"
          enum: ["en", "es", "fr", "de", "it"]
    outputSchema:
      type: object
      properties:
        greeting:
          type: string
          description: "The generated greeting"
        timestamp:
          type: string
          format: date-time
        agent_id:
          type: string
      required:
        - greeting
        - timestamp
        - agent_id
```

**Key Components:**
- **name**: Unique capability identifier
- **inputSchema**: JSON Schema for input validation
- **outputSchema**: JSON Schema for output structure
- **required**: Fields that must be present

### Configuration Schema

Define configurable parameters:

```yaml
configuration:
  schema:
    type: object
    properties:
      agent_name:
        type: string
        description: "Name of the agent"
        default: "Hello World Agent"
      default_language:
        type: string
        description: "Default language for greetings"
        default: "en"
      custom_greetings:
        type: object
        description: "Custom greeting messages by language"
        properties:
          en:
            type: string
            default: "Hello"
          es:
            type: string
            default: "Hola"
          fr:
            type: string
            default: "Bonjour"
```

This allows users to customize agent behavior without code changes.

### Deployment Configuration

Specify how the agent should be deployed:

```yaml
deployment:
  type: docker
  image: hello-world-agent:latest
  ports:
    - containerPort: 8000
      protocol: TCP
      name: http
  env:
    - name: PORT
      value: "8000"
    - name: HOST
      value: "0.0.0.0"
```

### Endpoints Declaration

List all ACP endpoints:

```yaml
endpoints:
  base_url: "http://localhost:8000"
  protocol: acp
  version: v0
  paths:
    auth: "/auth"
    schema: "/schema"
    config: "/config"
    invoke: "/invoke"
    capabilities: "/capabilities"
```

### Discovery Configuration

Enable and configure discovery:

```yaml
discovery:
  enabled: true
  keywords:
    - greeting
    - hello
    - multilingual
    - demo
  categories:
    - communication
    - demo
```

## 📄 The ACP Descriptor (acp-descriptor.json)

The ACP descriptor is a JSON file that ensures protocol compliance:

```json
{
  "agent_id": "hello-world-agent",
  "agent_name": "Hello World Agent",
  "version": "0.1.0",
  "description": "A simple agent that generates greetings in multiple languages",
  "protocol_version": "acp/v0",
  "base_url": "http://localhost:8000"
}
```

### Core Fields

```json
{
  "metadata": {
    "author": "AGNTCY Community",
    "license": "Apache-2.0",
    "tags": ["hello-world", "demo", "agntcy", "acp"],
    "categories": ["communication", "demo"],
    "keywords": ["greeting", "hello", "multilingual", "demo"]
  }
}
```

### Authentication Declaration

```json
{
  "authentication": {
    "type": "none",
    "description": "No authentication required"
  }
}
```

For agents requiring authentication:
```json
{
  "authentication": {
    "type": "api_key",
    "description": "API key required in X-API-Key header",
    "required": true
  }
}
```

### Endpoint Definitions

```json
{
  "endpoints": {
    "auth": {
      "path": "/auth",
      "method": "GET",
      "description": "Get authentication information"
    },
    "schema": {
      "path": "/schema",
      "method": "GET",
      "description": "Get JSON schemas for input, output, and configuration"
    },
    "invoke": {
      "path": "/invoke",
      "method": "POST",
      "description": "Invoke the agent with input data",
      "supports_streaming": true
    }
  }
}
```

### Capabilities Declaration

```json
{
  "capabilities": [
    {
      "name": "generate_greeting",
      "description": "Generate a personalized greeting message",
      "input_schema": {
        "type": "object",
        "properties": {
          "name": {"type": "string", "default": "World"},
          "language": {"type": "string", "enum": ["en", "es", "fr", "de", "it"]}
        }
      },
      "output_schema": {
        "type": "object",
        "properties": {
          "greeting": {"type": "string"},
          "timestamp": {"type": "string", "format": "date-time"}
        }
      }
    }
  ]
}
```

### Feature Support

```json
{
  "supported_features": {
    "streaming": true,
    "configuration": true,
    "discovery": true,
    "health_check": true
  }
}
```

## 🔍 Discovery Integration

### How Our Agent Advertises Itself

Our orchestrator discovers agents through multiple mechanisms:

```python
# From agents/orchestrator/src/orchestrator/protocols/acp_discovery.py

async def discover_acp_agent(self, endpoint: str) -> Optional[AgentInfo]:
    """Discover an ACP agent by querying its capabilities."""
    
    # 1. Check capabilities endpoint
    capabilities_url = f"{endpoint}/capabilities"
    response = await client.get(capabilities_url)
    capabilities_data = response.json()
    
    # 2. Extract capability information
    capabilities = []
    for cap in capabilities_data.get("capabilities", []):
        capability = AgentCapability(
            name=cap["name"],
            description=cap.get("description", ""),
            tags=self._extract_tags(cap)  # Extract tags from capability
        )
        capabilities.append(capability)
    
    # 3. Create AgentInfo with discovered data
    return AgentInfo(
        agent_id=f"acp-{agent_name}",
        name=agent_name,
        protocol="acp",
        endpoint=endpoint,
        capabilities=capabilities,
        status="healthy",
        metadata={
            "discovery_method": "http_acp_capabilities",
            "protocol_version": capabilities_data.get("protocol_version", "acp/v0")
        }
    )
```

### Tag-Based Discovery

Tags enable semantic discovery. Here's how we use them:

```python
# Our agent's tags for discovery
tags = ["greeting", "hello", "multilingual", "demo"]

# Orchestrator searches by tags
async def find_agents_by_capability(self, capability: str) -> List[AgentInfo]:
    """Find agents that match a capability."""
    matching_agents = []
    
    for agent in self.registry.values():
        for cap in agent.capabilities:
            # Check if capability matches tags
            if capability.lower() in [tag.lower() for tag in cap.tags]:
                matching_agents.append(agent)
                break
    
    return matching_agents
```

### Docker Labels for Discovery

We also use Docker labels for container-based discovery:

```yaml
# From docker-compose.yml
labels:
  - "agent.protocol=acp"
  - "agent.type=hello-world"
  - "agent.version=0.1.0"
  - "agent.capabilities=greeting,multilingual"
```

The orchestrator can discover agents via Docker:

```python
async def discover_docker_agents():
    """Discover agents running in Docker containers."""
    containers = docker_client.containers.list(
        filters={"label": "agent.protocol"}
    )
    
    for container in containers:
        labels = container.labels
        if labels.get("agent.protocol") == "acp":
            # Extract agent information from labels
            agent_info = create_agent_from_labels(labels)
            registry.register(agent_info)
```

## 🏷️ Best Practices for Configuration

### 1. Semantic Tagging

Use hierarchical, descriptive tags:
```yaml
tags:
  - category:communication    # Category
  - capability:greeting       # Specific capability
  - language:multilingual     # Feature
  - maturity:demo            # Development stage
```

### 2. Version Management

Follow semantic versioning strictly:
```yaml
version: "1.2.3"
# MAJOR.MINOR.PATCH
# MAJOR: Breaking changes
# MINOR: New features (backward compatible)
# PATCH: Bug fixes
```

### 3. Schema Validation

Always validate schemas:
```python
import jsonschema

def validate_configuration(config, schema):
    """Validate configuration against schema."""
    try:
        jsonschema.validate(config, schema)
        return True
    except jsonschema.ValidationError as e:
        logger.error(f"Configuration validation failed: {e}")
        return False
```

### 4. Environment-Specific Configuration

Support multiple environments:
```yaml
# agent-manifest.dev.yaml
metadata:
  name: hello-world-agent-dev
  tags:
    - development
    - testing

# agent-manifest.prod.yaml  
metadata:
  name: hello-world-agent
  tags:
    - production
    - stable
```

## 🔧 Implementing Configuration in Code

Here's how our agent loads and uses configuration:

```python
# From agents/acp-hello-world/src/hello_agent/agent.py

class HelloWorldAgent:
    def __init__(self):
        self.manifest = self._load_manifest()
        self.descriptor = self._load_descriptor()
        self.config_store = {}
    
    def _load_manifest(self):
        """Load agent manifest from YAML file."""
        with open("agent-manifest.yaml", "r") as f:
            return yaml.safe_load(f)
    
    def _load_descriptor(self):
        """Load ACP descriptor from JSON file."""
        with open("acp-descriptor.json", "r") as f:
            return json.load(f)
    
    def get_capabilities(self):
        """Return capabilities from manifest."""
        return self.manifest["spec"]["capabilities"]
    
    def get_schemas(self):
        """Extract schemas from manifest."""
        capability = self.manifest["spec"]["capabilities"][0]
        return {
            "input": capability["inputSchema"],
            "output": capability["outputSchema"],
            "config": self.manifest["spec"]["configuration"]["schema"]
        }
```

## 🚀 Testing Configuration and Discovery

Test your configuration:

```bash
# 1. Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('agent-manifest.yaml'))"

# 2. Validate JSON syntax
python -c "import json; json.load(open('acp-descriptor.json'))"

# 3. Test discovery endpoint
curl http://localhost:8000/capabilities | jq

# 4. Verify schema endpoint
curl http://localhost:8000/schema | jq

# 5. Test with orchestrator discovery
curl http://localhost:8004/agents?capability=greeting
```

## 📝 Configuration Checklist

Before deploying your agent, ensure:

- [ ] `agent-manifest.yaml` is valid YAML
- [ ] `acp-descriptor.json` is valid JSON
- [ ] All required fields are present
- [ ] Schemas are valid JSON Schema format
- [ ] Tags are descriptive and relevant
- [ ] Version follows semantic versioning
- [ ] Endpoints match implementation
- [ ] Discovery keywords are appropriate

## 🎓 Exercises

1. **Modify the manifest**: Add a new capability to the Hello World agent
2. **Update discovery tags**: Add domain-specific tags for better discovery
3. **Create environment configs**: Make dev and prod versions of the manifest
4. **Test discovery**: Use the orchestrator to discover your agent by tags

## 📚 Additional Resources

- [AGNTCY Manifest Specification](https://docs.agntcy.org/manifest)
- [JSON Schema Documentation](https://json-schema.org/)
- [Docker Labels for Metadata](https://docs.docker.com/config/labels-custom-metadata/)
- [Semantic Versioning](https://semver.org/)

## ⏭️ Next Steps

In [Part 3: Building Your First ACP Agent](./03-building-first-agent.md), we'll:
- Build a complete ACP agent from scratch
- Implement all required endpoints
- Add proper error handling
- Test with real requests

You now understand how ACP agents are configured and discovered. Ready to build your own?

---

*This tutorial is part of the Agent Network Sandbox educational series. All code examples are from our production-ready implementations.*