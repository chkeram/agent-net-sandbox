# 🤖 Agent Network Sandbox

*A production-ready Multi-Protocol Agent Orchestrator and development environment for building and testing agents across multiple communication protocols.*

**Get started in under 5 minutes** → [Quick Start Guide](QUICK_START.md)

The Agent Network Sandbox is a comprehensive platform that enables developers to experiment with different agent frameworks and protocols seamlessly. At its core is an AI-powered Multi-Protocol Agent Orchestrator that intelligently routes requests to the most appropriate agents across heterogeneous ecosystems.

## ✨ What Makes This Special

🧠 **AI-Powered Orchestration** - Intelligent routing using Pydantic AI with GPT-4o or Claude-3.5-Sonnet  
🔌 **Multi-Protocol Support** - ACP, A2A, MCP, and custom protocols in a unified platform  
🚀 **Production Ready** - Docker-based deployment with comprehensive testing (63.98% coverage)  
📚 **Developer Friendly** - Extensive documentation, examples, and 147+ tests  
🔧 **Highly Extensible** - Add new protocols and agents with minimal effort  
🏷️ **Tag-Based Discovery** - Semantic agent matching using capability tags  

---

## 🚀 Quick Start

**New here?** Get everything running in under 5 minutes:

```bash
# 1. Clone and start
git clone https://github.com/your-org/agent-net-sandbox.git
cd agent-net-sandbox
docker-compose up -d

# 2. Verify it works
./scripts/test_all_agents.sh

# 3. Try the orchestrator
curl -X POST "http://localhost:8004/process" \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello there!"}'
```

**Need more details?** → [Manual Setup Guide](MANUAL_SETUP.md)

---

## 🎯 Supported Protocols

| Protocol | Status | Port | Description |
|----------|--------|------|-------------|
| **ACP** | ✅ Production Ready | 8000 | AGNTCY Agent Connect Protocol |
| **A2A** | ✅ Production Ready | 8002 | Agent-to-Agent Communication Protocol |
| **MCP** | 🚧 Coming Soon | 8001 | Anthropic's Model Context Protocol |
| **Custom** | 🚧 Template Ready | 8003+ | Your custom protocol implementations |

## 🎯 Orchestrator Agent

The **Multi-Protocol Agent Orchestrator** is the central intelligence that manages and routes requests across all protocol implementations. It provides unified access to heterogeneous agent ecosystems.

| Component | Status | Port | Description |
|-----------|--------|------|-------------|
| **Orchestrator** | ✅ Implemented | 8004 | AI-powered request routing and agent management |
| **Discovery Service** | ✅ Implemented | - | Real-time agent discovery across protocols |
| **Routing Engine** | ✅ Implemented | - | Intelligent request-to-agent matching |

## 🏗️ Project Structure

```
agent-net-sandbox/
├── agents/                           # Individual agent implementations
│   ├── orchestrator/                # Multi-Protocol Agent Orchestrator (NEW)
│   │   ├── src/orchestrator/        # Orchestrator source code
│   │   │   ├── agent.py            # Pydantic AI routing agent
│   │   │   ├── discovery.py        # Multi-protocol discovery service
│   │   │   ├── models.py           # Data models and schemas
│   │   │   ├── config.py           # Configuration management
│   │   │   └── protocols/          # Protocol-specific discovery strategies
│   │   │       ├── acp_discovery.py    # ACP agent discovery
│   │   │       ├── a2a_discovery.py    # A2A agent discovery (stub)
│   │   │       ├── mcp_discovery.py    # MCP agent discovery (stub)
│   │   │       └── base.py             # Base discovery strategy
│   │   ├── tests/                  # Comprehensive test suite
│   │   ├── requirements.txt        # Python dependencies
│   │   ├── pyproject.toml         # Project configuration
│   │   └── Dockerfile             # Container definition
│   ├── acp-hello-world/             # ACP Hello World Agent (implemented)
│   │   ├── src/hello_agent/         # Agent source code
│   │   ├── agent-manifest.yaml      # AGNTCY manifest
│   │   ├── acp-descriptor.json      # ACP descriptor
│   │   ├── Dockerfile              # Container definition
│   │   ├── requirements.txt        # Python dependencies
│   │   └── README.md               # Agent-specific documentation
│   ├── mcp-example/                # Future MCP agent
│   ├── a2a-example/                # Future A2A agent
│   └── custom-protocol/            # Future custom protocol agent
├── common/                         # Shared utilities and libraries
├── scripts/                        # Testing and utility scripts
│   ├── agents/                     # Protocol-specific test scripts
│   │   └── test_acp.sh            # ACP agent tests
│   ├── test_all_agents.sh         # Master test script
│   ├── nginx.conf                 # Reverse proxy configuration
│   └── agent-directory.html       # Agent directory UI
├── docs/                          # Documentation
│   └── protocols/                 # Protocol-specific documentation
├── docker-compose.yml             # Multi-agent orchestration
└── README.md                      # This file
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- curl (for testing)

### Start All Agents

```bash
# Start all available agents
docker-compose up -d

