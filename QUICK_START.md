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
acp-hello-world-agent   acp-hello-world-agent      Up 30 seconds (healthy)
agent-directory         nginx:alpine               Up 30 seconds 
agent-orchestrator      agent-orchestrator         Up 30 seconds (healthy)
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
✅ ACP Hello World Agent - Healthy
✅ Agent Orchestrator - Healthy
✅ Agent Directory - Healthy
🎉 All systems operational!
```

## 3. Try the Orchestrator

The orchestrator is the "brain" that routes requests to appropriate agents.

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

## 4. Explore Individual Agents

### ACP Hello World Agent
```bash
# Direct agent communication
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{"input": {"name": "World", "language": "en"}}'
```

### Agent Directory (Web UI)
Open in your browser: http://localhost:8080

## 5. What's Next?

### 🧪 Experiment with the Orchestrator
Try different queries to see how the AI routing works:

```bash
# Different types of requests
echo '{"query": "Say hello in Spanish"}' | curl -s -X POST http://localhost:8004/process -H "Content-Type: application/json" -d @-

echo '{"query": "Greet me nicely"}' | curl -s -X POST http://localhost:8004/process -H "Content-Type: application/json" -d @-
```

### 📚 Learn More
- **[Manual Setup Guide](MANUAL_SETUP.md)** - Detailed installation and development setup
- **[Contributing Guide](CONTRIBUTING.md)** - How to add new agents and protocols  
- **[Orchestrator Documentation](agents/orchestrator/README.md)** - Deep dive into the AI routing system
- **[ACP Agent Example](agents/acp-hello-world/README.md)** - Learn how agents work

### 🛠️ Development Mode
Want to modify the code? See the [Manual Setup Guide](MANUAL_SETUP.md) for local development.

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

#### Tests failing?
```bash
# Wait a moment for services to fully start
sleep 10
./scripts/test_all_agents.sh

# Check individual service health
curl http://localhost:8000/health
curl http://localhost:8004/health
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