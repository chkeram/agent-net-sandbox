# Part 1: Understanding A2A Protocol Fundamentals

## 🎯 Learning Objectives

By the end of this tutorial, you will understand:
- What the Agent-to-Agent (A2A) Protocol is and why it matters
- How A2A differs from other agent communication protocols
- The core A2A message structure and JSON-RPC transport
- Key A2A concepts: skills, agent cards, and message parts
- Real-world A2A implementation through our Math Operations Agent

## 📚 Prerequisites

- Basic understanding of JSON and HTTP
- Familiarity with agent concepts and communication patterns
- Python 3.11+ installed for hands-on examples
- Basic knowledge of APIs and web services

## 🤝 What is the Agent-to-Agent Protocol?

The **Agent-to-Agent (A2A) Protocol** is a standardized communication protocol designed specifically for enabling seamless communication between AI agents. Unlike human-to-agent protocols, A2A is optimized for agent-to-agent interactions with:

### 🎯 **Core Design Principles**

1. **Agent-Native**: Built specifically for AI agent communication patterns
2. **Structured Messaging**: Standardized message formats with roles and parts
3. **Skill-Based Discovery**: Agents advertise capabilities through well-defined skills
4. **Transport Agnostic**: Works over HTTP, WebSocket, or other transport layers
5. **Extensible**: Supports various content types and future protocol enhancements

### 🔄 **A2A vs Other Protocols**

| Aspect | **A2A Protocol** | **ACP Protocol** | **MCP Protocol** |
|--------|------------------|------------------|------------------|
| **Primary Use** | Agent-to-Agent communication | Human-to-Agent (AGNTCY standard) | Model Context Protocol (Anthropic) |
| **Transport** | JSON-RPC over HTTP/WebSocket | HTTP REST endpoints | JSON-RPC over stdio/HTTP |
| **Message Structure** | Role-based parts system | Input/output schemas | Tools and resources |
| **Discovery** | Agent cards with skills | Capabilities endpoint | Tool discovery |
| **Focus** | Inter-agent collaboration | Human interaction patterns | Model context management |

## 🏗️ A2A Architecture Overview

### **Message Flow Architecture**
```
┌─────────────────┐    A2A Message     ┌─────────────────┐
│   Source Agent │ ──────────────────▶ │  Target Agent   │
│                 │   (JSON-RPC)       │                 │
└─────────────────┘                    └─────────────────┘
         │                                       │
         │ 1. Discovery via agent card           │ 3. Process message
         │ 2. Send structured message            │ 4. Return structured response
         │                                       │
┌─────────────────────────────────────────────────────────┐
│              A2A Transport Layer                        │
│          (HTTP, WebSocket, etc.)                        │
└─────────────────────────────────────────────────────────┘
```

### **Key Components**

1. **Agent Card** (`/.well-known/agent-card.json`) - Agent discovery and capabilities
2. **Message Structure** - Standardized request/response format with roles and parts
3. **Skills System** - Defined capabilities with examples and metadata
4. **Transport Layer** - JSON-RPC over various protocols

## 📋 Core A2A Message Structure

A2A messages follow a structured format with roles and parts:

### **Basic Message Format**
```json
{
  "messageId": "unique-message-id",
  "role": "user",
  "parts": [
    {
      "kind": "text",
      "text": "Your message content here"
    }
  ]
}
```

### **Complete JSON-RPC Request**
```json
{
  "jsonrpc": "2.0",
  "method": "message/send",
  "id": "request-id",
  "params": {
    "message": {
      "messageId": "msg-123",
      "role": "user",
      "parts": [
        {"kind": "text", "text": "What is 15 + 27?"}
      ]
    }
  }
}
```

### **A2A Response Format**
```json
{
  "jsonrpc": "2.0",
  "id": "request-id",
  "result": {
    "messageId": "response-456",
    "role": "agent", 
    "parts": [
      {"kind": "text", "text": "🧮 Calc: 15.0 + 27.0 = 42.0"}
    ]
  }
}
```

## 🎲 Message Roles and Parts

### **Roles**
- **`user`**: Messages from the requesting agent
- **`agent`**: Responses from the target agent
- **`system`**: System-level messages (future extension)

### **Part Types**
- **`text`**: Text content (primary type)
- **`image`**: Image data (future extension)
- **`file`**: File attachments (future extension)
- **`data`**: Structured data (future extension)

### **Multi-Part Message Example**
```json
{
  "messageId": "complex-msg",
  "role": "user",
  "parts": [
    {"kind": "text", "text": "Calculate the result of "},
    {"kind": "text", "text": "25 * 8"},
    {"kind": "text", "text": " and explain the process"}
  ]
}
```

## 🗃️ Agent Card Structure

The agent card is the discovery mechanism for A2A agents. Here's our real Math Agent card:

