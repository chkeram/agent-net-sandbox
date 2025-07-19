# AGNTCY Hello World Agent

A simple "hello world" agent implementation using the [AGNTCY Internet of Agents](https://agntcy.org) protocol and the [Agent Connect Protocol (ACP)](https://spec.acp.agntcy.org/).

This project demonstrates how to build, deploy, and test an agent that is fully compliant with the AGNTCY IoA ecosystem, including discovery mechanisms and Docker containerization.

## 🎯 Features

- ✅ **Full ACP Compliance**: Implements all required ACP endpoints
- 🌍 **Multi-language Support**: Greetings in English, Spanish, French, German, and Italian
- 🐳 **Docker Ready**: Complete containerization with Docker Compose
- 🔍 **Discovery Integration**: Agent manifest and ACP descriptor for discoverability
- 📡 **Streaming Support**: Server-sent events for real-time responses
- 🧪 **Testing Suite**: CLI client and automated testing scripts
- 📚 **Comprehensive Documentation**: API examples and usage guides

## 🏗️ Architecture

```
├── src/hello_agent/          # Main agent implementation
│   ├── __init__.py          # Package initialization
│   ├── app.py               # FastAPI application with ACP endpoints
│   ├── agent.py             # Core agent logic
│   ├── models.py            # Pydantic data models
│   ├── cli.py               # ACP SDK CLI client
│   └── simple_cli.py        # Simple HTTP CLI client
├── agent-manifest.yaml      # AGNTCY Agent Manifest
├── acp-descriptor.json      # ACP Descriptor for discovery
├── Dockerfile               # Container image definition
├── docker-compose.yml       # Multi-service deployment
├── scripts/                 # Testing and utility scripts
└── docs/                    # Additional documentation
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- curl (for testing)

### Option 1: Docker Compose (Recommended)

1. **Clone and navigate to the project:**
   ```bash
   git clone <repository-url>
   cd agent-net-sandbox
   ```

2. **Start the agent:**
   ```bash
   docker-compose up -d
   ```

3. **Test the agent:**
   ```bash
   curl -X POST "http://localhost:8000/hello" \
     -H "Content-Type: application/json" \
     -d '{"name": "AGNTCY", "language": "en"}'
   ```

4. **View the agent directory:**
   Open http://localhost:8080 in your browser

### Option 2: Local Development

1. **Set up Python environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run the agent:**
   ```bash
   export PYTHONPATH=src
   python -m uvicorn hello_agent.app:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Test the agent:**
   ```bash
   python -m hello_agent.simple_cli test
   ```

## 📋 Agent Connect Protocol (ACP) Endpoints

The agent implements all required ACP endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth` | GET | Authentication information |
| `/schema` | GET | JSON schemas for input/output/config |
| `/config` | POST | Create and store agent configuration |
| `/invoke` | POST | Execute agent with input data |
| `/capabilities` | GET | Agent capabilities and metadata |

### Additional Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Agent information and available endpoints |
| `/health` | GET | Health check status |
| `/hello` | POST | Direct hello endpoint (non-ACP) |
| `/agent-info` | GET | Comprehensive agent metadata |

## 🌍 Usage Examples

### Basic Hello World

```bash
# English greeting
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{"input": {"name": "World", "language": "en"}}'

# Spanish greeting  
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{"input": {"name": "Mundo", "language": "es"}}'

# Custom message
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{"input": {"name": "Developer", "message": "Welcome to AGNTCY"}}'
```

### Agent Configuration

```bash
# Create custom configuration
curl -X POST "http://localhost:8000/config" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "agent_name": "Custom Hello Agent",
      "default_language": "fr",
      "custom_greetings": {
        "en": "Hi there",
        "fr": "Salut"
      }
    }
  }'
```

### Streaming Response

```bash
# Get streaming response
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{"input": {"name": "Stream", "language": "en"}, "stream": true}'
```

## 🧪 Testing

### Automated Test Suite

```bash
# Run comprehensive API tests
./scripts/test_api.sh

# Test specific endpoint
./scripts/test_api.sh http://localhost:8000
```

### CLI Testing

```bash
# Using the simple CLI client
python -m hello_agent.simple_cli health
python -m hello_agent.simple_cli info  
python -m hello_agent.simple_cli hello --name "CLI User" --language "es"
python -m hello_agent.simple_cli test

# Using custom host/port
python -m hello_agent.simple_cli --host remote-host --port 8080 test
```

### Manual Testing

```bash
# Check agent health
curl http://localhost:8000/health

# Get agent capabilities
curl http://localhost:8000/capabilities

