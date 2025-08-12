# 🚀 Quick Start Guide

Get the Agent Network Sandbox running in under 5 minutes!

## Prerequisites

- **Docker & Docker Compose** (required)
- **curl** (for testing)

That's it! Everything else runs in containers.

## 1. Clone & Start

```bash
# Clone the repository
git clone https://github.com/your-org/agent-net-sandbox.git
cd agent-net-sandbox

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

Expected output:
```
NAME                    IMAGE                      STATUS
agent-frontend          agent-frontend:latest      Up 30 seconds (healthy)
agent-orchestrator      agent-orchestrator         Up 30 seconds (healthy)
acp-hello-world-agent   acp-hello-world-agent      Up 30 seconds (healthy)
a2a-math-agent          a2a-math-agent:latest      Up 30 seconds (healthy)
agent-directory         nginx:alpine               Up 30 seconds 
```

## 2. Verify Everything Works

```bash
# Test the comprehensive test suite
./scripts/test_all_agents.sh
```

Expected output:
```
🧪 Multi-Protocol Agent Sandbox Test Suite
=============================================
✅ React Frontend Interface - Healthy
✅ Multi-Protocol Orchestrator - Healthy
✅ ACP Hello World Agent - Healthy
✅ A2A Math Agent - Healthy
✅ Agent Directory - Healthy
🎉 All systems operational!
```

## 3. Try the Frontend Chat Interface

The easiest way to experience the Agent Network Sandbox is through the React frontend:

### Open the Chat Interface
```bash
# Open in your browser
open http://localhost:3000
# Or visit: http://localhost:3000
```

**What you'll see:**
- Modern chat interface with real-time messaging
- AI routing transparency showing which agent was selected
- Live streaming responses as they're generated
- Smart retry mechanisms for failed messages

### Try Different Queries
Type these in the chat interface to see different agents in action:

```
Hello there!                    # → Routes to ACP Hello World Agent
What is 2 + 2?                 # → Routes to A2A Math Agent  
Calculate the square root of 16 # → Routes to A2A Math Agent
Say hello in Spanish           # → Routes to ACP Hello World Agent
```

## 4. Try the Orchestrator API Directly

You can also test the orchestrator API directly if you prefer:

### Basic Usage
```bash
# Simple greeting request
curl -X POST "http://localhost:8004/process" \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello there!"}'
```

Expected response:
```json
{
  "success": true,
  "agent_id": "acp-hello-world",
  "protocol": "acp",
  "response_data": {
    "message": "Response from hello-world",
    "query": "Hello there!",
    "timestamp": "2025-01-XX..."
  },
  "duration_ms": 1250.5
}
```

### See Available Agents
```bash
# List all discovered agents
curl "http://localhost:8004/agents"
```

### Check Agent Capabilities
```bash
# See what agents can do
curl "http://localhost:8004/capabilities"
```

## 5. Explore Individual Services

### React Frontend (Chat Interface)
- **Production**: http://localhost:3000 - Full-featured chat interface
- **Features**: Real-time streaming, AI routing transparency, message retry

### Agent Directory (Web UI) 
- **URL**: http://localhost:8080 - Traditional agent directory

### Individual Agent APIs
```bash
# ACP Hello World Agent
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{"input": {"name": "World", "language": "en"}}'

# A2A Math Agent  
curl -X POST "http://localhost:8002/" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send", 
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "What is 5 * 7?"}]
      }
    },
    "id": "test_123"
  }'
```

## 6. What's Next?

### 🎨 Explore Frontend Development
Try development mode with hot reload:

```bash
# Option 1: Frontend only in development mode
docker-compose stop frontend
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up frontend
# Frontend with hot reload at: http://localhost:5173

# Option 2: Everything in development mode (enhanced logging + hot reload)
docker-compose down
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
# All services in dev mode with enhanced debugging
```

### 📚 Learn More
- **[Frontend Tutorials](docs/tutorials/frontend/)** - 47 comprehensive React development guides
- **[Manual Setup Guide](MANUAL_SETUP.md)** - Detailed installation and development setup
- **[Contributing Guide](CONTRIBUTING.md)** - How to add new agents and protocols  
- **[Orchestrator Documentation](agents/orchestrator/README.md)** - Deep dive into the AI routing system

### 🧪 Try Advanced Features
Experiment with the orchestrator API:

```bash
# Test different routing scenarios
echo '{"query": "Say hello in Spanish"}' | curl -s -X POST http://localhost:8004/process -H "Content-Type: application/json" -d @-

echo '{"query": "What is the derivative of x^2?"}' | curl -s -X POST http://localhost:8004/process -H "Content-Type: application/json" -d @-
```

### 🆘 Troubleshooting

#### Services won't start?
```bash
# Check logs
docker-compose logs

# Restart everything
docker-compose down
docker-compose up -d
```

#### Port conflicts?
```bash
# Check what's using ports 8000, 8004, 8080
lsof -i :8000
lsof -i :8004
lsof -i :8080

# Stop conflicting services or modify docker-compose.yml ports
```

#### Frontend not loading?
```bash
# Check if frontend service is running
docker-compose logs frontend

# Try accessing directly
curl http://localhost:3000/health

# For development mode:
curl http://localhost:5173
```

#### Tests failing?
```bash
# Wait a moment for services to fully start
sleep 10
./scripts/test_all_agents.sh

# Check individual service health
curl http://localhost:3000/health  # Frontend
curl http://localhost:8004/health  # Orchestrator
curl http://localhost:8000/health  # ACP Agent
curl http://localhost:8002/.well-known/agent-card  # A2A Agent
```

### 🎯 Next Steps

1. **Add Your First Agent**: Follow the [Contributing Guide](CONTRIBUTING.md) to add support for a new protocol
2. **Experiment with Routing**: Try complex queries and see how the orchestrator decides which agent to use
3. **Build Something Cool**: Use the orchestrator API to build your own multi-agent applications

## 🎉 You're Ready!

The Agent Network Sandbox is now running and ready for experimentation. The orchestrator will intelligently route your requests to the most appropriate agents, and you can easily add new protocols and agents as needed.

Happy agent building! 🤖✨

---

**Need help?** Check the [full documentation](README.md) or open an [issue](https://github.com/your-org/agent-net-sandbox/issues).