# View running services
docker-compose ps

# Check logs
docker-compose logs -f
```

### Access Services

| Service | URL | Description |
|---------|-----|-------------|
| **ACP Hello World** | http://localhost:8000 | ACP-compliant greeting agent |
| **Agent Directory** | http://localhost:8080 | Web interface showing all agents |
| **OpenAPI Docs** | http://localhost:8000/docs | ACP agent API documentation |

### Test All Agents

```bash
# Run comprehensive tests for all agents
./scripts/test_all_agents.sh

# Test specific protocol
./scripts/agents/test_acp.sh
```

## 🎯 Multi-Protocol Agent Orchestrator

### Overview

The **Multi-Protocol Agent Orchestrator** is the core innovation of this sandbox - an AI-powered routing system that provides unified access to agents across different protocols. It acts as an intelligent gateway that understands user intent and routes requests to the most appropriate specialized agents.

### 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Query    │───▶│   Orchestrator   │───▶│ Protocol Agents │
│                 │    │                  │    │                 │
│ "Hello World"   │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ "Calculate 2+2" │    │ │ Pydantic AI  │ │    │ │ ACP Agent   │ │
│ "Get Weather"   │    │ │ Routing      │ │    │ │ MCP Agent   │ │
│                 │    │ │ Engine       │ │    │ │ A2A Agent   │ │
└─────────────────┘    │ └──────────────┘ │    │ │ Custom...   │ │
                       │                  │    │ └─────────────┘ │
                       │ ┌──────────────┐ │    └─────────────────┘
                       │ │ Discovery    │ │           ▲
                       │ │ Service      │ │           │
                       │ └──────────────┘ │───────────┘
                       └──────────────────┘
                          Real-time Agent
                            Discovery
```

### 🔧 Technology Stack

**Core Framework**: Built using cutting-edge AI and Python technologies for maximum flexibility and experimentation:

