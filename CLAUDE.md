# CLAUDE.md - Agent Network Sandbox Context

## Project Overview

**Agent Network Sandbox** - A production-ready Multi-Protocol Agent Orchestrator and development environment for building and testing agents across multiple communication protocols. This is an educational project strictly following official protocol SDKs and architectural recommendations.

### Architecture
- **Multi-Protocol Support**: ACP, A2A, MCP, and custom protocols
- **AI-Powered Orchestrator**: Pydantic AI with GPT-4o/Claude-3.5-Sonnet for intelligent routing
- **Docker-Based**: Comprehensive containerization with Docker Compose
- **Production Ready**: 147+ tests with 63.98% coverage

### Service Ports
- **8000**: ACP Hello World Agent
- **8002**: A2A Math Agent  
- **8004**: Multi-Protocol Agent Orchestrator
- **8080**: Agent Directory (Nginx)

## ⚠️ CRITICAL: Virtual Environment Rules

**NEVER use global Python. ALWAYS work in the appropriate virtual environment for each agent.**

### Virtual Environment Locations
```
agents/orchestrator/venv/       # Orchestrator venv
agents/a2a-math-agent/venv/     # A2A Math Agent venv
agents/acp-hello-world/venv/    # ACP Hello World venv (create if needed)
```

### Before ANY Python Operation
```bash
# For Orchestrator
cd agents/orchestrator
source venv/bin/activate  # On Windows: venv\Scripts\activate

# For A2A Math Agent
cd agents/a2a-math-agent
source venv/bin/activate

# For ACP Hello World
cd agents/acp-hello-world
python -m venv venv  # Create if doesn't exist
source venv/bin/activate
```

### Venv Setup for New Agents
```bash
cd agents/{agent-name}
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If exists
```

## Testing Commands

### Master Test Suite
```bash
# Test all running agents (Docker)
./scripts/test_all_agents.sh

# Individual protocol tests
./scripts/agents/test_acp.sh
AGENT_URL=http://localhost:8002 ./scripts/agents/test_a2a.sh
```

### Orchestrator Testing (ALWAYS in venv)
```bash
cd agents/orchestrator
source venv/bin/activate
PYTHONPATH=src python -m pytest tests/ -v --cov=src --cov-report=term-missing

# Or use the test script
./run_tests.sh

# Specific test suites
python -m pytest tests/test_a2a_client.py -v
python -m pytest tests/test_discovery_enhanced.py -v
python -m pytest tests/test_orchestrator_agent.py -v
```

### A2A Math Agent Testing (ALWAYS in venv)
```bash
cd agents/a2a-math-agent
source venv/bin/activate
python -m pytest tests/ -v --cov=src/a2a_math_agent --cov-report=term-missing

# Test specific functionality
python -m pytest tests/test_math_operations.py -v
python -m pytest tests/test_llm_service.py -v
```

### Coverage Requirements
- **Minimum**: 75% for new code
- **Preferred**: 90%+ for critical components
- **Current**: 63.98% overall (aim to improve)

## Common Development Commands

### Docker Operations
```bash
# Start all services
docker-compose up -d

# View running services
docker-compose ps

# View logs
docker-compose logs -f [service-name]
docker-compose logs -f orchestrator
docker-compose logs -f a2a-math-agent

# Restart specific service
docker-compose restart orchestrator

# Rebuild and restart
docker-compose build orchestrator
docker-compose up -d orchestrator

# Stop all services
docker-compose down
```

### Local Development (ALWAYS in venv)
```bash
# Orchestrator development
cd agents/orchestrator
source venv/bin/activate
export PYTHONPATH=src
uvicorn orchestrator.api:app --reload --host 127.0.0.1 --port 8004

# A2A Math Agent development
cd agents/a2a-math-agent
source venv/bin/activate
export PYTHONPATH=/app
python -m a2a_math_agent.math_agent --port 8002

# ACP Hello World development
cd agents/acp-hello-world
source venv/bin/activate
export PYTHONPATH=src
python -m uvicorn hello_agent.app:app --reload --port 8000
```

### Health Checks
```bash
# Check service health
curl http://localhost:8000/health  # ACP
curl http://localhost:8002/.well-known/agent-card  # A2A
curl http://localhost:8004/health  # Orchestrator

# Test endpoints
curl -X POST "http://localhost:8004/process" \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello there!"}'

curl -X POST "http://localhost:8002/" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "What is 2 + 2?"}]
      }
    },
    "id": "test_123"
  }'
```

## Code Style & Formatting

### Python Standards (Run in appropriate venv)
```bash
# Format code with Black
black . --line-length 88

# Lint with Ruff
ruff check .
ruff check --fix .  # Auto-fix issues

# Type checking with MyPy
mypy src/

# Run all checks
black . && ruff check . && mypy src/
```

### Code Requirements
- **Type Hints**: Required for all functions
- **Docstrings**: Required for public functions/classes
- **Line Length**: 88 characters (Black default)
- **Import Order**: Ruff's isort integration
- **No Global Imports**: Use relative imports within modules

### pyproject.toml Configuration
- Black: line-length = 88
- Ruff: Default configuration with isort
- MyPy: Strict type checking enabled
- pytest: Coverage reporting configured

## Core Files & Structure

### Agent Structure Pattern
```
agents/{protocol}-{name}/
├── Dockerfile              # Container definition
├── README.md              # Agent documentation
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Project configuration
├── venv/                  # Virtual environment (DO NOT COMMIT)
├── src/                   # Source code
│   └── {module_name}/
│       ├── __init__.py
│       └── {agent}.py
└── tests/                 # Test suite
    ├── __init__.py
    └── test_{agent}.py
```

