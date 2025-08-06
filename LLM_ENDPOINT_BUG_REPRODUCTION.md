# LLM Endpoint Hallucination Bug - Step-by-Step Reproduction

## Overview
This document captures the detailed reproduction of the LLM endpoint hallucination bug where the Pydantic AI agent generates incorrect endpoints despite receiving correct data from tool functions.

## Bug Summary
- **Issue**: LLM receives correct endpoint data from tools but generates hallucinated endpoints in routing decisions
- **Expected**: `http://a2a-math-agent:8002` (from tool response)
- **Actual**: Various hallucinated endpoints like `http://a2a-math-agent-url`

## System State Before Testing

### Environment Setup
```bash
# Branch: feat/orchestrator-a2a-integration
# Docker Compose multi-agent setup
# Enhanced logging added to track LLM tool interactions
```

### Services Status
```bash
# Check all services are running
docker-compose ps
```

## Reproduction Steps

### Step 1: Verify A2A Math Agent is Healthy

**Command:**
```bash
curl -s http://localhost:8002/.well-known/agent-card.json | jq '.name'
```

**Result:**
```json
"A2A Math Operations Agent"
```
✅ **Status**: A2A Math Agent is responding correctly

### Step 2: Check Service Status

**Command:**
```bash
docker-compose ps
```

**Result:**
```
NAME                    IMAGE                          COMMAND                  SERVICE           CREATED          STATUS                    PORTS
a2a-math-agent          a2a-math-agent:latest          "python docker_entry…"   a2a-math-agent    22 hours ago     Up 22 hours (unhealthy)   0.0.0.0:8002->8002/tcp
acp-hello-world-agent   acp-hello-world-agent:latest   "python -m uvicorn h…"   acp-hello-world   46 minutes ago   Up 46 minutes (healthy)   0.0.0.0:8000->8000/tcp
agent-directory         nginx:alpine                   "/docker-entrypoint.…"   agent-directory   39 hours ago     Up 22 hours               0.0.0.0:8080->80/tcp
agent-orchestrator      agent-orchestrator:latest      "python -m orchestra…"   orchestrator      46 seconds ago   Up 44 seconds (healthy)   0.0.0.0:8004->8004/tcp
```
📝 **Note**: A2A Math Agent shows as unhealthy in Docker but responds to requests

### Step 3: Test Orchestrator Routing (Primary Test)

**Command:**
```bash
curl -X POST http://localhost:8004/route \
  -H "Content-Type: application/json" \
  -d '{"query": "What is 5 + 3?"}'
```

**Response:**
```json
{
  "request_id": "math-addition-query",
  "selected_agent": {
    "agent_id": "a2a-math",
    "name": "math", 
    "protocol": "a2a",
    "endpoint": "http://a2a-math-agent:8002",
    "capabilities": [
      {
        "name": "basic arithmetic",
        "description": "Perform basic arithmetic operations: addition, subtraction, multiplication, division"
      },
      {
        "name": "advanced mathematics", 
        "description": "Perform advanced mathematical operations like square roots and exponentiation"
      }
    ],
    "status": "healthy"
  },
  "confidence": 0.95,
  "decision_time_ms": 6172.709,
  "llm_provider": "openai"
}
```

## 🚨 IMPORTANT DISCOVERY

**The LLM routing is working CORRECTLY in this test!** The endpoint returned is exactly what we expect:
- **Received**: `"endpoint": "http://a2a-math-agent:8002"`  
- **Expected**: `"endpoint": "http://a2a-math-agent:8002"`
- **Status**: ✅ **CORRECT - No hallucination occurred**

## Detailed Log Analysis

### Step 4: LLM Tool Interaction Logs

**From orchestrator logs, we can see the exact flow:**

#### 4.1 LLM Request Start
```json
{
  "request_id": "6a0d66a5-7aca-4031-89af-fd6c071212b4",
  "query": "What is 5 + 3?",
  "llm_query": "User Query: \"What is 5 + 3?\"\nContext: None\n...",
  "event": "LLM_REQUEST_START",
  "timestamp": "2025-08-06T09:31:02.149450Z"
}
```