```json
{
  "name": "A2A Math Operations Agent",
  "version": "0.1.0",
  "description": "A mathematical computation agent using the A2A protocol with deterministic mathematical calculations",
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

### **Agent Card Fields Explained**

| Field | Purpose | Example |
|-------|---------|---------|
| **name** | Human-readable agent name | "A2A Math Operations Agent" |
| **version** | Agent version (semver) | "0.1.0" |
| **description** | Agent purpose and capabilities | "Mathematical computation agent..." |
| **protocolVersion** | A2A protocol version | "0.3.0" |
| **preferredTransport** | Transport preference | "JSONRPC" |
| **url** | Base agent URL | "http://localhost:8002" |
| **skills** | Array of agent capabilities | [skill objects] |
| **defaultInputModes** | Supported input types | ["text"] |
| **defaultOutputModes** | Supported output types | ["text"] |

## 🛠️ Skills Definition

Skills are the core of A2A agent capabilities:

### **Skill Structure**
```json
{
  "id": "skill_identifier",
  "name": "Human Readable Name",
  "description": "What this skill does",
  "examples": ["example input 1", "example input 2"],
  "tags": ["category", "type", "metadata"]
}
```

### **Skill Design Best Practices**
1. **Clear IDs**: Use snake_case identifiers
2. **Descriptive Names**: Human-readable skill names
3. **Detailed Descriptions**: Explain what the skill does
4. **Concrete Examples**: Show real input patterns
5. **Meaningful Tags**: Enable discovery and categorization

## 🧪 Real-World Example: Our Math Agent

Let's explore how A2A works with our production Math Operations Agent:

### **1. Agent Discovery**
```bash
# Get the agent card
curl -s http://localhost:8002/.well-known/agent-card.json | jq '{
  name, 
  version,
  skills: [.skills[] | {id, name, description}]
}'
```

**Expected Output:**
```json
{
  "name": "A2A Math Operations Agent",
  "version": "0.1.0", 
  "skills": [
    {
      "id": "basic_arithmetic",
      "name": "Basic Arithmetic",
      "description": "Perform basic arithmetic operations: addition, subtraction, multiplication, division"
    },
    {
      "id": "advanced_math",
      "name": "Advanced Mathematics", 
      "description": "Perform advanced mathematical operations like square roots and exponentiation"
    }
  ]
}
```

### **2. Basic A2A Communication**
```bash
# Send a math problem to the agent
curl -s -X POST http://localhost:8002/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "id": "math-test-1",
    "params": {
      "message": {
        "messageId": "msg-addition", 
        "role": "user",
        "parts": [{"kind": "text", "text": "15 + 27"}]
      }
    }
  }' | jq '.result.parts[0].text'
```

**Expected Output:**
```
"🧮 Calc: 15.0 + 27.0 = 42.0"
```

### **3. Advanced Mathematics Example**
```bash
# Test advanced math skill
curl -s -X POST http://localhost:8002/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", 
    "method": "message/send",
    "id": "math-test-2",
    "params": {
      "message": {
        "messageId": "msg-sqrt",
        "role": "user", 
        "parts": [{"kind": "text", "text": "sqrt(144)"}]
      }
    }
  }' | jq '.result.parts[0].text'
```

**Expected Output:**
```
"🧮 Calc: √144.0 = 12.0"
```

## 🔍 A2A Protocol Features in Action

### **1. Multi-Part Messages**
A2A supports breaking messages into multiple parts:

```bash
curl -s -X POST http://localhost:8002/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send", 
    "id": "multi-part-test",
    "params": {
      "message": {
        "messageId": "msg-multi",
        "role": "user",
        "parts": [
          {"kind": "text", "text": "Calculate "},
          {"kind": "text", "text": "20 * 3"}
        ]
      }
    }
  }' | jq '.result.parts[0].text'
```

### **2. Error Handling**
A2A provides structured error responses:

```bash
# Test division by zero
curl -s -X POST http://localhost:8002/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "id": "error-test",
    "params": {
      "message": {
        "messageId": "msg-error",
        "role": "user",
        "parts": [{"kind": "text", "text": "10 / 0"}]
      }
    }
  }' | jq '.result.parts[0].text'
```

**Expected Output:**
```
"🧮 Calc: Division by zero is not allowed"
```

## 📊 A2A vs Traditional APIs

### **Traditional REST API**
```bash
# Traditional approach - rigid endpoints
POST /calculate
{
  "operation": "add",
  "a": 15, 
  "b": 27
}
```

### **A2A Protocol Approach**
```bash
# A2A approach - natural language + structure
POST /
{
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [{"kind": "text", "text": "15 + 27"}]
    }
  }
}
```

### **Key Advantages of A2A**
1. **Natural Communication**: Agents can communicate naturally
2. **Flexible Input**: Multiple ways to express the same request
3. **Extensible**: Easy to add new content types and capabilities
4. **Discoverable**: Skills and capabilities are self-describing
5. **Standardized**: Consistent format across all A2A agents

## 🔧 A2A Implementation Patterns

Our Math Agent demonstrates several A2A patterns:

### **1. Dual-Mode Processing**
```python
# Simplified pattern from our agent
class MathAgent:
    async def process_message(self, message):
        text = self.extract_text(message.parts)
        
        # Try LLM processing first
        if self.llm_service.is_available():
            try:
                return await self.llm_service.process(text)
            except Exception:
                pass  # Fall back to deterministic
        
        # Deterministic fallback
        return self.math_operations.process(text)
