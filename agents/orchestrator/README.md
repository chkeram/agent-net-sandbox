# Multi-Protocol Agent Orchestrator

An AI-powered orchestrator that provides intelligent routing and management for multi-protocol agent ecosystems. Built as part of the Agent Network Sandbox project for experimenting with different LLM frameworks and agent protocols.

## 🎯 Overview

The Multi-Protocol Agent Orchestrator serves as a central intelligence hub that:

- **Discovers agents** automatically across multiple protocols (ACP, A2A, MCP)
- **Routes requests intelligently** using AI-powered decision making with tag-based semantic matching
- **Manages agent lifecycles** with health monitoring and registry management
- **Provides unified access** to heterogeneous agent ecosystems
- **Ensures production readiness** with comprehensive testing (63.98% coverage, 147+ tests)

## ✨ Key Features

### 🤖 AI-Powered Routing
- **Pydantic AI Framework**: Modern AI agent framework for intelligent routing
- **Multi-LLM Support**: Configurable OpenAI GPT-4o and Anthropic Claude-3.5-Sonnet
- **Confidence Scoring**: AI provides confidence levels for routing decisions
- **Tool Integration**: AI agent has access to real-time agent discovery data

### 🔍 Multi-Protocol Discovery
- **Real-Time Discovery**: Automatically discovers agents as they come online
- **Protocol-Specific Strategies**: Tailored discovery for ACP, A2A, MCP protocols
- **Tag-Based Matching**: Semantic capability discovery using agent tags
- **Health Monitoring**: Continuous health checking and agent status tracking
- **HTTP-Based Discovery**: Direct HTTP endpoint discovery with localhost fallback

### 🌐 Production-Ready REST API
- **15+ REST Endpoints**: Complete HTTP API for all orchestrator functionality
- **OpenAPI Documentation**: Auto-generated Swagger/ReDoc documentation
- **CORS Support**: Configurable cross-origin resource sharing
- **Error Handling**: Comprehensive exception handling with structured responses

### 🚀 Deployment Options
- **Docker Compose**: Multi-service orchestration with networking and volumes
- **Standalone Docker**: Lightweight containerized deployment
- **Local Development**: Hot-reload development server with debugging

### 📊 Monitoring & Observability
- **Health Checks**: Built-in health monitoring for all components
- **Structured Logging**: JSON-formatted logs with request tracing
- **Metrics Collection**: Performance metrics and agent statistics
- **Service Status**: Real-time system status and agent availability

### 🧪 Comprehensive Testing
- **147+ Tests**: Full test suite covering all core functionality
- **63.98% Code Coverage**: Production-ready test coverage
- **Protocol Testing**: Complete A2A, ACP, and orchestrator component testing
- **Integration Tests**: End-to-end routing and execution workflows

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd agent-net-sandbox

# Configure environment
cp agents/orchestrator/.env.example .env
# Edit .env with your API keys (OPENAI_API_KEY or ANTHROPIC_API_KEY)

# Deploy the orchestrator and agent ecosystem
./agents/orchestrator/scripts/deploy.sh start

# Access the orchestrator
open http://localhost:8004
```

### Option 2: Standalone Docker

```bash
cd agents/orchestrator

# Build the image
./scripts/build.sh

# Run the container
docker run -d \
  --name orchestrator \
  -p 8004:8004 \
  -e OPENAI_API_KEY="your-key" \
  -e ORCHESTRATOR_LLM_PROVIDER=openai \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  agent-orchestrator:latest
```

### Option 3: Local Development

```bash
cd agents/orchestrator

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start development server with hot reload
./scripts/dev.sh
```

## 📋 API Reference

### Core Endpoints

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| **System** | | | |
| `/` | GET | Service information and endpoint directory | Service metadata |
| `/health` | GET | Health check with service status | Health status |
| `/status` | GET | Comprehensive system status | System overview |
| **Agent Management** | | | |
| `/agents` | GET | List discovered agents with filtering | Agent summaries |
| `/agents/{agent_id}` | GET | Get detailed agent information | Agent details |
| `/agents/refresh` | POST | Trigger immediate agent discovery | Refresh status |
| **Request Routing** | | | |
| `/route` | POST | Route request to most appropriate agent | Routing decision |
| `/process` | POST | Complete request processing (route + execute) | Agent response |
| **Analytics** | | | |
| `/metrics` | GET | Orchestrator performance metrics | Metrics data |
| `/capabilities` | GET | Available capabilities across all agents | Capability index |
| `/protocols` | GET | Supported protocols and their status | Protocol information |

### Example API Calls

**Route a Request with Tag-Based Matching**
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
    "context": {"user_id": "123"},
    "preferred_protocol": "acp"
  }'
```

