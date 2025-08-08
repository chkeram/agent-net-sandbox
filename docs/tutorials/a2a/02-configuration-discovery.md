# Part 2: Configuration & Discovery

## 🎯 Learning Objectives

By the end of this tutorial, you will:
- Master A2A agent card structure and customization
- Understand skill definition and capability advertisement
- Learn agent discovery mechanisms and registration patterns
- Implement dynamic agent cards with environment-based capabilities
- Integrate with orchestrators and discovery services

## 📚 Prerequisites

- Completed [Part 1: Understanding A2A Fundamentals](./01-understanding-a2a.md)
- Basic understanding of JSON and configuration patterns
- Familiarity with environment variables and configuration management
- Access to our A2A Math Agent for hands-on examples

## 🗃️ A2A Agent Card Deep Dive

The agent card (`/.well-known/agent-card.json`) is the cornerstone of A2A discovery. Let's examine our Math Agent's card in detail:

### **Complete Agent Card Structure**

Our Math Agent dynamically creates its agent card based on available LLM providers:

```json
{
  "name": "A2A Math Operations Agent",
  "description": "A mathematical computation agent using the A2A protocol with deterministic mathematical calculations",
  "version": "0.1.0",
  "protocolVersion": "0.3.0",
  "preferredTransport": "JSONRPC",
  "url": "http://localhost:8002",
  "capabilities": {},
  "defaultInputModes": ["text"],
  "defaultOutputModes": ["text"],
  "skills": [
    {
      "id": "basic_arithmetic",
      "name": "Basic Arithmetic",
      "description": "Perform basic arithmetic operations: addition, subtraction, multiplication, division",
      "examples": ["5 + 3", "10 - 4", "6 * 7", "15 / 3"],
      "tags": ["arithmetic", "math", "basic", "deterministic"]
    },
    {
      "id": "advanced_math",
      "name": "Advanced Mathematics",
      "description": "Perform advanced mathematical operations like square roots and exponentiation", 
      "examples": ["sqrt(16)", "2^3", "5**2"],
      "tags": ["advanced", "math", "power", "roots", "deterministic"]
    }
  ]
}
```

**Note**: When LLM providers are configured, the agent card dynamically adds a third skill:

```json
{
  "id": "llm_math",
  "name": "LLM-Powered Mathematics",
  "description": "Natural language mathematical problem solving using AI (gemini, openai, anthropic)",
  "examples": [
    "What is the derivative of x^2?",
    "Solve 2x + 5 = 13", 
    "Calculate the area of a circle with radius 5",
    "Convert 32 Fahrenheit to Celsius"
  ],
  "tags": ["llm", "natural-language", "ai", "complex-math", "gemini", "openai", "anthropic"]
}
```

## 🏗️ Agent Card Field Breakdown

### **Essential Fields**

| Field | Type | Purpose | Example |
|-------|------|---------|---------|
| **name** | string | Human-readable agent name | "A2A Math Operations Agent" |
| **description** | string | Agent capabilities summary | "Mathematical computation agent..." |
| **version** | string | Agent version (semver) | "0.1.0" |
| **protocolVersion** | string | A2A protocol version | "0.3.0" |
| **preferredTransport** | string | Transport preference | "JSONRPC" |
| **url** | string | Base agent URL | "http://localhost:8002" |

### **Capability Fields**

| Field | Type | Purpose | Example |
|-------|------|---------|---------|
| **skills** | Array[Skill] | Agent capabilities | [arithmetic, advanced_math] |
| **capabilities** | Object | Additional capabilities | {} |
| **defaultInputModes** | Array[string] | Supported input types | ["text"] |
| **defaultOutputModes** | Array[string] | Supported output types | ["text"] |

### **Skill Structure**

| Field | Type | Purpose | Example |
|-------|------|---------|---------|
| **id** | string | Unique skill identifier | "basic_arithmetic" |
| **name** | string | Human-readable name | "Basic Arithmetic" |
| **description** | string | What the skill does | "Perform basic arithmetic operations..." |
| **examples** | Array[string] | Sample inputs | ["5 + 3", "10 - 4"] |
| **tags** | Array[string] | Discovery metadata | ["arithmetic", "math", "basic"] |

## 🎛️ Dynamic Agent Card Configuration

Our Math Agent demonstrates advanced configuration patterns:

### **1. Environment-Based Configuration**

