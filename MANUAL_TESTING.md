# Manual End-to-End Testing Guide
## Multi-Protocol Agent Orchestrator + ACP Agent Integration

This guide provides comprehensive manual testing procedures for validating the integration between the Multi-Protocol Agent Orchestrator and the ACP Hello World Agent.

## 🎯 Testing Objective

Verify the complete integration workflow:
1. **Agent Discovery** - Orchestrator automatically discovers ACP agents
2. **Intelligent Routing** - AI-powered routing selects appropriate agents
3. **Request Processing** - End-to-end request execution and response handling
4. **Monitoring** - Metrics collection and system health tracking

## 📋 Assessment: ACP Hello World Agent Readiness

**✅ The ACP Hello World Agent is PERFECT for integration testing!**

**Why it's ideal:**
- **Full ACP Protocol Compliance**: Implements all required endpoints (`/auth`, `/schema`, `/config`, `/invoke`, `/capabilities`)
- **Rich Capabilities**: Multi-language greetings, custom configurations, streaming responses
- **Docker Discovery Ready**: Proper labels for orchestrator discovery (`agent.protocol=acp`, `agent.type=hello-world`)
- **Comprehensive API**: Both ACP-compliant (`/invoke`) and direct (`/hello`) endpoints
- **Built-in Testing Tools**: Health checks, CLI clients, and test scripts
- **Multi-language Support**: English, Spanish, French, German, Italian greetings

## 🚀 Five-Phase Testing Plan

### Phase 1: Environment Setup

#### 1.1 Prerequisites
- Docker and Docker Compose installed
- OpenAI API key OR Anthropic API key
- curl and jq for testing (optional but recommended)

#### 1.2 Setup Commands
```bash
# Navigate to project root
cd agent-net-sandbox

# Create environment configuration
cp agents/orchestrator/.env.example .env

# Edit .env file with your API key
# Required: Set either OPENAI_API_KEY or ANTHROPIC_API_KEY
# Example:
# OPENAI_API_KEY=sk-your-actual-key-here
# ORCHESTRATOR_LLM_PROVIDER=openai
```

#### 1.3 Start Services
```bash
# Build and start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# Expected output: orchestrator, acp-hello-world, and agent-directory should be "Up"
```

#### 1.4 Health Verification
```bash
# Check orchestrator health
curl http://localhost:8004/health

# Expected: {"status": "healthy", ...}

# Check ACP agent health  
curl http://localhost:8000/health

# Expected: {"status": "healthy", "timestamp": ...}
```

---

### Phase 2: Discovery Testing

#### 2.1 Verify Agent Discovery
```bash
# List all discovered agents
curl http://localhost:8004/agents | jq

# Expected: Array with one ACP agent
# Look for: agent_id="acp-hello-world-agent", protocol="acp", status="healthy"
```

#### 2.2 Get Detailed Agent Information
```bash
# Get specific agent details
curl http://localhost:8004/agents/acp-hello-world-agent | jq

# Expected: Full agent details including capabilities, endpoint, metadata
```

#### 2.3 Check System Capabilities
```bash
# List all available capabilities across agents
curl http://localhost:8004/capabilities | jq

# Expected: Should include greeting-related capabilities from ACP agent
```

#### 2.4 Verify System Status
```bash
# Get comprehensive system status
curl http://localhost:8004/status | jq

# Expected: 
# - orchestrator_healthy: true
# - discovery_service_healthy: true  
# - total_agents: 1
# - healthy_agents: 1
```

---

### Phase 3: Routing Intelligence Testing

#### 3.1 Test Basic Greeting Routing
```bash
# Test simple greeting request
curl -X POST http://localhost:8004/route \
  -H "Content-Type: application/json" \
  -d '{"query": "Say hello to me"}' | jq

# Expected:
# - selected_agent: ACP hello world agent
# - confidence: > 0.8 (high confidence)
# - reasoning: Should mention greeting/hello capabilities
```

#### 3.2 Test Language-Specific Routing
```bash
# Test Spanish greeting request
curl -X POST http://localhost:8004/route \
  -H "Content-Type: application/json" \
  -d '{"query": "Say hello in Spanish"}' | jq

# Test French greeting request  
curl -X POST http://localhost:8004/route \
  -H "Content-Type: application/json" \
  -d '{"query": "Greet me in French please"}' | jq

# Expected: High confidence, agent selected, language-aware reasoning
```