# Get authentication info
curl http://localhost:8000/auth

# Get schemas
curl http://localhost:8000/schema
```

## 🐳 Docker Deployment

### Building the Image

```bash
# Build the agent image
docker build -t hello-world-agent:latest .

# Run the container
docker run -p 8000:8000 hello-world-agent:latest
```

### Docker Compose Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f hello-world-agent

# Stop services
docker-compose down
```

The Docker Compose setup includes:
- **hello-world-agent**: Main agent service (port 8000)
- **agent-directory**: Mock discovery service (port 8001)

## 🔍 AGNTCY Discovery Integration

The agent includes full discovery integration:

### Agent Manifest (`agent-manifest.yaml`)
- Defines agent metadata, capabilities, and deployment configuration
- Specifies resource requirements and dependencies
- Enables discovery through AGNTCY Agent Directory

### ACP Descriptor (`acp-descriptor.json`)
- Machine-readable agent description
- Protocol endpoint definitions
- Capability schemas and authentication requirements

### Discovery Features
- **Keywords**: greeting, hello, multilingual, demo
- **Categories**: communication, demo
- **Capabilities**: generate_greeting, multilingual support, streaming
- **Languages**: en, es, fr, de, it

## 📊 Supported Languages

| Language | Code | Greeting |
|----------|------|----------|
| English | en | Hello |
| Spanish | es | Hola |
| French | fr | Bonjour |
| German | de | Hallo |
| Italian | it | Ciao |

## 🛠️ Development

### Project Structure

```
agent-net-sandbox/
├── src/hello_agent/           # Main application code
├── tests/                     # Test files (optional)
├── scripts/                   # Utility scripts
├── docs/                      # Documentation
├── agent-manifest.yaml        # AGNTCY manifest
├── acp-descriptor.json        # ACP descriptor
├── Dockerfile                 # Container definition
├── docker-compose.yml         # Multi-service setup
├── requirements.txt           # Python dependencies
├── pyproject.toml            # Project configuration
└── README.md                 # This file
```

### Adding New Features

1. **Extend the Agent Logic**: Modify `src/hello_agent/agent.py`
2. **Update Data Models**: Add new schemas in `src/hello_agent/models.py`
3. **Add API Endpoints**: Extend `src/hello_agent/app.py`
4. **Update Manifest**: Modify `agent-manifest.yaml` and `acp-descriptor.json`
5. **Add Tests**: Create test cases in `scripts/test_api.sh`

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8000 | Server port |
| `HOST` | 0.0.0.0 | Server host |
| `PYTHONPATH` | src | Python module path |

## 📈 Monitoring and Health

### Health Check
- **Endpoint**: `/health`
- **Method**: GET
- **Docker**: Built-in health check every 30s
- **Response**: `{"status": "healthy", "timestamp": <unix_timestamp>}`

### Logs
```bash
# View container logs
docker-compose logs -f hello-world-agent

# View Python logs (local development)
python -m uvicorn hello_agent.app:app --log-level info
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request

## 📝 License

This project is licensed under the Apache 2.0 License - see the LICENSE file for details.

## 🔗 Links

- [AGNTCY Internet of Agents](https://agntcy.org)
- [Agent Connect Protocol Specification](https://spec.acp.agntcy.org/)
- [AGNTCY Documentation](https://docs.agntcy.org)
- [AGNTCY GitHub](https://github.com/agntcy)

## 🐛 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using port 8000
   lsof -i :8000
   
   # Use different port
   docker-compose up -d -e PORT=8080
   ```

2. **Permission Denied (Docker)**
   ```bash
   # Add user to docker group
   sudo usermod -aG docker $USER
   
   # Or run with sudo
   sudo docker-compose up -d
   ```

3. **Module Not Found**
   ```bash
   # Ensure PYTHONPATH is set
   export PYTHONPATH=src
   
   # Or install in development mode
   pip install -e .
   ```

4. **Agent Not Responding**
   ```bash
   # Check agent health
   curl http://localhost:8000/health
   
   # Check Docker logs
   docker-compose logs hello-world-agent
   ```

### Getting Help

- Check the [example requests](scripts/example_requests.md)
- Run the test suite: `./scripts/test_api.sh`
- Review container logs: `docker-compose logs -f`
- Open an issue on GitHub

## 🎉 Success!

If you've made it this far, you should have a fully functional AGNTCY-compliant hello world agent running in Docker! 

Try visiting:
- http://localhost:8000 - Agent API
- http://localhost:8000/docs - OpenAPI documentation  
- http://localhost:8001 - Mock agent directory

Happy agent building! 🤖✨