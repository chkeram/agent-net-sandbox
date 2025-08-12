# Orchestrator Discovery and Routing Flow

## Overview

This document provides a comprehensive breakdown of how the Agent Network Sandbox orchestrator discovers, routes to, and executes requests on agents. Understanding this flow is crucial for debugging, enhancing, and extending the orchestrator system.

## High-Level Process

1. **Startup**: Discovery service initializes and performs initial agent discovery
2. **Discovery Loop**: Periodic refresh of agent registry  
3. **Schema Collection**: Fetch capabilities and schemas from agent endpoints
4. **Storage**: Store agent information in memory registry
5. **Routing**: LLM analyzes user queries and selects appropriate agents
6. **Execution**: Call selected agents using protocol-specific clients
7. **Response**: Return processed results to frontend

---

## Step-by-Step Code Flow

### Step 1: Startup - Discovery Service Initialization

**File:** `/agents/orchestrator/src/orchestrator/discovery.py`  
**Lines:** 31-43

```python
async def start(self):
    """Start the discovery service"""
    logger.info("Starting unified discovery service")
    
    self._running = True
    
    # Start discovery loop
    self._discovery_task = asyncio.create_task(self._discovery_loop())
    
    # Do initial discovery - THIS IS KEY!
    await self.refresh()  # ← First discovery happens here
    
    logger.info("Discovery service started successfully")
```

**When this happens:** When orchestrator container starts up  
**What happens:** Discovery service initializes and performs immediate agent discovery

---

### Step 2: Discovery Loop - Periodic Refresh

**File:** `/agents/orchestrator/src/orchestrator/discovery.py`  
**Lines:** 60-71

```python
async def _discovery_loop(self):
    """Continuous discovery loop"""
    while self._running:
        try:
            await asyncio.sleep(self.settings.discovery_interval_seconds)  # ← Wait interval
            if self._running:
                await self.refresh()  # ← Periodic rediscovery
        except Exception as e:
            logger.error("Discovery loop error", error=str(e))
```

**When this happens:** Every few minutes (configurable via `discovery_interval_seconds`)  
**What happens:** Continuous background process keeps agent registry fresh

---

### Step 3: Agent Discovery - HTTP Endpoint Probing

**File:** `/agents/orchestrator/src/orchestrator/discovery.py`  
**Lines:** 73-96 (main refresh), 98-163 (HTTP discovery)

```python
async def refresh(self):
    """Refresh the agent registry by discovering all available agents"""
    try:
        # Use HTTP-based agent discovery
        discovered_agents = await self._discover_agents_http()  # ← Core discovery
        
        # Update registry with health checks
        await self._update_registry(discovered_agents)
        
        # Clean up old/failed agents
        self._cleanup_registry()
```

**HTTP Discovery Logic:**
```python
async def _discover_agents_http(self) -> List[DiscoveredAgent]:
    known_endpoints = [
        {"url": "http://acp-hello-world-agent:8000", "protocol": "acp", "name": "hello-world"},
        {"url": "http://a2a-math-agent:8002", "protocol": "a2a", "name": "math"},
    ]
    
    for endpoint in known_endpoints:
        # Protocol-specific health checks
        health_url = f"{endpoint['url']}/health"
        if endpoint['protocol'] == 'a2a':
            health_url = f"{endpoint['url']}/.well-known/agent-card.json"
        
        # If healthy, extract agent information
        agent = await self._create_agent_from_endpoint(endpoint, session)
```

**What happens:** Probes known endpoints to check agent availability and health

---

### Step 4: Schema Collection - The Rich Information Gathering

**File:** `/agents/orchestrator/src/orchestrator/discovery.py`  
**Lines:** 165-251

#### For ACP Agents (Lines 174-204):

```python
if endpoint['protocol'] == 'acp':
    # Try to get ACP capabilities - THIS IS WHERE WE GET SCHEMAS!
    async with session.get(f"{endpoint['url']}/capabilities") as response:
        if response.status == 200:
            capabilities_data = await response.json()
            raw_capabilities = capabilities_data.get('capabilities', [])
            
            # Convert capability data to AgentCapability objects
            for cap in raw_capabilities:
                if isinstance(cap, dict):
                    # 🚨 PROBLEM: Only basic fields are stored
                    capabilities.append(AgentCapability(**cap))
                    # Missing: input_schema, output_schema from cap dict!
```

**What we GET from `/capabilities`:**
```json
{
  "name": "generate_greeting",
  "description": "Generate a personalized greeting message",
  "input_schema": {
    "type": "object",
    "properties": {
      "name": {"type": "string", "description": "Name to greet"},
      "language": {"type": "string", "description": "Language for greeting"}
    }
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "greeting": {"type": "string", "description": "The generated greeting"},
      "timestamp": {"type": "string", "description": "When generated"}
    }
  }
}
```

