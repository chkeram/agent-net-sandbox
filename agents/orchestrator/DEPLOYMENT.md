# Multi-Protocol Agent Orchestrator - Deployment Guide

This guide covers deployment options for the Multi-Protocol Agent Orchestrator, from local development to production environments.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Git
- OpenAI or Anthropic API key

### 1. Clone and Setup

```bash
git clone <repository-url>
cd agent-net-sandbox/agents/orchestrator
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys
vim .env  # or your preferred editor
```

**Required Environment Variables:**
```bash
OPENAI_API_KEY=your-openai-api-key-here
# OR
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

### 3. Deploy with Docker Compose

```bash
# From repository root
cd ../../
./agents/orchestrator/scripts/deploy.sh start
```

The orchestrator will be available at:
- **API**: http://localhost:8004
- **Documentation**: http://localhost:8004/docs
- **Health Check**: http://localhost:8004/health

## 📋 Deployment Options

### Option 1: Docker Compose (Recommended)

**Advantages:**
- Complete multi-agent environment
- Service orchestration and networking
- Volume management and persistence
- Easy scaling and management

**Steps:**
```bash
# Build and start all services
docker-compose up -d

# Or start only the orchestrator
docker-compose up -d orchestrator

# View logs
docker-compose logs -f orchestrator

# Stop services
docker-compose down
```

### Option 2: Standalone Docker Container

**Advantages:**
- Lightweight deployment
- Direct container management
- Custom networking options

**Steps:**
```bash
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

# View logs
docker logs -f orchestrator
```

### Option 3: Local Development

**Advantages:**
- Hot reload for development
- Direct Python debugging
- No containerization overhead

**Steps:**
```bash
# Install dependencies
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-key"
export ORCHESTRATOR_LLM_PROVIDER=openai

# Start development server
./scripts/dev.sh
```

## 🔧 Configuration

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ORCHESTRATOR_HOST` | `0.0.0.0` | Host address to bind |
| `ORCHESTRATOR_PORT` | `8004` | Port to listen on |
| `ORCHESTRATOR_ENVIRONMENT` | `production` | Environment mode |
| `ORCHESTRATOR_LOG_LEVEL` | `INFO` | Logging level |

### LLM Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ORCHESTRATOR_LLM_PROVIDER` | `openai` | LLM provider (`openai`, `anthropic`) |
| `OPENAI_API_KEY` | - | OpenAI API key |
| `ANTHROPIC_API_KEY` | - | Anthropic API key |
| `ORCHESTRATOR_DEFAULT_MODEL_TEMPERATURE` | `0.7` | Model temperature (0.0-2.0) |

### Discovery Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ORCHESTRATOR_DISCOVERY_INTERVAL_SECONDS` | `30` | Agent discovery interval |
| `ORCHESTRATOR_DOCKER_NETWORK` | `agent-network` | Docker network for discovery |
| `ORCHESTRATOR_DOCKER_SOCKET_PATH` | `/var/run/docker.sock` | Docker socket path |

### Complete Configuration

See [`.env.example`](.env.example) for all available configuration options.

## 🐳 Docker Configuration

### Multi-Stage Build

The Dockerfile uses a multi-stage build for optimized production images:

1. **Builder Stage**: Compiles Python wheels
2. **Production Stage**: Minimal runtime image

### Container Labels

The orchestrator container includes labels for service discovery:

```dockerfile
LABEL agent.protocol="orchestrator"
LABEL agent.type="orchestrator" 
LABEL agent.name="Multi-Protocol Agent Orchestrator"
LABEL agent.version="0.1.0"
LABEL agent.capabilities="routing,discovery,management"
```

### Volume Mounts

| Mount | Purpose | Required |
|-------|---------|----------|
| `/var/run/docker.sock` | Agent discovery | Yes |
| `/app/logs` | Persistent logging | Optional |
| `/app/data` | Application data | Optional |

## 🔍 Health Monitoring

### Health Check Endpoint

```bash
curl http://localhost:8004/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2025-01-15T10:30:00Z",
  "services": {
    "orchestrator": "healthy",
    "discovery_service": "healthy",
    "llm_provider": "openai"
  }
}
```