```python
# From our agent implementation
def create_agent_card() -> AgentCard:
    """Create the agent card describing this math agent's capabilities."""
    
    # Check LLM availability to adjust capabilities
    llm_service = LLMService()
    llm_available = llm_service.is_llm_available()
    provider_status = llm_service.get_provider_status()
    
    # Base skills (always available)
    skills = [
        AgentSkill(
            id="basic_arithmetic",
            name="Basic Arithmetic",
            description="Perform basic arithmetic operations: addition, subtraction, multiplication, division",
            examples=["5 + 3", "10 - 4", "6 * 7", "15 / 3"],
            tags=["arithmetic", "math", "basic", "deterministic"]
        ),
        AgentSkill(
            id="advanced_math",
            name="Advanced Mathematics", 
            description="Perform advanced mathematical operations like square roots and exponentiation",
            examples=["sqrt(16)", "2^3", "5**2"],
            tags=["advanced", "math", "power", "roots", "deterministic"]
        )
    ]
    
    # Add LLM-powered skill if available
    if llm_available:
        available_providers = provider_status.get("available_providers", [])
        skills.append(
            AgentSkill(
                id="llm_math",
                name="LLM-Powered Mathematics",
                description=f"Natural language mathematical problem solving using AI ({', '.join(available_providers)})",
                examples=[
                    "What is the derivative of x^2?",
                    "Solve 2x + 5 = 13",
                    "Calculate the area of a circle with radius 5",
                    "Convert 32 Fahrenheit to Celsius"
                ],
                tags=["llm", "natural-language", "ai", "complex-math"] + available_providers
            )
        )
```

### **2. Dynamic Description Generation**

```python
# Create description based on capabilities
base_description = "A mathematical computation agent using the A2A protocol"
if llm_available:
    available_providers = provider_status.get("available_providers", [])
    description = f"{base_description} with AI-powered problem solving ({', '.join(available_providers)}) and deterministic calculation fallback"
else:
    description = f"{base_description} with deterministic mathematical calculations"
```

### **3. Environment Variables Integration**

```bash
# .env configuration affects agent card
LLM_PROVIDER=gemini                    # Changes available skills
GEMINI_API_KEY=your_key_here          # Enables LLM skill
A2A_PORT=8002                         # Updates agent URL
LLM_MAX_TOKENS=150                    # Affects LLM skill description
```

## 🔍 Discovery Mechanisms

A2A agents are discovered through multiple mechanisms:

### **1. HTTP Endpoint Discovery**

```bash
# Primary discovery endpoint
curl -s http://localhost:8002/.well-known/agent-card.json | jq '{
  name,
  version,
  skills: [.skills[] | {id, name, description}]
}'
```

### **2. Alternative Discovery Endpoints**

```bash
# Alternative agent card endpoint
curl -s http://localhost:8002/.well-known/agent.json | jq .

# Direct agent info (if implemented)
curl -s http://localhost:8002/info | jq .
```

### **3. Orchestrator Integration**

Our orchestrator discovers A2A agents through HTTP-based discovery:

```python
# From agents/orchestrator/src/orchestrator/discovery.py
async def _create_agent_from_endpoint(self, endpoint: dict, session) -> Optional[DiscoveredAgent]:
    if endpoint['protocol'] == 'a2a':
        # Try to get A2A agent card
        try:
            async with session.get(f"{endpoint['url']}/.well-known/agent-card.json") as response:
                if response.status == 200:
                    agent_card = await response.json()
                    metadata = {
                        'version': agent_card.get('version'),
                        'protocolVersion': agent_card.get('protocolVersion'),
                        'description': agent_card.get('description'),
                        'preferredTransport': agent_card.get('preferredTransport')
                    }
                    
                    # Convert skills to capabilities
                    skills = agent_card.get('skills', [])
                    for skill in skills:
                        capabilities.append(AgentCapability(
                            name=skill.get('name', skill.get('id', 'unknown')),
                            description=skill.get('description', f"A2A skill: {skill.get('name', 'unknown')}"),
                            tags=skill.get('tags', [])
                        ))
```

## 🏷️ Skill Definition Best Practices

### **1. Skill Naming Conventions**

```python
# Good skill IDs
"basic_arithmetic"     # Clear, descriptive, snake_case
"advanced_math"        # Category and level
"llm_math"            # Technology and domain
"text_processing"     # Function and data type

# Avoid
"skill1"              # Non-descriptive
"BasicArithmetic"     # CamelCase
"math-advanced"       # Inconsistent separators
```

