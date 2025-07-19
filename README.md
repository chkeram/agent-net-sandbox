# Multi-Protocol Agent Sandbox

A comprehensive development environment for building and testing agents across multiple communication protocols. This sandbox supports various agent frameworks and protocols, making it easy to compare implementations and develop multi-protocol agent systems.

## 🎯 Supported Protocols

| Protocol | Status | Port | Description |
|----------|--------|------|-------------|
| **ACP** | ✅ Implemented | 8000 | AGNTCY Agent Connect Protocol |
| **MCP** | 🚧 Coming Soon | 8001 | Anthropic's Model Context Protocol |
| **A2A** | 🚧 Coming Soon | 8002 | Agent-to-Agent Communication Protocol |
| **Custom** | 🚧 Template Ready | 8003+ | Your custom protocol implementations |

## 🏗️ Project Structure

```
agent-net-sandbox/
├── agents/                           # Individual agent implementations
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

### A2A Agent 🚧

**Protocol:** Agent-to-Agent Communication  
**Port:** 8002  
**Status:** Coming soon

**Planned Features:**
- Direct agent-to-agent communication
- Message routing and discovery
- Protocol negotiation
- Workflow coordination

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
- **Implementation**: [agents/a2a-example/](agents/a2a-example/) (coming soon)

## 🤝 Contributing

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

## 📝 License

This project is licensed under the Apache 2.0 License - see the LICENSE file for details.

## 🔗 Links

- [AGNTCY Internet of Agents](https://agntcy.org)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Agent-to-Agent Protocol](https://a2aprotocol.ai/)
- [Docker Documentation](https://docs.docker.com/)

## 🎉 Getting Started

Ready to build your first multi-protocol agent? 

1. **Start with ACP**: `docker-compose up acp-hello-world`
2. **Test the implementation**: `./scripts/test_all_agents.sh`
3. **Explore the code**: Check out `agents/acp-hello-world/`
4. **Add your protocol**: Follow the "Adding New Agents" guide
5. **Join the community**: Contribute your implementations!

Happy agent building! 🤖✨