#### 4.2 Tool Call 1: get_agents_by_capability
```json
{
  "tool_name": "get_agents_by_capability",
  "capability_requested": "math",
  "agents_count": 0,
  "agent_endpoints": [],
  "full_response": [],
  "event": "LLM_TOOL_CALL: get_agents_by_capability"
}
```
📝 **Finding**: LLM first tried to find agents with "math" capability but got 0 results

#### 4.3 Tool Call 2: get_available_agents (Successful)
```json
{
  "tool_name": "get_available_agents",
  "agents_count": 2,
  "agent_endpoints": ["http://acp-hello-world-agent:8000", "http://a2a-math-agent:8002"],
  "full_response": [
    {
      "agent_id": "acp-hello-world",
      "name": "hello-world",
      "protocol": "acp",
      "capabilities": [{"name": "greeting", "description": "Agent greeting capability"}],
      "endpoint": "http://acp-hello-world-agent:8000"
    },
    {
      "agent_id": "a2a-math",
      "name": "math", 
      "protocol": "a2a",
      "capabilities": [
        {"name": "basic arithmetic", "description": "Perform basic arithmetic operations: addition, subtraction, multiplication, division"},
        {"name": "advanced mathematics", "description": "Perform advanced mathematical operations like square roots and exponentiation"}
      ],
      "endpoint": "http://a2a-math-agent:8002"
    }
  ]
}
```
✅ **Tool Response Correct**: A2A Math Agent endpoint is `http://a2a-math-agent:8002`

#### 4.4 LLM Decision (Final Result)
```json
{
  "selected_agent_id": "a2a-math",
  "selected_agent_name": "math",
  "selected_agent_endpoint": "http://a2a-math-agent:8002",
  "confidence": 0.95,
  "reasoning": "The user query requires a capability in basic arithmetic to compute the sum of 5 and 3. The 'math' agent is specialized in both basic and advanced mathematical operations including addition, and is currently healthy.",
  "full_selected_agent": {
    "agent_id": "a2a-math", 
    "name": "math",
    "protocol": "a2a",
    "endpoint": "http://a2a-math-agent:8002"
  }
}
```

✅ **LLM Decision Correct**: The LLM used the exact endpoint from the tool response

## Critical Analysis

### What This Test Reveals:

1. **LLM Tool Integration Works**: The LLM correctly called `get_available_agents` and received accurate endpoint data

2. **No Endpoint Hallucination**: The LLM returned the exact same endpoint it received from tools: `http://a2a-math-agent:8002`

3. **Proper Agent Selection**: The LLM correctly identified that the A2A Math Agent has the required arithmetic capabilities

4. **Data Flow Integrity**: Tool → LLM → Decision pipeline maintained data accuracy

### Hypothesis Status:
❌ **BUG NOT REPRODUCED** - The LLM routing system worked correctly in this test

### Possible Explanations:
1. **Bug was fixed**: Our previous commits may have resolved the issue
2. **Intermittent Bug**: The hallucination may only occur under specific conditions
3. **Environment Dependent**: The bug may be related to specific LLM models or API states
4. **Condition-Specific**: Bug may only manifest with certain query types or system states

### Next Steps for Reproduction

We need to try different scenarios to reproduce the original hallucination bug:

---

## 🔬 Additional Reproduction Attempts

After the initial successful test, I conducted extensive testing to try to reproduce the original hallucination bug:

### Test 2: Different Math Operations
```bash
curl -X POST http://localhost:8004/route \
  -H "Content-Type: application/json" \
  -d '{"query": "Calculate the square root of 144"}'
```
**Result**: ✅ Correct endpoint returned: `http://a2a-math-agent:8002`

### Test 3: With Preferred Protocol
```bash
curl -X POST http://localhost:8004/route \
  -H "Content-Type: application/json" \
  -d '{"query": "I need help with mathematical calculations", "preferred_protocol": "a2a"}'
```
**Result**: ✅ Correct endpoint returned: `http://a2a-math-agent:8002`

