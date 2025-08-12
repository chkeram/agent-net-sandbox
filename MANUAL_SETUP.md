# 🛠️ Manual Setup Guide

Comprehensive guide for local development, manual installation, and advanced configuration of the Agent Network Sandbox.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Orchestrator Development](#orchestrator-development)
- [Agent Development](#agent-development)
- [Configuration Management](#configuration-management)
- [Advanced Docker Setup](#advanced-docker-setup)
- [Platform-Specific Instructions](#platform-specific-instructions)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

#### Docker & Docker Compose
```bash
# macOS (using Homebrew)
brew install docker docker-compose

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io docker-compose-plugin

# CentOS/RHEL
sudo yum install docker docker-compose

# Windows
# Download Docker Desktop from https://www.docker.com/products/docker-desktop
```

#### Python 3.11+
```bash
# macOS (using Homebrew)
brew install python@3.11

# Ubuntu/Debian
sudo apt-get install python3.11 python3.11-venv python3.11-dev

# CentOS/RHEL
sudo yum install python311 python311-devel

# Windows
# Download from https://www.python.org/downloads/
```

#### Git
```bash
# macOS
brew install git

# Ubuntu/Debian
sudo apt-get install git

# CentOS/RHEL
sudo yum install git

# Windows
# Download from https://git-scm.com/
```

#### curl (for testing)
```bash
# macOS (usually pre-installed)
brew install curl

# Ubuntu/Debian
sudo apt-get install curl

# CentOS/RHEL
sudo yum install curl

# Windows (use PowerShell's Invoke-WebRequest or install curl)
```

### Optional Tools

#### Development Tools
```bash
# Code editor/IDE (choose one)
code .  # VS Code
pycharm .  # PyCharm
vim .  # Vim/Neovim

# Additional utilities
brew install jq httpie  # macOS
sudo apt-get install jq httpie  # Ubuntu
```

## Local Development Setup

### 1. Clone Repository
```bash
git clone https://github.com/your-org/agent-net-sandbox.git
cd agent-net-sandbox
```

### 2. Environment Setup

#### Option A: Full Docker Development (Recommended)
```bash
# Start development environment (includes frontend)
docker-compose up -d

# Verify services (including frontend)
docker-compose ps
./scripts/test_all_agents.sh

# Access frontend at: http://localhost:3000
```

#### Option B: Frontend Development Mode (Hot Reload)
```bash
# Start backend services only
docker-compose up -d orchestrator acp-hello-world a2a-math-agent agent-directory

# Start frontend in development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up frontend

# Frontend with hot reload at: http://localhost:5173
```

#### Option C: Full Development Mode (Everything in Dev Mode)
```bash
# Start all services in development mode with enhanced logging
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Benefits:
# - Frontend hot reload on port 5173
# - Enhanced orchestrator debugging (DEBUG log level)
# - Source code volume mounts for live editing
# - Development environment variables
```

#### Option D: Full Local Development (Frontend + Backend)
```bash
# Setup local development for all components
# Backend: See Orchestrator/Agent Development sections
# Frontend: See Frontend Development section below
```

## Orchestrator Development

The Multi-Protocol Agent Orchestrator is the core intelligence system.

### Local Development Setup

#### 1. Navigate to Orchestrator Directory
```bash
cd agents/orchestrator
```

#### 2. Create Virtual Environment
```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

#### 3. Install Dependencies
```bash
# Install development dependencies
pip install --upgrade pip
pip install -r requirements-dev.txt

# Install main dependencies
pip install -r requirements.txt
```

#### 4. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
vim .env  # or your preferred editor
```

Required configuration:
```env
# LLM Provider (choose one)
ORCHESTRATOR_LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key-here

# OR
ORCHESTRATOR_LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Application settings
ORCHESTRATOR_HOST=0.0.0.0
ORCHESTRATOR_PORT=8004
ORCHESTRATOR_ENVIRONMENT=development
ORCHESTRATOR_DEBUG=true
ORCHESTRATOR_LOG_LEVEL=DEBUG
```

#### 5. Run Tests
```bash
# Run all tests
PYTHONPATH=src python -m pytest tests/ -v

# Run with coverage
PYTHONPATH=src python -m pytest tests/ --cov=src/orchestrator --cov-report=html

# Run specific test files
PYTHONPATH=src python -m pytest tests/test_discovery.py -v
```

#### 6. Start Development Server
```bash
# Start with hot reload
PYTHONPATH=src python -m orchestrator.main

# Or using uvicorn directly
PYTHONPATH=src uvicorn orchestrator.main:app --reload --host 0.0.0.0 --port 8004
```

#### 7. Development Workflow
```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type check
mypy src/

# Run tests
PYTHONPATH=src python -m pytest tests/ -v

# Start development server
PYTHONPATH=src python -m orchestrator.main
```

### Advanced Orchestrator Configuration

#### Multiple LLM Providers
```env
# Primary provider
ORCHESTRATOR_LLM_PROVIDER=openai
OPENAI_API_KEY=your-key

# Backup provider (for fallback)
ANTHROPIC_API_KEY=your-backup-key
```

#### Discovery Configuration
```env
# Discovery settings
ORCHESTRATOR_DISCOVERY_INTERVAL_SECONDS=30
ORCHESTRATOR_DISCOVERY_TIMEOUT_SECONDS=5

# Health check configuration
ORCHESTRATOR_ROUTING_TIMEOUT_SECONDS=30.0
ORCHESTRATOR_MAX_RETRIES=3
ORCHESTRATOR_RETRY_DELAY_SECONDS=1.0
```

#### Performance Tuning
```env
# Production settings
ORCHESTRATOR_WORKERS=4
ORCHESTRATOR_ENVIRONMENT=production
ORCHESTRATOR_DEBUG=false
ORCHESTRATOR_LOG_LEVEL=INFO
```

## Frontend Development

The React Frontend provides a modern chat interface with real-time streaming and advanced UX features.

### Local Frontend Development Setup

#### 1. Prerequisites
```bash
# Node.js 18+ and npm (check versions)
node --version  # Should be 18+
npm --version   # Should be 8+

# If Node.js is not installed:
# macOS: brew install node
# Ubuntu: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs
# Windows: Download from https://nodejs.org/
```

#### 2. Navigate to Frontend Directory
```bash
cd frontend
```

#### 3. Install Dependencies
```bash
# Install all dependencies
npm install

# Verify installation
npm list --depth=0
```

#### 4. Environment Configuration
```bash
# Create environment file (optional)
cp .env.example .env

# Edit configuration if needed
vim .env
```

**Environment variables:**
```env
# Backend API URL (adjust if orchestrator runs elsewhere)
VITE_API_BASE_URL=http://localhost:8004

# Application configuration
VITE_APP_TITLE=Agent Network Sandbox
VITE_APP_VERSION=1.0.0

# Development settings
NODE_ENV=development
```

#### 5. Start Development Server
```bash
# Start Vite development server with hot reload
npm run dev

# Server will start at: http://localhost:5173
# Hot reload: Changes to source files will trigger automatic refresh
```

#### 6. Development Workflow
```bash
# Format code
npm run lint

# Type checking
npm run build  # This runs TypeScript compilation

# Build for production
npm run build
npm run preview  # Preview production build locally
```

### Frontend Architecture

#### Project Structure
```
frontend/
├── src/
│   ├── components/           # React components
│   │   ├── Chat/            # Chat interface components
│   │   │   ├── ChatContainer.tsx          # Basic chat container
│   │   │   ├── StreamingChatContainer.tsx # Advanced streaming container
│   │   │   ├── MessageList.tsx           # Message list with auto-scroll
│   │   │   ├── Message.tsx               # Individual message component
│   │   │   ├── ChatInput.tsx             # Message input with shortcuts
│   │   │   └── RoutingReasoning.tsx      # AI routing transparency
│   │   └── Layout/          # Layout components
│   ├── hooks/               # Custom React hooks
│   │   ├── useOrchestrator.ts           # Basic API integration
│   │   └── useStreamingOrchestrator.ts  # Advanced streaming with SSE
│   ├── services/            # API service layer
│   │   ├── orchestratorApi.ts          # Main orchestrator API
│   │   └── streamingApi.ts             # Streaming API with SSE
│   ├── types/               # TypeScript definitions
│   │   ├── chat.ts         # Chat-related types
│   │   └── agent.ts        # Agent-related types
│   └── utils/              # Utility functions
├── public/                 # Static assets
├── Dockerfile             # Container definition
├── nginx.conf            # Production nginx config
├── package.json          # Dependencies and scripts
├── vite.config.ts       # Vite configuration
├── tailwind.config.js   # Tailwind CSS configuration
└── tsconfig.json        # TypeScript configuration
```

#### Key Technologies
- **React 18** with functional components and hooks
- **TypeScript** for type safety and better development experience
- **Vite** for fast development server and optimized builds
- **Tailwind CSS** for utility-first styling
- **Server-Sent Events (SSE)** for real-time streaming
- **react-markdown** with syntax highlighting for message rendering

### Development Tips

#### Working with the API
```typescript
// The frontend expects the orchestrator to be running on port 8004
// Start backend services:
docker-compose up -d orchestrator acp-hello-world a2a-math-agent

// Test API connection:
curl http://localhost:8004/health
```

#### Hot Reload Development
```bash
# Frontend changes are reflected immediately
# Backend changes require service restart:
docker-compose restart orchestrator
```

#### Debugging
```bash
# View frontend logs
npm run dev  # Shows Vite logs and React errors

# View network requests in browser DevTools
# Check Console tab for JavaScript errors
# Use React DevTools extension for component debugging
```

#### Testing the Chat Interface
1. Start backend services: `docker-compose up -d orchestrator acp-hello-world a2a-math-agent`
2. Start frontend: `npm run dev`
3. Open http://localhost:5173
4. Try these test messages:
   - "Hello there!" → Should route to ACP Hello World Agent
   - "What is 2 + 2?" → Should route to A2A Math Agent
   - "Calculate 15 * 7" → Should route to A2A Math Agent

### Production Build

#### Build and Deploy
```bash
# Create production build
npm run build

# Test production build locally
npm run preview

# Build Docker image
docker build -t agent-frontend:local .

# Run production container
docker run -p 3000:80 agent-frontend:local
```

#### Docker Integration
```bash
# Build production image
docker-compose build frontend

# Run production container
docker-compose up -d frontend

# Access at: http://localhost:3000
```

### Troubleshooting Frontend Issues

#### Node.js/npm Issues
```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check for version conflicts
npm list
```

#### Build Issues
```bash
# TypeScript errors
npm run build  # Shows detailed TypeScript errors

# Vite build issues
rm -rf dist node_modules
npm install
npm run build
```

#### API Connection Issues
```bash
# Verify backend is running
curl http://localhost:8004/health

# Check CORS issues in browser DevTools
# Ensure VITE_API_BASE_URL is correct in .env

# Test direct API call
curl -X POST "http://localhost:8004/process" \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello test"}'
```

## Agent Development

### ACP Agent Development

#### 1. Navigate to Agent Directory
```bash
cd agents/acp-hello-world
```

#### 2. Local Development Setup
```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

#### 3. Run Locally
```bash
# Set Python path
export PYTHONPATH=src

# Start with hot reload
python -m uvicorn hello_agent.app:app --reload --host 0.0.0.0 --port 8000

# Or run directly
python -m hello_agent.app
```

#### 4. Test Agent
```bash
# Health check
curl http://localhost:8000/health

# Invoke agent
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{"input": {"name": "Developer", "language": "en"}}'

# Get capabilities
curl http://localhost:8000/capabilities
```

### Creating New Agents

#### 1. Use Agent Template
```bash
# Copy template
mkdir -p agents/my-new-agent
cp -r templates/agent-template/* agents/my-new-agent/
cd agents/my-new-agent
```

#### 2. Implement Agent Logic
```python
# src/my_agent/app.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="My Agent")

class HealthResponse(BaseModel):
    status: str
    timestamp: float

@app.get("/health")
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        timestamp=time.time()
    )

# Implement your agent-specific endpoints
```

#### 3. Configure Docker
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "my_agent.app"]
```

#### 4. Add to Docker Compose
```yaml
# Add to docker-compose.yml
my-new-agent:
  build:
    context: ./agents/my-new-agent
    dockerfile: Dockerfile
  ports:
    - "8005:8000"  # Use next available port
  networks:
    - agent-network
  labels:
    - "agent.protocol=my-protocol"
    - "agent.type=example"
```

## Configuration Management

### Environment Files

#### Project Structure
```
agent-net-sandbox/
├── .env.example                 # Template for root config
├── agents/
│   ├── orchestrator/
│   │   ├── .env                # Orchestrator-specific config
│   │   └── .env.example        # Orchestrator template
│   └── acp-hello-world/
│       └── .env.example        # Agent template
```

#### Configuration Hierarchy
1. Environment variables
2. `.env` files (agent-specific)
3. Default values in code

#### Orchestrator Configuration Options

```env
# Application Settings
ORCHESTRATOR_APP_NAME="Multi-Protocol Agent Orchestrator"
ORCHESTRATOR_HOST=0.0.0.0
ORCHESTRATOR_PORT=8004
ORCHESTRATOR_WORKERS=1
ORCHESTRATOR_ENVIRONMENT=development  # development|staging|production
ORCHESTRATOR_DEBUG=false

# LLM Provider Configuration
ORCHESTRATOR_LLM_PROVIDER=openai  # openai|anthropic
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
ORCHESTRATOR_DEFAULT_MODEL_TEMPERATURE=0.7

# OpenAI Specific
ORCHESTRATOR_OPENAI_MODEL=gpt-4o
ORCHESTRATOR_OPENAI_MAX_TOKENS=4096
ORCHESTRATOR_OPENAI_TIMEOUT=30.0

# Anthropic Specific
ORCHESTRATOR_ANTHROPIC_MODEL=claude-3-5-sonnet-20240620
ORCHESTRATOR_ANTHROPIC_MAX_TOKENS=4096
ORCHESTRATOR_ANTHROPIC_TIMEOUT=30.0

# Discovery Settings
ORCHESTRATOR_DISCOVERY_INTERVAL_SECONDS=30
ORCHESTRATOR_DISCOVERY_TIMEOUT_SECONDS=5

# Routing Settings
ORCHESTRATOR_ROUTING_TIMEOUT_SECONDS=30.0
ORCHESTRATOR_MAX_RETRIES=3
ORCHESTRATOR_RETRY_DELAY_SECONDS=1.0
ORCHESTRATOR_ENABLE_FALLBACK_ROUTING=true

# Monitoring
ORCHESTRATOR_ENABLE_METRICS=true
ORCHESTRATOR_METRICS_PORT=9090
ORCHESTRATOR_LOG_LEVEL=INFO  # DEBUG|INFO|WARNING|ERROR|CRITICAL
ORCHESTRATOR_STRUCTURED_LOGGING=true

# Security
ORCHESTRATOR_CORS_ORIGINS=*
ORCHESTRATOR_CORS_METHODS=GET,POST,PUT,DELETE
ORCHESTRATOR_CORS_HEADERS=*
```

## Advanced Docker Setup

### Custom Docker Configuration

#### Development Docker Compose
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  orchestrator:
    build:
      context: ./agents/orchestrator
      dockerfile: Dockerfile
      target: development  # Use development stage
    volumes:
      - ./agents/orchestrator/src:/app/src  # Mount source for hot reload
      - ./agents/orchestrator/.env:/app/.env
    environment:
      - ORCHESTRATOR_DEBUG=true
      - ORCHESTRATOR_LOG_LEVEL=DEBUG
    ports:
      - "8004:8004"

# Use with: docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

#### Production Docker Compose
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  orchestrator:
    image: agent-orchestrator:latest
    restart: unless-stopped
    environment:
      - ORCHESTRATOR_ENVIRONMENT=production
      - ORCHESTRATOR_DEBUG=false
      - ORCHESTRATOR_WORKERS=4
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

### Multi-Architecture Builds

```bash
# Build for multiple architectures
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 -t agent-orchestrator:latest .
```

### Container Optimization

#### Multi-Stage Dockerfile Example
```dockerfile
# Build stage
FROM python:3.11-slim as builder
WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# Runtime stage
FROM python:3.11-slim
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache /wheels/* && rm -rf /wheels
COPY --chown=appuser:appuser src/ ./src/
USER appuser
EXPOSE 8000
CMD ["python", "-m", "app"]
```

## Platform-Specific Instructions

### macOS

#### Prerequisites
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install docker docker-compose python@3.11 git curl jq
```

#### Docker Desktop Setup
1. Download Docker Desktop from https://www.docker.com/products/docker-desktop
2. Install and start Docker Desktop
3. Verify installation: `docker version`

#### Common macOS Issues
- **M1/M2 Macs**: Some Docker images may need `--platform linux/amd64`
- **Port conflicts**: Check if ports are in use: `lsof -i :8000`

### Ubuntu/Debian Linux

#### Prerequisites
```bash
# Update package index
sudo apt-get update

# Install Docker
sudo apt-get install docker.io docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install Python and tools
sudo apt-get install python3.11 python3.11-venv python3.11-dev
sudo apt-get install git curl jq build-essential
```

#### System Configuration
```bash
# Enable Docker service
sudo systemctl enable docker
sudo systemctl start docker

# Verify installation
docker version
docker-compose version
```

### Windows

#### Prerequisites
1. **Docker Desktop**: Download and install from https://www.docker.com/products/docker-desktop
2. **Python 3.11+**: Download from https://www.python.org/downloads/
3. **Git**: Download from https://git-scm.com/
4. **Windows Subsystem for Linux (WSL2)**: Recommended for better performance

#### WSL2 Setup (Recommended)
```bash
# Install WSL2
wsl --install

# Set WSL2 as default
wsl --set-default-version 2

# Install Ubuntu in WSL2
wsl --install -d Ubuntu

# Use Ubuntu terminal for development
```

#### PowerShell Commands
```powershell
# Clone repository
git clone https://github.com/your-org/agent-net-sandbox.git
cd agent-net-sandbox

# Start services
docker-compose up -d

# Test (using Invoke-WebRequest instead of curl)
Invoke-WebRequest -Uri "http://localhost:8004/health" -Method GET
```

### CentOS/RHEL

#### Prerequisites
```bash
# Install Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Install Python and tools
sudo yum install python311 python311-devel git curl
```

## Troubleshooting

### Common Issues

#### Docker Issues

**Service won't start**
```bash
# Check logs
docker-compose logs [service-name]

# Restart service
docker-compose restart [service-name]

# Rebuild and restart
docker-compose build [service-name]
docker-compose up -d [service-name]
```

**Port already in use**
```bash
# Find process using port
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process or change port in docker-compose.yml
```

**Permission denied (Linux)**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Or run with sudo (not recommended)
sudo docker-compose up -d
```

#### Python Issues

**Module not found**
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=src

# Verify Python path
python -c "import sys; print(sys.path)"

# Reinstall dependencies
pip install -r requirements.txt
```

**Virtual environment issues**
```bash
# Remove and recreate venv
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### API Issues

**Connection refused**
```bash
# Check if service is running
docker-compose ps

# Check service logs
docker-compose logs orchestrator

# Verify network connectivity
docker network ls
docker network inspect agent-net-sandbox_agent-network
```

**Authentication errors**
```bash
# Verify API keys in .env
cat agents/orchestrator/.env

# Test API key separately
curl -H "Authorization: Bearer YOUR_API_KEY" https://api.openai.com/v1/models
```

### Debug Mode

#### Enable Debug Logging
```env
# In .env file
ORCHESTRATOR_DEBUG=true
ORCHESTRATOR_LOG_LEVEL=DEBUG
```

#### Container Debugging
```bash
# Enter container
docker exec -it agent-orchestrator /bin/bash

# View logs in real-time
docker-compose logs -f orchestrator

# Check container resources
docker stats
```

#### Network Debugging
```bash
# Test internal network connectivity
docker exec agent-orchestrator curl http://acp-hello-world-agent:8000/health

# Check DNS resolution
docker exec agent-orchestrator nslookup acp-hello-world-agent

# Inspect network
docker network inspect agent-net-sandbox_agent-network
```

### Performance Issues

#### Resource Monitoring
```bash
# Check container resources
docker stats

# Check host resources
htop  # or top on macOS
df -h  # disk usage
```

#### Optimization Tips
- Increase Docker memory allocation
- Use production-optimized Docker images
- Enable Docker BuildKit for faster builds
- Use volume mounts instead of copying files during development

### Getting Help

1. **Check the logs**: `docker-compose logs`
2. **Review configuration**: Verify `.env` files
3. **Test components individually**: Use direct API calls
4. **Check GitHub issues**: Search for similar problems
5. **Create an issue**: Provide logs, configuration, and steps to reproduce

---

This manual setup guide should help you get the Agent Network Sandbox running in any environment. For quick setup, see the [Quick Start Guide](QUICK_START.md).