# Multi-Protocol Agent Orchestrator

A central hub for discovering and routing requests to specialized agents across multiple protocols (ACP, A2A, MCP).

## Features

- **Multi-Protocol Support**: Works with ACP, A2A, MCP, and custom protocols
- **Intelligent Routing**: Uses Pydantic AI with OpenAI/Anthropic for smart request routing
- **Dynamic Discovery**: Automatically discovers agents via Docker labels and protocol-specific methods
- **Fallback Support**: Multiple LLM providers and alternative agent routing
- **Production Ready**: Health checks, metrics, structured logging

## Quick Start

### Docker

```bash
docker build -t orchestrator-agent .
docker run -p 8000:8000 -p 9090:9090 orchestrator-agent
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the orchestrator
python -m uvicorn orchestrator.app:app --reload
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/route` | POST | Route request to appropriate agent |
| `/agents` | GET | List discovered agents |
| `/agents/{agent_id}` | GET | Get specific agent details |
| `/agents/refresh` | POST | Trigger agent discovery refresh |
| `/capabilities` | GET | Get orchestrator capabilities |
| `/metrics` | GET | Prometheus metrics (if enabled) |

## Configuration

See `.env.example` for all available configuration options. Key settings:

- `LLM_PROVIDER`: Choose between `openai`, `anthropic`, or `both`
- `OPENAI_API_KEY`: Your OpenAI API key
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `DISCOVERY_INTERVAL_SECONDS`: How often to discover agents
- `ENABLE_METRICS`: Enable Prometheus metrics

## Testing

```bash
# From the orchestrator directory
cd agents/orchestrator
PYTHONPATH=src python -m pytest tests --cov=src/orchestrator --cov-report=html

# Or from project root
PYTHONPATH=agents/orchestrator/src python -m pytest agents/orchestrator/tests

# Run specific test files
PYTHONPATH=src python -m pytest tests/test_config.py tests/test_models.py

# Alternative: Install in development mode first
pip install -e .
pytest tests --cov=src/orchestrator --cov-report=html
```

## Architecture

The orchestrator uses:
- **Pydantic AI** for intelligent routing decisions
- **FastAPI** for the REST API
- **Docker SDK** for agent discovery
- **Protocol-specific discovery strategies** for each supported protocol

## License

Apache 2.0