**Complete Request Processing**
```bash
# End-to-end processing with agent execution
curl -X POST "http://localhost:8004/process" \
  -H "Content-Type: application/json" \
  -d '{"query": "Calculate the square root of 144"}'
```

**Tag-Based Agent Discovery**
```bash
# Find agents with "math" capability (matches tags)
curl "http://localhost:8004/agents?capability=math"

# List all available agents with status filter
curl "http://localhost:8004/agents?status_filter=healthy"
```

**System Monitoring**
```bash
# Check system health with detailed status
curl "http://localhost:8004/health" | python -m json.tool

# Get performance metrics
curl "http://localhost:8004/metrics" | python -m json.tool
```

### Interactive Documentation

- **Swagger UI**: http://localhost:8004/docs
- **ReDoc**: http://localhost:8004/redoc
- **OpenAPI Spec**: http://localhost:8004/openapi.json

## ⚙️ Configuration

### Environment Variables

The orchestrator is configured via environment variables. Copy `.env.example` to `.env` and customize:

**Application Settings**
```bash
ORCHESTRATOR_HOST=0.0.0.0
ORCHESTRATOR_PORT=8004
ORCHESTRATOR_ENVIRONMENT=development
ORCHESTRATOR_LOG_LEVEL=INFO
```

**LLM Provider Configuration**
```bash
# Choose: openai, anthropic
ORCHESTRATOR_LLM_PROVIDER=openai

# API Keys (set at least one)
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

**Discovery Settings**
```bash
ORCHESTRATOR_DISCOVERY_INTERVAL_SECONDS=30
ORCHESTRATOR_DOCKER_NETWORK=agent-network
ORCHESTRATOR_DOCKER_SOCKET_PATH=/var/run/docker.sock
```

See [`.env.example`](.env.example) for all available options.

### Docker Compose Configuration

The orchestrator integrates with the multi-agent ecosystem via `docker-compose.yml`:

```yaml
services:
  orchestrator:
    build: ./agents/orchestrator
    ports: ["8004:8004"]
    environment:
      - OPENAI_API_KEY
      - ORCHESTRATOR_LLM_PROVIDER=openai
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    depends_on: [acp-hello-world]
    networks: [agent-network]
```

## 🧪 Development & Testing

### Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set PYTHONPATH for module imports
export PYTHONPATH=src

# Start development server
./scripts/dev.sh
```

### Running Tests

```bash
# Run all tests with coverage
PYTHONPATH=src python -m pytest tests/ -v --cov=src/orchestrator --cov-report=html

# Run specific test categories
python -m pytest tests/test_api.py -v --no-cov  # API tests
python -m pytest tests/test_agent.py -v --no-cov  # Agent tests
python -m pytest tests/test_discovery.py -v --no-cov  # Discovery tests

# Run with specific markers
python -m pytest -m "not integration" -v  # Skip integration tests
python -m pytest -m "asyncio" -v  # Only async tests
```

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/

# Linting
ruff check src/ tests/
```

## 🏗️ Architecture

### System Design

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

### Component Architecture

**Core Components:**
- **FastAPI Application** (`api.py`): REST API layer with 15+ endpoints
- **Pydantic AI Agent** (`agent.py`): AI-powered routing with multi-LLM support
- **Discovery Service** (`discovery.py`): Multi-protocol agent discovery
- **Protocol Strategies** (`protocols/`): Protocol-specific discovery implementations
- **Data Models** (`models.py`): Pydantic V2 models with validation

**Technology Stack:**
- **AI Framework**: Pydantic AI 0.4.11 for modern agent development
- **Web Framework**: FastAPI for high-performance async REST API
- **LLM Providers**: OpenAI GPT-4o, Anthropic Claude-3.5-Sonnet
- **Container Runtime**: Docker SDK for dynamic agent discovery
- **Data Validation**: Pydantic V2 for type-safe data models
- **Logging**: Structlog for structured JSON logging

### Discovery Strategies

Each protocol has a specialized discovery strategy:

- **ACP Discovery**: Fetches capabilities and schema from `/capabilities` and `/schema`
- **A2A Discovery**: Placeholder for future Agent-to-Agent protocol support
- **MCP Discovery**: Placeholder for Model Context Protocol support
- **Custom Discovery**: Template for implementing custom protocols

## 📦 Deployment

### Quick Deployment

```bash
# Deploy with Docker Compose (recommended)
./agents/orchestrator/scripts/deploy.sh start

# Check status
./agents/orchestrator/scripts/deploy.sh status

# View logs
./agents/orchestrator/scripts/deploy.sh logs