### **2. Example Strategy**

```python
# Provide diverse, realistic examples
examples = [
    "5 + 3",           # Simple case
    "10 - 4",          # Different operation
    "6 * 7",           # Multiplication
    "15 / 3",          # Division
    "12.5 + 2.3"       # Decimal numbers
]

# For LLM skills, show natural language variety
llm_examples = [
    "What is the derivative of x^2?",        # Calculus
    "Solve 2x + 5 = 13",                     # Algebra
    "Calculate the area of a circle with radius 5",  # Geometry
    "Convert 32 Fahrenheit to Celsius"       # Unit conversion
]
```

### **3. Tag Strategy**

```python
# Hierarchical tagging
tags = [
    "arithmetic",      # Domain
    "math",           # Broader category  
    "basic",          # Complexity level
    "deterministic"   # Processing type
]

# For LLM skills
llm_tags = [
    "llm",                    # Technology
    "natural-language",       # Input type
    "ai",                    # Processing method
    "complex-math"           # Capability level
] + available_providers     # Dynamic provider tags
```

## 🔧 Testing Agent Card Configuration

### **Test 1: Basic Agent Card Retrieval**

```bash
# Test agent discovery
curl -s http://localhost:8002/.well-known/agent-card.json | jq '{
  name,
  version,
  description,
  protocolVersion,
  url,
  skillCount: (.skills | length),
  inputModes: .defaultInputModes,
  outputModes: .defaultOutputModes
}'
```

**Expected Output:**
```json
{
  "name": "A2A Math Operations Agent",
  "version": "0.1.0",
  "description": "A mathematical computation agent using the A2A protocol with deterministic mathematical calculations",
  "protocolVersion": "0.3.0", 
  "url": "http://localhost:8002",
  "skillCount": 2,
  "inputModes": ["text"],
  "outputModes": ["text"]
}
```

### **Test 2: Skills and Capabilities**

```bash
# Test skills structure
curl -s http://localhost:8002/.well-known/agent-card.json | jq '.skills[] | {
  id,
  name,
  description,
  exampleCount: (.examples | length),
  tags
}'
```

**Expected Output:**
```json
{
  "id": "basic_arithmetic",
  "name": "Basic Arithmetic", 
  "description": "Perform basic arithmetic operations: addition, subtraction, multiplication, division",
  "exampleCount": 4,
  "tags": ["arithmetic", "math", "basic", "deterministic"]
}
{
  "id": "advanced_math",
  "name": "Advanced Mathematics",
  "description": "Perform advanced mathematical operations like square roots and exponentiation",
  "exampleCount": 3,
  "tags": ["advanced", "math", "power", "roots", "deterministic"]
}
```

## 🎯 Key Takeaways

### **🔑 Agent Card Essentials**
1. **Dynamic Configuration**: Agent cards should reflect current capabilities
2. **Skill-Based Design**: Use skills to advertise specific capabilities  
3. **Tag Strategy**: Implement hierarchical, meaningful tags for discovery
4. **Example Diversity**: Provide varied, realistic usage examples
5. **Environment Integration**: Support configuration through environment variables

### **🚀 Discovery Best Practices**
- **Standard Endpoints**: Use `/.well-known/agent-card.json` for discovery
- **Health Integration**: Provide health checks for discovery validation
- **Self-Registration**: Support automatic registration with discovery services
- **Graceful Degradation**: Handle configuration errors gracefully
- **Runtime Updates**: Support dynamic capability changes

### **🛠️ Configuration Patterns**
- **Environment-Based**: Use environment variables for configuration
- **Validation**: Validate configuration on startup
- **Documentation**: Make configuration self-documenting
- **Fallbacks**: Provide sensible defaults and fallback behavior

## ⏭️ Next Steps

In [Part 3: Building Your First A2A Agent](./03-building-first-agent.md), we'll:
- Build a complete A2A agent from scratch
- Implement message handling and response generation
- Add skill-based processing and routing
- Create comprehensive testing and validation
- Deploy and integrate with orchestrator

You now understand A2A configuration and discovery! Ready to build your own agent?

---

*This tutorial is part of the Agent Network Sandbox educational series. All examples use our production A2A Math Operations Agent for real-world learning.*