#### 3.3 Test Edge Cases
```bash
# Test non-greeting query (should show lower confidence or no agent)
curl -X POST http://localhost:8004/route \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the weather today?"}' | jq

# Test ambiguous query
curl -X POST http://localhost:8004/route \
  -H "Content-Type: application/json" \
  -d '{"query": "Help me"}' | jq

# Expected: Lower confidence scores, possibly no agent selected
```

#### 3.4 Test Preferred Protocol
```bash
# Test with protocol preference
curl -X POST http://localhost:8004/route \
  -H "Content-Type: application/json" \
  -d '{"query": "Say hello", "preferred_protocol": "acp"}' | jq

# Expected: ACP agent selected if available and suitable
```

---

### Phase 4: End-to-End Request Processing

#### 4.1 Basic Request Processing
```bash
# Complete request processing (route + execute)
curl -X POST http://localhost:8004/process \
  -H "Content-Type: application/json" \
  -d '{"query": "Say hello to Alice"}' | jq

# Expected:
# - success: true
# - agent_id: "acp-hello-world-agent"
# - response_data: Greeting message for Alice
# - metadata: Routing decision and execution details
```

#### 4.2 Multi-Language Processing
```bash
# Test Spanish greeting
curl -X POST http://localhost:8004/process \
  -H "Content-Type: application/json" \
  -d '{"query": "Say hello to Bob in Spanish"}' | jq

# Test French greeting
curl -X POST http://localhost:8004/process \
  -H "Content-Type: application/json" \
  -d '{"query": "Generate a French greeting for Marie"}' | jq

# Expected: Responses in appropriate languages (Hola, Bonjour)
```

#### 4.3 Custom Message Processing
```bash
# Test custom greeting message
curl -X POST http://localhost:8004/process \
  -H "Content-Type: application/json" \
  -d '{"query": "Create a personalized greeting for Sarah with a welcome message"}' | jq

# Expected: Personalized greeting with custom message
```

#### 4.4 Error Handling
```bash
# Test unsupported request
curl -X POST http://localhost:8004/process \
  -H "Content-Type: application/json" \
  -d '{"query": "Calculate the square root of 144"}' | jq

# Expected: 
# - success: false OR routing to indicate no suitable agent
# - error message explaining no suitable agent found
```

---

### Phase 5: Advanced Testing

#### 5.1 Direct ACP Agent Testing
```bash
# Test ACP agent directly (bypass orchestrator)
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{"input": {"name": "DirectTest", "language": "en"}}' | jq

# Compare with orchestrated request
curl -X POST http://localhost:8004/process \
  -H "Content-Type: application/json" \
  -d '{"query": "Say hello to DirectTest"}' | jq

# Expected: Both should produce greeting responses, orchestrated version includes metadata
```

#### 5.2 Capabilities and Schema Testing
```bash
# Get ACP agent capabilities directly
curl http://localhost:8000/capabilities | jq

# Get ACP agent schema
curl http://localhost:8000/schema | jq

# Compare with orchestrator's view
curl http://localhost:8004/agents/acp-hello-world-agent | jq

# Expected: Orchestrator should have parsed and stored agent capabilities correctly
```

#### 5.3 Metrics and Monitoring
```bash
# Check orchestrator metrics before requests
curl http://localhost:8004/metrics | jq

# Make several requests
for i in {1..5}; do
  curl -X POST http://localhost:8004/process \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"Say hello to User$i\"}" > /dev/null 2>&1
done

# Check metrics after requests
curl http://localhost:8004/metrics | jq

# Expected: 
# - total_requests should increase by 5
# - successful_requests should increase
# - Response times should be recorded
```

#### 5.4 Logging Analysis
```bash
# View orchestrator logs during processing
docker-compose logs -f orchestrator &

# Make a request in another terminal
curl -X POST http://localhost:8004/process \
  -H "Content-Type: application/json" \
  -d '{"query": "Say hello with logs"}' | jq

# Expected logs:
# - Agent discovery events
# - Routing decision logs
# - Request processing logs
# - Response generation logs
```

---

## 📊 Expected Results Summary