**What we STORE in AgentCapability:**
```python
# Only name and description are stored!
# Rich schema information is discarded ❌
```

#### For A2A Agents (Lines 206-233):

```python
elif endpoint['protocol'] == 'a2a':
    # Try to get A2A agent card
    async with session.get(f"{endpoint['url']}/.well-known/agent-card.json") as response:
        agent_card = await response.json()
        skills = agent_card.get('skills', [])
        for skill in skills:
            capabilities.append(AgentCapability(
                name=skill.get('name'),
                description=skill.get('description'),
                tags=skill.get('tags', [])
                # A2A doesn't provide detailed schemas in agent-card
            ))
```

**What happens:** Rich capability information is collected but schemas are not properly stored

---

### Step 5: Storage - Memory Registry

**File:** `/agents/orchestrator/src/orchestrator/discovery.py`  
**Lines:** 235-251

```python
# Create discovered agent
agent_data = {
    "agent_id": f"{endpoint['protocol']}-{endpoint['name']}",
    "name": endpoint.get('name'),
    "protocol": endpoint['protocol'],
    "endpoint": endpoint['url'],
    "capabilities": capabilities,  # ← Stored without rich schemas!
    "metadata": metadata,
    "status": "healthy",
    "discovered_at": datetime.utcnow()
}

# Agent gets stored in self.agent_registry
discovered_agent = DiscoveredAgent(**agent_data)
```

**What happens:** Agent information is stored in memory registry, but schema information is lost

---

### Step 6: Routing - LLM Agent Selection Process

**File:** `/agents/orchestrator/src/orchestrator/agent.py`

#### 6a: User Request Processing (Lines 263-289)

```python
async def route_request(self, request: RoutingRequest) -> RoutingDecision:
    # Create context for the AI agent
    context = OrchestratorContext(
        discovery_service=self.discovery_service,
        request=request
    )
    
    # Prepare the query for the AI agent
    query = f"""
User Query: "{request.query}"
Context: {request.context or 'None'}
Preferred Protocol: {request.preferred_protocol or 'Any'}

Please analyze this query and determine the best agent to handle it. Consider:
1. What capabilities are needed to answer this query?
2. Which available agents have those capabilities?
3. What is the best match based on agent specialization?

Use the available tools to get information about agents and their capabilities.
    """
    
    # Run the AI agent - THIS IS WHERE LLM GETS INVOLVED
    result = await self.agent.run(query, deps=context)
    routing_decision = result.data
```

#### 6b: LLM Tool Functions (Lines 137-171)

```python
@self.agent.tool
async def get_available_agents(ctx: RunContext[OrchestratorContext]) -> List[Dict[str, Any]]:
    """Get list of currently available and healthy agents"""
    agents = await ctx.deps.discovery_service.get_healthy_agents()
    
    result = [
        {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "protocol": agent.protocol.value,
            "capabilities": [
                {
                    "name": cap.name,
                    "description": cap.description,
                    "tags": cap.tags
                    # 🚨 PROBLEM: NO SCHEMAS PASSED TO LLM!
                }
                for cap in agent.capabilities
            ],
            "status": agent.status.value,
            "endpoint": agent.endpoint,
            "metadata": agent.metadata
        }
        for agent in agents
    ]
    return result
```

#### 6c: LLM Decision Process

**Example LLM reasoning for query "What is 2 + 2?":**

1. **LLM receives available agents:**
   ```json
   [
     {
       "agent_id": "a2a-math",
       "name": "math", 
       "protocol": "a2a",
       "capabilities": [
         {
           "name": "basic arithmetic",
           "description": "Perform basic arithmetic operations: addition, subtraction, multiplication, division"
         }
       ]
     },
     {
       "agent_id": "acp-hello-world", 
       "name": "hello-world",
       "protocol": "acp",
       "capabilities": [
         {
           "name": "greeting",
           "description": "Agent greeting capability"
         }
       ]
     }
   ]
   ```

2. **LLM reasoning process:**
   - User query requires mathematical calculation
   - Math agent has "basic arithmetic" capability  
   - Hello-world agent only has "greeting" capability
   - Best match: math agent with high confidence

3. **LLM returns decision:**
   ```python
   RoutingDecision(
       selected_agent=math_agent,
       confidence=0.95,
       reasoning="User's query asks for basic arithmetic operation which perfectly matches the math agent's capabilities"
   )
   ```

---

### Step 7: Execution - Calling the Selected Agent

**File:** `/agents/orchestrator/src/orchestrator/agent.py`

#### 7a: Process Request (Lines 366-433)