### System Status

```bash
curl http://localhost:8004/status
```

**Response:**
```json
{
  "status": "healthy",
  "orchestrator_healthy": true,
  "discovery_service_healthy": true,
  "total_agents": 2,
  "healthy_agents": 2,
  "protocols_supported": ["acp", "orchestrator"]
}
```

### Docker Health Check

The container includes a built-in health check:

```bash
# Check container health
docker ps --filter name=orchestrator

# View health check logs
docker inspect orchestrator --format='{{.State.Health.Status}}'
```

## 📊 Monitoring and Logging

### Application Logs

```bash
# Docker Compose
docker-compose logs -f orchestrator

# Standalone Docker
docker logs -f orchestrator

# Local development
tail -f logs/orchestrator.log
```

### Structured Logging

Logs are structured in JSON format for easy parsing:

```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "info",
  "logger": "orchestrator.agent",
  "message": "Request routed successfully",
  "query": "Say hello to me",
  "selected_agent": "acp-greeting-agent",
  "confidence": 0.95,
  "duration_ms": 150.2
}
```

### Metrics Endpoint

```bash
curl http://localhost:8004/metrics
```

## 🔒 Security Considerations

### API Keys

- Store API keys in environment variables or secrets management
- Never commit API keys to version control
- Use different keys for development and production

### Container Security

- Runs as non-root user (`orchestrator`)
- Minimal base image (Python slim)
- Read-only Docker socket mount for discovery

### Network Security

- Configure CORS origins for production
- Use HTTPS in production environments
- Restrict Docker network access as needed

## 🚦 Production Deployment

### Environment Setup

```bash
# Production environment variables
ORCHESTRATOR_ENVIRONMENT=production
ORCHESTRATOR_DEBUG=false
ORCHESTRATOR_LOG_LEVEL=INFO
ORCHESTRATOR_CORS_ORIGINS=https://your-domain.com
```

### Docker Compose Override

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  orchestrator:
    restart: always
    environment:
      - ORCHESTRATOR_ENVIRONMENT=production
      - ORCHESTRATOR_DEBUG=false
      - ORCHESTRATOR_CORS_ORIGINS=https://your-domain.com
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

Deploy with:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Load Balancing

For high availability, deploy multiple orchestrator instances:

```yaml
version: '3.8'

services:
  orchestrator:
    scale: 3
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

## 🛠️ Troubleshooting

### Common Issues

**1. Container Won't Start**
```bash
# Check logs
docker-compose logs orchestrator

# Common causes:
# - Missing API keys
# - Port conflicts
# - Docker socket permissions
```

**2. Agent Discovery Issues**
```bash
# Check Docker socket mount
docker-compose exec orchestrator ls -la /var/run/docker.sock

# Verify network connectivity
docker-compose exec orchestrator curl http://acp-hello-world:8000/health
```

**3. LLM Provider Errors**
```bash
# Verify API key
docker-compose exec orchestrator env | grep API_KEY

# Check provider configuration
curl http://localhost:8004/health
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Environment variable
ORCHESTRATOR_DEBUG=true
ORCHESTRATOR_LOG_LEVEL=DEBUG

# Or restart with debug
docker-compose restart orchestrator
```

### Log Analysis

```bash
# Filter error logs
docker-compose logs orchestrator | grep ERROR

# Search for specific agent
docker-compose logs orchestrator | grep "acp-greeting-agent"

# Monitor real-time
docker-compose logs -f --tail=100 orchestrator
```

## 📚 Additional Resources

- [API Documentation](http://localhost:8004/docs) - Interactive API docs
- [Configuration Reference](.env.example) - Complete environment variables
- [Development Guide](README.md) - Local development setup
- [Agent Discovery Guide](../README.md) - Multi-agent ecosystem

## 🆘 Support

For deployment issues:

1. Check the [troubleshooting section](#troubleshooting)
2. Review logs for error messages
3. Verify configuration settings
4. Check container and network status
5. Create an issue with logs and configuration details