### Key Configuration Files
- `docker-compose.yml`: Service orchestration
- `agents/*/pyproject.toml`: Agent-specific Python config
- `scripts/test_all_agents.sh`: Master test runner
- `scripts/nginx.conf`: Proxy configuration

### Discovery & Routing
- **Tag-Based**: Agents advertise capabilities via tags
- **Protocol-Specific**: Each protocol has discovery strategy
- **Health Monitoring**: Continuous health checking
- **Registry Management**: Centralized agent registry

## Repository Guidelines

### Branch Naming
```
feat/feature-name       # New features
fix/bug-description     # Bug fixes
docs/update-name        # Documentation
refactor/component      # Code refactoring
test/test-description   # Test additions
```

### Commit Format
```
<type>(<scope>): <description>

# Types: feat, fix, docs, refactor, test, chore
# Examples:
feat(orchestrator): add MCP protocol support
fix(a2a): handle empty responses gracefully
test(discovery): add integration tests
docs(readme): update setup instructions
```

### PR Requirements
- All tests must pass
- Code formatted with Black
- No Ruff violations
- Type checking passes
- Documentation updated
- Commit messages follow convention

## Protocol Resources

### Official Documentation & SDKs
- **ACP Protocol**
  - Docs: https://docs.agntcy.org/
  - SDK: https://github.com/agntcy/acp-sdk
  - Python SDK Docs: https://agntcy.github.io/acp-sdk/html/index.html
  - Spec: https://spec.acp.agntcy.org/

- **A2A Protocol**
  - Website: https://a2a-protocol.org/
  - Specification: https://a2a-protocol.org/latest/specification/
  - Python SDK: https://github.com/a2aproject/a2a-python
  - SDK API Docs: https://a2a-protocol.org/latest/sdk/python/api/

- **MCP Protocol** (Coming Soon)
  - Spec: https://spec.modelcontextprotocol.io/

### Implementation Patterns
- Follow official SDK examples strictly
- Use protocol-specific discovery mechanisms
- Implement all required endpoints
- Include comprehensive health checks
- Add proper error handling

## Environment Variables

### Orchestrator
```bash
# LLM Configuration (Required for AI routing)
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional Configuration
export ORCHESTRATOR_DEBUG=true
export ORCHESTRATOR_LOG_LEVEL=DEBUG
export ORCHESTRATOR_PORT=8004
```

### A2A Math Agent
```bash
# Optional LLM fallback
export LLM_PROVIDER=openai
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GEMINI_API_KEY="..."
```

## Common Issues & Solutions

### Port Conflicts
```bash
# Check what's using a port
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process using port
kill -9 $(lsof -t -i:8000)  # macOS/Linux
```

### Docker Issues
```bash
# Clean rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Remove all containers and volumes
docker-compose down -v
docker system prune -a
```

### Python Path Issues
```bash
# Always set PYTHONPATH for local development
export PYTHONPATH=src  # For most agents
export PYTHONPATH=/app  # For A2A agent in Docker
```

### Virtual Environment Issues
```bash
# Recreate venv if corrupted
rm -rf venv/
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Quick Development Workflow

### 1. Start Development
```bash
# Start Docker services
docker-compose up -d

# Verify everything works
./scripts/test_all_agents.sh
```

### 2. Make Changes (ALWAYS in venv)
```bash
# Navigate to agent
cd agents/{agent-name}

# Activate venv
source venv/bin/activate

# Install dependencies if needed
pip install -r requirements.txt

# Make your changes
# ...

# Format and lint
black . && ruff check --fix .

# Run tests
python -m pytest tests/ -v
```

### 3. Test Integration
```bash
# Rebuild if needed
docker-compose build {service-name}
docker-compose up -d {service-name}

# Test the service
curl http://localhost:{port}/health

# Check logs
docker-compose logs -f {service-name}
```

### 4. Commit Changes
```bash
# Stage changes
git add .

# Commit with conventional format
git commit -m "feat(agent): add new capability"

# Push to feature branch
git push origin feat/new-capability
```

## Important Notes

1. **NEVER commit venv/ directories** - They're in .gitignore
2. **ALWAYS activate venv** before any Python operation
3. **ALWAYS set PYTHONPATH** for local development
4. **NEVER hardcode API keys** - Use environment variables
5. **ALWAYS run tests** before committing
6. **FOLLOW protocol specs** exactly - This is educational
7. **CHECK health endpoints** after changes
8. **USE Docker** for integration testing
9. **MAINTAIN test coverage** above 75%
10. **DOCUMENT your changes** in code and README

## Debugging Tips

### View Structured Logs
```bash
# Orchestrator decision logs
docker-compose logs orchestrator | grep -E "(LLM_|TOOL_CALL|DECISION)"

# A2A Math Agent operations
docker-compose logs a2a-math-agent | grep -E "(INFO|ERROR|DEBUG)"
```

### Test Specific Functionality
```bash
# Test orchestrator routing
curl -X POST "http://localhost:8004/route" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is 2 + 2?"}'

# Test agent discovery
curl "http://localhost:8004/agents"
curl "http://localhost:8004/agents?capability=math"
```

### Interactive Python Testing (in venv)
```python
# Test imports and functionality
cd agents/orchestrator
source venv/bin/activate
python
>>> from orchestrator.discovery import DiscoveryService
>>> from orchestrator.models import AgentInfo
>>> # Test your code interactively
```

---
**Remember**: This is an educational project. Always follow official protocol specifications and SDK patterns. When in doubt, consult the official documentation links above.