| Component | Technology | Purpose |
|-----------|------------|---------|
| **AI Routing** | [Pydantic AI 0.4.11](https://ai.pydantic.dev/) | Multi-LLM agent framework for intelligent routing |
| **LLM Support** | OpenAI GPT-4o, Anthropic Claude-3.5-Sonnet | Configurable AI models for routing decisions |
| **Discovery** | Custom Multi-Protocol Discovery Service | Real-time agent discovery across protocols |
| **Data Models** | Pydantic V2 | Type-safe data validation and serialization |
| **Configuration** | Pydantic Settings | Environment-based configuration management |
| **Async Runtime** | Python asyncio | High-performance asynchronous processing |
| **Container Discovery** | Docker API | Dynamic agent discovery via container labels |
| **Protocol Support** | ACP, A2A, MCP + Custom | Extensible protocol architecture |
| **Testing** | pytest + pytest-asyncio | Comprehensive async test coverage |
| **Logging** | structlog | Structured logging with context |

### 🚀 Key Features

#### 1. **Intelligent Routing**
- **AI-Powered Decision Making**: Uses Pydantic AI with GPT-4o or Claude-3.5-Sonnet to analyze user queries
- **Tag-Based Capability Matching**: Semantic matching via capability tags (e.g., "math" finds agents with "math" tags)
- **Confidence Scoring**: Provides confidence levels for routing decisions (0.0-1.0)
- **Fallback Handling**: Graceful handling when no suitable agent is found

#### 2. **Multi-Protocol Discovery**
- **Real-Time Discovery**: Automatically discovers agents as they come online
- **Protocol-Specific Strategies**: Tailored discovery for ACP, A2A, MCP protocols
- **Health Monitoring**: Continuous health checking and agent status tracking
- **HTTP-Based Discovery**: Uses HTTP endpoints for agent discovery with localhost fallback

#### 3. **Unified Agent Registry**
- **Centralized Management**: Single registry for all discovered agents
- **Tag-Based Indexing**: Searchable index of agent capabilities by name and tags
- **Performance Metrics**: Request tracking and performance monitoring
- **Status Management**: Real-time agent health and availability status

#### 4. **Flexible Configuration**
- **Multi-LLM Support**: Switch between OpenAI (GPT-4o) and Anthropic (Claude-3.5-Sonnet) models
- **Environment-Based**: Configuration via environment variables
- **Protocol Extension**: Easy addition of new protocol support
- **Development/Production**: Different configurations for different environments

#### 5. **Comprehensive Testing**
- **147+ Tests**: Comprehensive test suite with 63.98% code coverage
- **Protocol Coverage**: Full testing for A2A client, discovery service, and orchestrator agent
- **Integration Tests**: End-to-end testing of routing and execution workflows
- **Error Handling**: Comprehensive testing of failure scenarios and edge cases

### 📋 Implementation Details

#### Phase 1: Foundation ✅
- **Project Structure**: Modular architecture with clear separation of concerns
- **Data Models**: Comprehensive Pydantic models for all data types
- **Configuration System**: Environment-based settings with validation
- **Test Infrastructure**: pytest setup with comprehensive fixtures

#### Phase 2: Discovery Service ✅  
- **Multi-Protocol Discovery**: Unified discovery service with protocol-specific strategies
- **ACP Discovery**: Full implementation with capabilities and schema fetching
- **A2A Discovery**: Complete implementation with agent-card.json parsing and tag extraction
- **Health Monitoring**: Continuous agent health checking and registry management
- **HTTP-Based Discovery**: Direct HTTP endpoint discovery with fallback mechanisms

#### Phase 3: AI Routing Engine ✅
- **Pydantic AI Integration**: Modern AI agent framework with tool support
- **Multi-LLM Configuration**: Support for OpenAI GPT-4o and Anthropic Claude-3.5-Sonnet
- **Tag-Based Routing**: Enhanced capability matching using semantic tags
- **Request Processing**: Complete request lifecycle from routing to execution

#### Phase 4: A2A Protocol Integration ✅
- **A2A Client**: Full JSON-RPC client implementation with error handling
- **Protocol Compliance**: Complete adherence to A2A protocol specifications
- **Message Processing**: Support for A2A message structures and text extraction
- **Tag-Based Discovery**: Semantic agent discovery using capability tags

#### Phase 5: Comprehensive Testing ✅
- **Test Suite Expansion**: 147 tests covering all core functionality
- **Coverage Achievement**: 63.98% code coverage across all modules
- **Protocol Testing**: Comprehensive testing of A2A, ACP, and orchestrator components
- **Edge Case Handling**: Thorough testing of error conditions and failure scenarios

### 🧪 Experimentation Focus

This orchestrator serves as an **experimentation sandbox** for:

#### **LLM Framework Comparison**
- **Pydantic AI vs LangChain**: Direct comparison of modern AI frameworks
- **Model Performance**: Testing OpenAI vs Anthropic for routing decisions
- **Tool Integration**: Evaluation of different function/tool calling approaches

#### **Multi-Protocol Challenges**
- **Protocol Translation**: Converting requests between different agent protocols
- **Capability Mapping**: Standardizing capability descriptions across protocols
- **Discovery Strategies**: Optimizing discovery for different protocol types

#### **Scaling Patterns**
- **Load Distribution**: Intelligent routing based on agent load and performance
- **Fallback Strategies**: Handling agent failures and unavailability
- **Request Aggregation**: Combining responses from multiple agents

### 🔍 Discovery Mechanisms

```python
# Example: A2A Agent Discovery with Tags
{
  "agent_id": "a2a-math",
  "name": "Math Agent", 
  "protocol": "a2a",
  "endpoint": "http://a2a-math-agent:8002",
  "capabilities": [
    {
      "name": "basic arithmetic",
      "description": "Perform basic arithmetic operations",
      "tags": ["math", "arithmetic", "calculation"]
    },
    {
      "name": "advanced mathematics", 
      "description": "Solve complex mathematical problems",
      "tags": ["math", "algebra", "calculus"]
    }
  ],
  "status": "healthy",
  "metadata": {
    "version": "1.0.0",
    "protocolVersion": "1.0.0",
    "description": "Mathematical computation agent",
    "discovery_method": "http_a2a_agent_card"
  }
}

# Example: ACP Agent Discovery
{
  "agent_id": "acp-greeting-agent",
  "name": "Greeting Agent", 
  "protocol": "acp",
  "endpoint": "http://greeting-agent:8000",
  "capabilities": [
    {
      "name": "greeting", 
      "description": "Generate greetings in multiple languages",
      "tags": ["greeting", "hello", "welcome"]
    }
  ],
  "status": "healthy",
  "metadata": {
    "agent_id": "greeting-001",
    "version": "1.0.0",
    "discovery_method": "http_acp_capabilities"
  }
}
```

### 📊 Routing Intelligence

```python
# Example: AI Routing Decision
{
  "request_id": "req_12345",
  "selected_agent": {
    "agent_id": "acp-greeting-agent",
    "protocol": "acp"
  },
  "confidence": 0.95,
  "reasoning": "User request 'say hello' matches greeting capability perfectly. Agent supports multiple languages and has excellent health status.",
  "alternative_agents": ["a2a-chat-agent"],
  "estimated_response_time": 2.0
}
```

### 🚦 Usage Examples

#### Basic Routing with Semantic Matching
```bash
# Math query routed to A2A Math Agent via tag matching
curl -X POST "http://localhost:8004/route" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is 2 + 2?",
    "context": {"user_id": "123"}
  }'

# Greeting query routed to ACP Hello World Agent
curl -X POST "http://localhost:8004/route" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Say hello to me in Spanish",
    "context": {"user_id": "123"}
  }'
```

#### Complete Request Processing
```bash
# End-to-end processing with agent execution
curl -X POST "http://localhost:8004/process" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Calculate the square root of 144"
  }'
```

#### Tag-Based Capability Discovery
```bash
# Find agents with "math" capability (matches tags)
curl "http://localhost:8004/agents?capability=math"

# Find agents with "greeting" capability
curl "http://localhost:8004/agents?capability=greeting"
```

#### Health Status and Metrics
```bash
# Orchestrator health check
curl "http://localhost:8004/health"

# Performance metrics
curl "http://localhost:8004/metrics"
```

### 🔧 Development & Testing

```bash
# Run orchestrator locally with comprehensive test suite
cd agents/orchestrator
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt

# Run full test suite (147 tests)
PYTHONPATH=src python -m pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific test suites
python -m pytest tests/test_a2a_client.py -v          # A2A client tests
python -m pytest tests/test_discovery_enhanced.py -v  # Enhanced discovery tests
python -m pytest tests/test_orchestrator_agent.py -v  # Orchestrator agent tests

# Start with Docker
docker-compose up orchestrator

# View logs with structured output
docker-compose logs -f orchestrator | grep -E "(LLM_|TOOL_CALL|DECISION)"
```

The orchestrator represents the future of multi-agent systems - providing intelligent, AI-powered routing across heterogeneous agent ecosystems with production-ready testing (63.98% coverage) and comprehensive protocol support.

## 🤖 Available Agents

### ACP Hello World Agent ✅

**Protocol:** AGNTCY Agent Connect Protocol (ACP)  
**Port:** 8000  
**Status:** Fully implemented

**Features:**
- Full ACP compliance with all required endpoints
- Multi-language greeting support (5 languages)
- Streaming response capabilities
- Configuration management
- Discovery integration

**Quick Test:**
```bash
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{"input": {"name": "Sandbox", "language": "en"}}'
```

**Documentation:** [agents/acp-hello-world/README.md](agents/acp-hello-world/README.md)

### MCP Agent 🚧

**Protocol:** Model Context Protocol (MCP)  
**Port:** 8001  
**Status:** Coming soon

**Planned Features:**
- MCP server implementation
- Tool and resource exposure
- Model context management
- Client connection handling

### A2A Math Agent ✅

**Protocol:** Agent-to-Agent Communication Protocol (A2A)  
**Port:** 8002  
**Status:** Fully implemented

**Features:**
- Full A2A protocol compliance with JSON-RPC support
- Mathematical computation capabilities (basic arithmetic, advanced mathematics)
- Tag-based capability discovery (supports "math", "arithmetic", "calculation" tags)
- Skills-based agent card with metadata
- LLM fallback for complex mathematical operations
- Comprehensive test coverage (65/65 tests passing)

**Quick Test:**
```bash
curl -X POST "http://localhost:8002/" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "What is 2 + 2?"}],
        "messageId": "test_123"
      }
    },
    "id": "test_123"
  }'
```

**Documentation:** [agents/a2a-math-agent/README.md](agents/a2a-math-agent/README.md)

### Custom Protocol Agent 🚧

**Protocol:** Your custom implementation  
**Port:** 8003+  
**Status:** Template ready

**Use Cases:**
- Proprietary protocols
- Research implementations
- Protocol extensions
- Hybrid approaches

## 🛠️ Adding New Agents

### 1. Create Agent Directory

```bash
mkdir -p agents/{protocol}-{name}
cd agents/{protocol}-{name}
```

### 2. Implement Your Agent

Choose your preferred framework and language:
- Python (FastAPI, Flask, etc.)
- Node.js (Express, Koa, etc.)
- Go (Gin, Echo, etc.)
- Rust (Axum, Warp, etc.)
- Any language with HTTP support

### 3. Create Dockerfile

```dockerfile
FROM your-base-image

# Install dependencies
COPY requirements.txt .
RUN install-command

# Copy source code
COPY src/ ./src/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["your-start-command"]
```

### 4. Update Docker Compose

Add your service to `docker-compose.yml`:

```yaml
  your-agent-name:
    build:
      context: ./agents/your-protocol-name
      dockerfile: Dockerfile
    ports:
      - "8XXX:8000"  # Choose next available port
    networks:
      - agent-network
    labels:
      - "agent.protocol=your-protocol"
      - "agent.type=your-type"
```

### 5. Add Proxy Configuration

Update `scripts/nginx.conf`:

```nginx
location /agents/your-agent {
    proxy_pass http://your-agent-name:8000;
    proxy_set_header Host $host;
    # ... other headers
}
```

### 6. Create Test Scripts

Create `scripts/agents/test_your-protocol.sh`:

```bash
#!/bin/bash
# Test script for your protocol
# Follow the pattern from test_acp.sh
```

### 7. Update Documentation

- Update this README with your agent
- Create agent-specific README
- Update the agent directory HTML
- Add protocol documentation

## 🧪 Testing

### Master Test Suite

```bash
# Test all running agents
./scripts/test_all_agents.sh

# Output shows status of each agent
🧪 Multi-Protocol Agent Sandbox Test Suite
=============================================
✅ ACP Hello World Agent
🚧 MCP Agent (not running)
🚧 A2A Agent (not running)
```

### Individual Agent Testing

```bash
# Test specific protocol
AGENT_URL=http://localhost:8000 ./scripts/agents/test_acp.sh

# Test with custom URL
AGENT_URL=http://remote-host:8080 ./scripts/agents/test_acp.sh
```

### Development Testing

```bash
# Start specific agent for development
docker-compose up acp-hello-world

# Run agent locally
cd agents/acp-hello-world
python -m uvicorn hello_agent.app:app --reload
```

## 📊 Monitoring and Management

### Service Health

```bash
# Check all services
docker-compose ps

# View logs
docker-compose logs -f [service-name]

# Restart specific service
docker-compose restart acp-hello-world
```

### Agent Directory

Visit http://localhost:8080 for a web interface showing:
- All running agents
- Protocol information
- Health status
- API endpoints
- Testing interfaces

### Resource Usage

```bash
# View resource usage
docker stats

# View networks
docker network ls

# View volumes
docker volume ls
```

## 🔧 Development

### Local Development

```bash
# Work on specific agent
cd agents/acp-hello-world

# Install dependencies
pip install -r requirements.txt

# Run locally with hot reload
export PYTHONPATH=src
python -m uvicorn hello_agent.app:app --reload

# Run tests
python -m pytest tests/
```

### Adding Protocol Support

1. **Research the protocol** - Understand specifications and requirements
2. **Create agent structure** - Follow the project conventions
3. **Implement core functionality** - Focus on protocol compliance
4. **Add containerization** - Docker setup for deployment
5. **Create tests** - Comprehensive testing suite
6. **Update documentation** - README and protocol docs
7. **Integration** - Add to compose and directory

### Best Practices

- **Protocol Compliance**: Follow specifications exactly
- **Health Checks**: Always implement `/health` endpoint
- **Error Handling**: Proper HTTP status codes and responses
- **Documentation**: Clear API documentation
- **Testing**: Comprehensive test coverage
- **Security**: Follow container security best practices
- **Monitoring**: Structured logging and metrics

## 🗺️ Roadmap

### 🎉 Current Release (v1.0) - Production Ready
- ✅ **Multi-Protocol Agent Orchestrator** - AI-powered intelligent routing with Pydantic AI
- ✅ **ACP Protocol Support** - Full AGNTCY Agent Connect Protocol implementation
- ✅ **A2A Protocol Support** - Complete Agent-to-Agent Communication Protocol with JSON-RPC
- ✅ **Tag-Based Discovery** - Semantic agent matching using capability tags
- ✅ **Real-time Discovery** - Automatic agent discovery and health monitoring
- ✅ **Comprehensive Testing** - 147 tests with 63.98% code coverage
- ✅ **Production Documentation** - Complete setup and contribution guides
- ✅ **Docker Deployment** - Container-based architecture with Docker Compose

### 🚧 Next Release (v1.1) - Q1 2025
- 🔄 **MCP Protocol Support** - Anthropic's Model Context Protocol integration
- 🔄 **Enhanced Web UI** - Interactive agent directory with testing capabilities
- 🔄 **Metrics Dashboard** - Real-time monitoring and performance analytics
- 🔄 **Load Balancing** - Intelligent request distribution across agent instances
- 🔄 **Advanced Routing** - Multi-agent workflows and request orchestration

### 🔮 Future Releases (v1.2+)
- **Security Layer** - Authentication, authorization, and encrypted communications
- **Protocol Extensions** - Support for additional protocols and custom implementations
- **Scaling Features** - Kubernetes deployment and horizontal scaling
- **Developer Tools** - Protocol SDK, testing frameworks, and code generators
- **AI Model Expansion** - Support for additional LLM providers and models

### 🤝 Community Contributions Welcome
We're looking for contributors to help with:
- **Protocol Implementations** - Add support for new agent protocols
- **Agent Examples** - Reference implementations and use cases
- **Documentation** - Tutorials, guides, and protocol specifications
- **Testing** - Integration tests and performance benchmarks

---

## 📚 Protocol Documentation

### ACP (Agent Connect Protocol)

- **Specification**: https://spec.acp.agntcy.org/
- **Documentation**: [docs/protocols/acp.md](docs/protocols/acp.md)
- **Implementation**: [agents/acp-hello-world/](agents/acp-hello-world/)

### MCP (Model Context Protocol)

- **Specification**: https://spec.modelcontextprotocol.io/
- **Documentation**: [docs/protocols/mcp.md](docs/protocols/mcp.md) (coming soon)
- **Implementation**: [agents/mcp-example/](agents/mcp-example/) (coming soon)

### A2A (Agent-to-Agent Protocol)

- **Specification**: https://a2aprotocol.ai/
- **Documentation**: [docs/protocols/a2a.md](docs/protocols/a2a.md) (coming soon)
- **Implementation**: [agents/a2a-math-agent/](agents/a2a-math-agent/) ✅ Production Ready

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for detailed information.

**Quick contribution workflow:**

1. **Fork the repository**
2. **Create agent in appropriate directory**
3. **Follow project conventions**
4. **Add comprehensive tests**
5. **Update documentation**
6. **Submit pull request**

### Contribution Guidelines

- Use consistent naming conventions
- Follow Docker best practices
- Include health checks
- Provide clear documentation
- Add appropriate labels and metadata
- Test thoroughly across protocols

**Need help?** Check our [Contributing Guide](CONTRIBUTING.md) and [Security Policy](SECURITY.md)

---

## 🎫 Future Work & Community Tasks

The following features are planned for future development and community contributions:

### 📋 GitHub Issue & PR Templates
- **Issue Templates** (`.github/ISSUE_TEMPLATE/`) - Standardized templates for bug reports, feature requests, and protocol support requests
- **PR Template** (`.github/pull_request_template.md`) - Consistent pull request format with checklists and requirements

These templates will help maintain consistent quality and provide clear guidance for contributors. Community members are welcome to contribute these templates following GitHub's best practices.

### 🔧 Additional Planned Enhancements
- **CI/CD Workflows** - Automated testing, security scanning, and deployment pipelines
- **Protocol Testing Framework** - Automated compliance testing for new protocol implementations
- **Performance Benchmarking** - Automated performance testing and regression detection
- **Documentation Automation** - Auto-generated API docs and protocol specifications

---

## 📖 Documentation & Resources

### 📚 Setup & Usage
- **[Quick Start Guide](QUICK_START.md)** - Get running in 5 minutes
- **[Manual Setup Guide](MANUAL_SETUP.md)** - Detailed installation and development setup
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute agents and protocols  
- **[Security Policy](SECURITY.md)** - Security guidelines and vulnerability reporting

### 🔗 External Resources
- [AGNTCY Internet of Agents](https://agntcy.org) - ACP Protocol Ecosystem
- [Model Context Protocol](https://modelcontextprotocol.io/) - Anthropic's MCP Specification
- [Agent-to-Agent Protocol](https://a2aprotocol.ai/) - A2A Protocol Documentation
- [Docker Documentation](https://docs.docker.com/) - Container Platform Documentation
- [Pydantic AI](https://ai.pydantic.dev/) - Modern AI Agent Framework

---

## 🎉 Ready to Start?

**Choose your path:**

🚀 **Quick Start**: `git clone && docker-compose up -d` → [Quick Start Guide](QUICK_START.md)  
🛠️ **Development**: Local setup with hot reload → [Manual Setup Guide](MANUAL_SETUP.md)  
🤝 **Contributing**: Add protocols and agents → [Contributing Guide](CONTRIBUTING.md)  
🔍 **Deep Dive**: Explore the orchestrator → [Orchestrator Documentation](agents/orchestrator/README.md)  

---

## 📝 License

This project is licensed under the **Apache 2.0 License** - see the [LICENSE](LICENSE) file for details.

---

**Happy agent building!** 🤖✨

*Built with ❤️ for the multi-protocol agent community*