```python
async def process_request(self, request: RoutingRequest) -> AgentResponse:
    """Process a complete request: route and execute"""
    
    # First, route the request
    routing_decision = await self.route_request(request)
    
    if not routing_decision.selected_agent:
        return AgentResponse(success=False, error="No suitable agent found")
    
    # Use the selected agent
    selected_agent = routing_decision.selected_agent
    
    # Execute the request on the selected agent
    response_data = await self._execute_on_agent(selected_agent, request)
    
    return AgentResponse(
        request_id=request.request_id,
        agent_id=selected_agent.agent_id,
        protocol=selected_agent.protocol,
        response_data=response_data,
        success=True,
        metadata={"routing_decision": routing_decision.model_dump()}
    )
```

#### 7b: Protocol-Specific Execution (Lines 455-553)

```python
async def _execute_on_agent(
    self, 
    agent: DiscoveredAgent, 
    request: RoutingRequest
) -> Dict[str, Any]:
    """Execute request on the selected agent (protocol-specific implementation)"""
    
    if agent.protocol == ProtocolType.A2A:
        # ✅ REAL A2A CLIENT IMPLEMENTATION
        from .protocols.a2a_client import A2AProtocolClient
        
        client = A2AProtocolClient(timeout=10.0)
        response = await client.send_query(agent.endpoint, request.query)
        
        return {
            "message": response.get("text", "No response text"),
            "query": request.query,
            "agent_id": agent.agent_id,
            "protocol": agent.protocol.value,
            "timestamp": datetime.utcnow().isoformat(),
            "simulated": False,  # Real response!
            "raw_response": response.get("raw_result", response.get("raw_response")),
            "success": True
        }
        
    elif agent.protocol == ProtocolType.ACP:
        # 🚨 HARDCODED SIMULATION - NO REAL ACP CLIENT!
        await asyncio.sleep(0.1)  # Fake processing time
        
        return {
            "message": f"Response from {agent.name} (ACP protocol)",  # ← Hardcoded!
            "query": request.query,
            "agent_id": agent.agent_id,
            "protocol": agent.protocol.value,
            "timestamp": datetime.utcnow().isoformat(),
            "simulated": True  # Explicitly marked as fake
        }
```

---

## Current System Limitations

### 1. Schema Information Loss 🚨
- **Problem**: Rich schema information is collected during discovery but not stored
- **Impact**: Cannot dynamically parse response structures
- **Location**: `/agents/orchestrator/src/orchestrator/discovery.py:174-204`
- **Solution**: Store `input_schema` and `output_schema` in `AgentCapability` objects

### 2. Missing ACP Client Implementation 🚨
- **Problem**: ACP agents return hardcoded simulation responses
- **Impact**: Users don't get real responses from ACP agents
- **Location**: `/agents/orchestrator/src/orchestrator/agent.py:510-522`
- **Solution**: Implement real ACP protocol client

### 3. Limited LLM Context 🚨
- **Problem**: LLM doesn't receive schema information for routing decisions
- **Impact**: Less informed routing decisions
- **Location**: `/agents/orchestrator/src/orchestrator/agent.py:148-154`
- **Solution**: Include schemas in LLM tool responses

---

## Data Flow Summary

```
User Query "What is 2 + 2?"
           ↓
    [Orchestrator API]
           ↓
    [LLM Routing Agent] → Gets agents without schemas
           ↓
    [Selected: a2a-math]
           ↓
    [A2A Protocol Client] → Real implementation ✅
           ↓ 
    [A2A Math Agent] → Returns structured response
           ↓
    [Frontend] → Parses A2A parts structure ✅
```

vs.

```
User Query "Hello there"
           ↓
    [Orchestrator API]
           ↓  
    [LLM Routing Agent] → Gets agents without schemas
           ↓
    [Selected: acp-hello-world]
           ↓
    [Hardcoded Simulation] → No real ACP client ❌
           ↓
    [Generic Response] → "Response from hello-world (ACP protocol)"
           ↓
    [Frontend] → Gets hardcoded text ❌
```

---

## Related Issues

- **Issue #25**: [bug: Orchestrator uses hardcoded responses for ACP protocol instead of calling actual agent](https://github.com/chkeram/agent-net-sandbox/issues/25)
- **Issue #26**: [feat: Implement schema-aware discovery and dynamic response parsing](https://github.com/chkeram/agent-net-sandbox/issues/26)

---

## Next Steps

1. **Implement ACP Client** (Issue #25)
   - Create real ACP protocol client
   - Replace hardcoded simulation with actual agent calls

2. **Enhance Schema Storage** (Issue #26)  
   - Store schemas during discovery
   - Pass schemas to LLM for better routing
   - Use schemas for dynamic response parsing

3. **Improve Frontend Parsing**
   - Use schema information for content extraction
   - Support dynamic field parsing for any agent type