### Discovery Phase
- **Agents Found**: 1 healthy ACP agent
- **Agent Details**: Proper protocol, capabilities, and endpoint information
- **Health Status**: All services reporting healthy

### Routing Phase  
- **Greeting Queries**: High confidence (>0.8) routing to ACP agent
- **Language Queries**: Intelligent language-aware routing
- **Non-Greeting Queries**: Low confidence or no agent selection
- **Reasoning**: Clear explanations for routing decisions

### Processing Phase
- **Success Rate**: 100% for greeting-related queries
- **Response Quality**: Proper greetings in requested languages
- **Metadata**: Complete routing and execution information
- **Error Handling**: Graceful handling of unsupported queries

### Monitoring Phase
- **Metrics**: Accurate tracking of requests, responses, and timing
- **Logs**: Detailed structured logging of all operations
- **Health**: Continuous health monitoring of all components

---

## ✅ Success Criteria

### Core Functionality
- [ ] Orchestrator discovers ACP agent automatically within 30 seconds
- [ ] Routing decisions show confidence >0.8 for greeting queries
- [ ] End-to-end requests return proper greeting responses
- [ ] Multi-language support works correctly (EN, ES, FR, DE, IT)

### System Integration
- [ ] Agent metadata and capabilities correctly extracted from Docker labels
- [ ] ACP protocol endpoints properly called by orchestrator
- [ ] Request/response format conversion works seamlessly
- [ ] Error handling provides clear feedback

### Monitoring & Observability
- [ ] Logs show successful discovery and routing operations
- [ ] Metrics accurately track requests and responses
- [ ] Health checks report system status correctly
- [ ] Performance metrics show reasonable response times (<2s typical)

### Edge Cases
- [ ] Non-greeting queries handled gracefully
- [ ] Invalid requests return appropriate error messages
- [ ] Agent unavailability detected and reported
- [ ] System recovery works after agent restarts

---

## 🔧 Troubleshooting

### Common Issues

**Services Not Starting**
```bash
# Check Docker compose logs
docker-compose logs orchestrator
docker-compose logs acp-hello-world

# Verify port availability
lsof -i :8004  # Orchestrator port
lsof -i :8000  # ACP agent port
```

**Agent Not Discovered**
```bash
# Check Docker network
docker network ls | grep agent-network

# Verify agent labels
docker inspect acp-hello-world-agent | jq '.[0].Config.Labels'

# Check orchestrator discovery logs
docker-compose logs orchestrator | grep -i discovery
```

**Routing Failures**
```bash
# Verify LLM provider configuration
curl http://localhost:8004/status | jq '.orchestrator_healthy'

# Check API key in logs (will show errors if invalid)
docker-compose logs orchestrator | grep -i "api\|auth\|key"
```

**Low Performance**
```bash
# Check resource usage
docker stats

# Monitor response times
time curl -X POST http://localhost:8004/process \
  -H "Content-Type: application/json" \
  -d '{"query": "Say hello"}'
```

---

## 🎉 Completion

After completing all phases successfully, you will have:

1. **Validated Discovery** - Confirmed automatic agent discovery works
2. **Tested Routing** - Verified AI-powered intelligent routing  
3. **Confirmed Processing** - End-to-end request processing operational
4. **Monitored System** - Metrics and logging functioning properly

The Multi-Protocol Agent Orchestrator is now ready for production deployment and can be extended with additional agents and protocols!

---

## 📝 Test Results Template

Use this template to record your test results:

```
## Test Execution Results - [Date]

### Environment
- Docker Compose Version: ___
- Services Started: ___
- LLM Provider: ___

### Phase 1 - Setup: ✅/❌
- Services started: ___
- Health checks passed: ___
- Notes: ___

### Phase 2 - Discovery: ✅/❌  
- Agents discovered: ___
- Capabilities parsed: ___
- Notes: ___

### Phase 3 - Routing: ✅/❌
- Greeting queries confidence: ___
- Language routing: ___
- Edge cases: ___
- Notes: ___

### Phase 4 - Processing: ✅/❌
- Success rate: ___
- Response quality: ___
- Error handling: ___
- Notes: ___

### Phase 5 - Advanced: ✅/❌
- Direct agent comparison: ___
- Metrics accuracy: ___
- Logging quality: ___
- Notes: ___

### Overall Result: ✅/❌
### Additional Notes:
```