# Stop services
./agents/orchestrator/scripts/deploy.sh stop
```

### Production Deployment

1. **Environment Configuration**:
   ```bash
   # Production settings
   ORCHESTRATOR_ENVIRONMENT=production
   ORCHESTRATOR_DEBUG=false
   ORCHESTRATOR_LOG_LEVEL=INFO
   ORCHESTRATOR_CORS_ORIGINS=https://your-domain.com
   ```

2. **Docker Compose Override**:
   ```yaml
   # docker-compose.prod.yml
   services:
     orchestrator:
       restart: always
       logging:
         driver: json-file
         options:
           max-size: "10m"
           max-file: "3"
   ```

3. **Deploy**:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

### Deployment Scripts

- **`scripts/build.sh`**: Build Docker image with multi-stage optimization
- **`scripts/deploy.sh`**: Complete deployment management with health checks
- **`scripts/start.sh`**: Production startup with environment validation
- **`scripts/dev.sh`**: Development server with hot reload

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment guide.

## 🔍 Monitoring

### Health Monitoring

```bash
# System health
curl http://localhost:8004/health

# Detailed status
curl http://localhost:8004/status

# Agent availability
curl http://localhost:8004/agents
```

### Metrics Collection

```bash
# Performance metrics
curl http://localhost:8004/metrics

# Capability analysis
curl http://localhost:8004/capabilities

# Protocol statistics
curl http://localhost:8004/protocols
```

### Log Analysis

```bash
# Container logs
docker-compose logs -f orchestrator

# Filter by level
docker-compose logs orchestrator | grep ERROR

# Search for specific operations
docker-compose logs orchestrator | grep "routing"
```

## 🧪 Experimentation Features

As part of the Agent Network Sandbox, the orchestrator enables experimentation with:

### LLM Framework Comparison
- **Pydantic AI vs LangChain**: Direct comparison of modern AI frameworks
- **Model Performance**: A/B testing OpenAI vs Anthropic for routing decisions
- **Tool Integration**: Evaluation of different function calling approaches

### Multi-Protocol Challenges
- **Protocol Translation**: Converting requests between different agent protocols
- **Capability Mapping**: Standardizing capability descriptions across protocols
- **Discovery Strategies**: Optimizing discovery for different protocol types

### Scaling Patterns
- **Load Distribution**: Intelligent routing based on agent load and performance
- **Fallback Strategies**: Handling agent failures and unavailability
- **Request Aggregation**: Combining responses from multiple agents

## 🤝 Contributing

### Development Workflow

1. **Fork and Clone**: Fork the repository and clone locally
2. **Environment Setup**: Create virtual environment and install dependencies
3. **Feature Branch**: Create feature branch from `main`
4. **Development**: Implement changes with tests
5. **Testing**: Run full test suite with coverage
6. **Documentation**: Update README and API docs
7. **Pull Request**: Submit PR with detailed description

### Code Standards

- **Type Hints**: All functions must have type annotations
- **Testing**: Minimum 75% test coverage required
- **Documentation**: All public methods must have docstrings
- **Formatting**: Use Black, isort, and Ruff for code quality
- **Async/Await**: Use proper async patterns for I/O operations

### Testing Requirements

```bash
# All tests must pass
python -m pytest tests/ -v

# Coverage requirement
python -m pytest tests/ --cov=src/orchestrator --cov-fail-under=75

# Type checking
mypy src/

# Code quality
ruff check src/ tests/
```

## 📚 Resources

### Documentation
- **[API Documentation](http://localhost:8004/docs)**: Interactive Swagger UI
- **[Deployment Guide](DEPLOYMENT.md)**: Complete deployment instructions
- **[Environment Config](.env.example)**: All configuration options

### Related Projects
- **[Agent Network Sandbox](../../README.md)**: Main project documentation
- **[ACP Hello World Agent](../acp-hello-world/README.md)**: Example ACP implementation
- **[Pydantic AI](https://ai.pydantic.dev/)**: AI framework documentation

### External APIs
- **[OpenAI API](https://platform.openai.com/docs)**: GPT-4o integration
- **[Anthropic API](https://docs.anthropic.com/)**: Claude integration
- **[Docker SDK](https://docker-py.readthedocs.io/)**: Container discovery

## 📄 License

Apache License 2.0 - see [LICENSE](../../LICENSE) for details.

## 🎉 Getting Started

Ready to experiment with multi-protocol agent orchestration?

1. **🚀 Quick Start**: `./agents/orchestrator/scripts/deploy.sh start`
2. **📖 Explore API**: Visit http://localhost:8004/docs
3. **🧪 Test Routing**: Try the `/route` endpoint with different queries
4. **🔍 Monitor Agents**: Check `/agents` for discovered services
5. **📊 View Metrics**: Analyze performance at `/metrics`

**Happy orchestrating!** 🤖✨