```

### **2. Skill-Based Routing**
```python
# Skills determine what the agent can handle
skills = [
    {
        "id": "basic_arithmetic",
        "examples": ["5 + 3", "10 - 4"], 
        "pattern": r'\d+\s*[+\-*/÷×]\s*\d+'
    },
    {
        "id": "advanced_math",
        "examples": ["sqrt(16)", "2^3"],
        "pattern": r'(sqrt|√|\^|\*\*)'
    }
]
```

### **3. Response Formatting**
```python
# Consistent response format
def format_response(self, result, method):
    if method == "llm":
        return f"🤖 LLM: {result}"
    else:
        return f"🧮 Calc: {result}"
```

## 🎓 Hands-On Exercise

Let's test different A2A capabilities:

### **Exercise 1: Basic Arithmetic**
```bash
# Test each operation type
for operation in "5 + 3" "10 - 4" "6 * 7" "15 / 3"; do
  echo "Testing: $operation"
  curl -s -X POST http://localhost:8002/ \
    -H "Content-Type: application/json" \
    -d "{
      \"jsonrpc\": \"2.0\",
      \"method\": \"message/send\",
      \"id\": \"test\",
      \"params\": {
        \"message\": {
          \"messageId\": \"msg\",
          \"role\": \"user\", 
          \"parts\": [{\"kind\": \"text\", \"text\": \"$operation\"}]
        }
      }
    }" | jq -r '.result.parts[0].text'
  echo
done
```

### **Exercise 2: Advanced Math**
```bash
# Test advanced operations
for operation in "sqrt(25)" "2^4" "√49"; do
  echo "Testing: $operation"
  curl -s -X POST http://localhost:8002/ \
    -H "Content-Type: application/json" \
    -d "{
      \"jsonrpc\": \"2.0\",
      \"method\": \"message/send\", 
      \"id\": \"test\",
      \"params\": {
        \"message\": {
          \"messageId\": \"msg\",
          \"role\": \"user\",
          \"parts\": [{\"kind\": \"text\", \"text\": \"$operation\"}]
        }
      }
    }" | jq -r '.result.parts[0].text'
  echo
done
```

### **Exercise 3: Error Handling**
```bash
# Test error cases
for operation in "10 / 0" "sqrt(-4)" "invalid operation"; do
  echo "Testing error case: $operation"
  curl -s -X POST http://localhost:8002/ \
    -H "Content-Type: application/json" \
    -d "{
      \"jsonrpc\": \"2.0\",
      \"method\": \"message/send\",
      \"id\": \"test\", 
      \"params\": {
        \"message\": {
          \"messageId\": \"msg\",
          \"role\": \"user\",
          \"parts\": [{\"kind\": \"text\", \"text\": \"$operation\"}]
        }
      }
    }" | jq -r '.result.parts[0].text'
  echo
done
```

## 📚 A2A Specification References

### **Official A2A Resources**
- **[A2A Protocol Specification](https://a2a-protocol.org/latest/)** - Complete protocol documentation
- **[A2A Python SDK](https://github.com/a2aproject/a2a-python)** - Official Python implementation
- **[A2A Message Format](https://a2a-protocol.org/latest/message-format/)** - Detailed message structure

### **Implementation Examples**
- **[Our Math Agent](../../agents/a2a-math-agent/)** - Production A2A implementation
- **[A2A SDK Examples](https://github.com/a2aproject/a2a-python/tree/main/examples)** - Official examples
- **[Agent Network Sandbox](../../README.md)** - Multi-protocol environment

## 🎯 Key Takeaways

### **🔑 A2A Core Concepts**
1. **Agent-to-Agent Focus**: Optimized for AI agent communication
2. **Structured Messages**: Role-based parts system with extensible content types
3. **Skill-Based Discovery**: Agents advertise capabilities through well-defined skills
4. **JSON-RPC Transport**: Standardized request/response over various transport layers
5. **Extensible Design**: Supports future enhancements and content types

### **🚀 A2A Advantages**
- **Natural Communication**: Agents can communicate in flexible, natural ways
- **Self-Describing**: Agent cards provide complete capability information
- **Transport Agnostic**: Works over HTTP, WebSocket, or custom transports
- **Standardized**: Consistent format across all A2A implementations
- **Future-Proof**: Extensible for new content types and capabilities

### **🛠️ Implementation Patterns**
- **Multi-Part Messages**: Break complex messages into structured parts
- **Skill-Based Routing**: Use skills to determine agent capabilities
- **Graceful Degradation**: Handle errors and provide helpful responses
- **Discovery Integration**: Support agent card-based discovery

## ⏭️ Next Steps

In [Part 2: Configuration & Discovery](./02-configuration-discovery.md), we'll explore:
- A2A agent card structure and customization
- Discovery mechanisms and skill definition
- Agent registration and capability advertisement
- Integration with orchestrators and discovery services
- Best practices for A2A agent configuration

You now understand the fundamentals of A2A protocol! Ready to dive deeper into configuration and discovery?

---

*This tutorial is part of the Agent Network Sandbox educational series. All examples use our production A2A Math Operations Agent for real-world learning.*