### Test 4: Full Process Execution
```bash
curl -X POST http://localhost:8004/process \
  -H "Content-Type: application/json" \
  -d '{"query": "What is 7 + 9?"}'
```
**Result**: ✅ Successful execution with `simulated: false` - A2A communication working properly

### Test 5: Rapid Successive Requests
```bash
for i in {1..5}; do curl -X POST http://localhost:8004/route -H "Content-Type: application/json" -d "{\"query\": \"Calculate $i + $i\"}" -s | jq -c '{endpoint: .selected_agent.endpoint}'; done
```
**Results**: 
- All 5 requests returned: `{"endpoint":"http://a2a-math-agent:8002"}`
- No hallucination detected

### Test 6: Agent Restart Scenario
```bash
docker restart a2a-math-agent
# Wait 5 seconds
curl -X POST http://localhost:8004/route -H "Content-Type: application/json" -d '{"query": "What is 15 - 7?"}'
```
**Result**: ✅ Correct endpoint even after agent restart

### Test 7: Concurrent Load Testing
```bash
for i in {1..10}; do (curl -X POST http://localhost:8004/route -H "Content-Type: application/json" -d "{\"query\": \"Math test $i: what is $i times 2?\"}" -s | jq -c "{test: \"$i\", endpoint: .selected_agent.endpoint}" &); done; wait
```
**Results**: All 10 concurrent requests returned correct endpoint: `http://a2a-math-agent:8002`

### Test 8: Complex Reasoning Query
```bash
curl -X POST http://localhost:8004/route \
  -H "Content-Type: application/json" \
  -d '{"query": "I need an agent that can handle mathematical calculations for computing derivatives and integrals"}'
```
**Result**: ✅ Correct endpoint returned: `http://a2a-math-agent:8002`

## 🚨 CRITICAL FINDING: Bug Not Reproducible

After extensive testing with multiple scenarios, patterns, and edge cases, **I was unable to reproduce the LLM endpoint hallucination bug**.

### Evidence Analysis:

#### ✅ **What's Working Correctly:**
1. **Tool Function Data**: All tool functions return correct endpoint `http://a2a-math-agent:8002`
2. **LLM Tool Calls**: Logs show LLM correctly receives endpoint data from tools
3. **LLM Decision Making**: LLM consistently returns the exact same endpoint from tool responses
4. **No Hallucination**: Zero instances of incorrect endpoints like `http://a2a-math-agent-url`
5. **End-to-End Flow**: Complete orchestrator → A2A Math Agent communication working with `simulated: false`

#### 📊 **Test Coverage:**
- **Simple math queries**: ✅ Working
- **Complex queries**: ✅ Working  
- **Protocol preferences**: ✅ Working
- **Rapid requests**: ✅ Working
- **Concurrent requests**: ✅ Working
- **Agent restart scenarios**: ✅ Working
- **Full execution flow**: ✅ Working

### Hypothesis: **Bug Was Previously Fixed**

The most likely explanation is that our previous bug fixes in the conversation resolved the endpoint hallucination issue:

1. **Fixed endpoint field inclusion** in `get_agents_by_protocol` and `get_agents_by_capability`
2. **Fixed A2A protocol implementation** (root endpoint `/` and `kind: text` format)
3. **Added comprehensive logging** that may have also improved system stability

### Status Update:
- **Original Bug**: LLM hallucinating endpoints despite receiving correct tool data
- **Current Status**: ❌ **NOT REPRODUCIBLE** - System working correctly
- **Likely Resolution**: Fixed by previous commits addressing endpoint data flow

### Recommendation:
1. **Mark Issue #12 as potentially resolved** by previous fixes
2. **Monitor production** for any recurrence of the hallucination behavior
3. **Keep enhanced logging** to detect future occurrences
4. **Consider closing** the GitHub issue if no further instances are observed

---

## Summary

This reproduction attempt demonstrates that the LLM endpoint hallucination bug is currently **not occurring**. The system is correctly:
- Discovering agents with proper endpoints
- Providing accurate data to LLM tools  
- Having LLM return exact endpoints from tool responses
- Successfully executing A2A agent communication

The comprehensive logging we added will help detect if this issue reoccurs in the future.