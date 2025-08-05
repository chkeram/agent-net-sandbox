# 🧮 A2A Math Operations Agent

A mathematical computation agent built using the **A2A Protocol SDK** that provides arithmetic and advanced mathematical operations through agent-to-agent communication.

## 🎯 Features

### 🤖 **Dual-Mode Operation**
- **LLM-Powered**: Natural language mathematical problem solving using OpenAI, Anthropic, or Gemini
- **Deterministic Fallback**: Reliable pattern-based calculations when LLM is unavailable
- **Automatic Fallback**: Seamlessly switches between modes based on configuration and availability

### Mathematical Operations
- **Basic Arithmetic**: Addition, subtraction, multiplication, division
- **Advanced Math**: Square root, exponentiation, trigonometry
- **Natural Language**: Complex queries like "What is the derivative of x^2?" or "Convert 32°F to Celsius"
- **Pattern Recognition**: Supports expressions like "5 + 3", "sqrt(16)", "2^3"

### A2A Protocol Integration
- Built with official `a2a-sdk` v0.3.0
- Supports agent-to-agent communication
- Auto-discoverable by A2A-compatible orchestrators
- Dynamic capabilities based on LLM availability
- Standard A2A agent card specification

## 🚀 Quick Start

### Local Development

```bash
# Navigate to agent directory
cd agents/a2a-math-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the agent
python math_agent.py
```

The agent will start on `http://localhost:8002`

### 🤖 **LLM Configuration (Optional)**

To enable AI-powered mathematical problem solving, configure one or more LLM providers:

#### OpenAI Configuration
```bash
export OPENAI_API_KEY="your-openai-api-key"
export LLM_PROVIDER="openai"
export OPENAI_MODEL="gpt-4o-mini"  # optional
```

#### Anthropic Configuration
```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export LLM_PROVIDER="anthropic"
export ANTHROPIC_MODEL="claude-3-haiku-20240307"  # optional
```

#### Gemini Configuration
```bash
export GEMINI_API_KEY="your-gemini-api-key"
export LLM_PROVIDER="gemini"
export GEMINI_MODEL="gemini-1.5-flash"  # optional
```

#### Using .env File
```bash
# Copy the example file and edit it
cp .env.example .env
# Edit .env with your API keys
```

**Note**: If no LLM is configured, the agent automatically falls back to deterministic calculations.

### Docker

```bash
# Build and run from project root (deterministic mode)
docker-compose up a2a-math-agent

# Or with LLM support (set environment variables first)
export OPENAI_API_KEY="your-key"
docker-compose up a2a-math-agent
```

## 📡 A2A Protocol Endpoints

- **Agent Card**: `GET /.well-known/agent-card`
- **Send Message**: `POST /send-message`
- **Health Check**: Standard A2A health endpoints

## 🧪 Testing

```bash
# Run basic functionality tests
python test_agent.py
```

## 📋 Usage Examples

### 🧮 **Deterministic Mode** (Pattern-Based)
- `5 + 3` → `🧮 Calc: 5.0 + 3.0 = 8.0`
- `10 - 4` → `🧮 Calc: 10.0 - 4.0 = 6.0`
- `6 * 7` → `🧮 Calc: 6.0 * 7.0 = 42.0`
- `15 / 3` → `🧮 Calc: 15.0 / 3.0 = 5.0`
- `sqrt(16)` → `🧮 Calc: √16.0 = 4.0`
- `2^3` → `🧮 Calc: 2.0^3.0 = 8.0`

### 🤖 **LLM-Powered Mode** (Natural Language)
- "What is the derivative of x²?" → `🤖 LLM: The derivative of x² is 2x`
- "Convert 32 Fahrenheit to Celsius" → `🤖 LLM: 32°F = 0°C`
- "Solve 2x + 5 = 13 for x" → `🤖 LLM: x = 4`
- "What is the area of a circle with radius 5?" → `🤖 LLM: A = πr² = 25π ≈ 78.54`
- "Calculate sin(π/2)" → `🤖 LLM: sin(π/2) = 1`

### **Automatic Fallback**
- Complex queries fall back to deterministic when LLM unavailable
- Simple expressions work in both modes
- Seamless user experience regardless of configuration

## 🏗️ Architecture

```
┌─────────────────────────────┐
│     A2A Protocol Layer      │  ← A2A SDK (JSON-RPC/HTTP)
│        (a2a-sdk)            │
├─────────────────────────────┤
│    Request Handler Layer    │  ← DefaultRequestHandler
│   (Task & Queue Management) │
├─────────────────────────────┤
│    Agent Executor Layer     │  ← MathAgent (AgentExecutor)
│   (Message Processing)      │
├─────────────────────────────┤
│   Mathematical Operations   │  ← MathOperations
│     (Computation Logic)     │
└─────────────────────────────┘
```

## 🔧 Technical Details

### Dependencies
- **a2a-sdk**: Official A2A Protocol SDK
- **langchain-core**: Tool framework (future expansion)
- **uvicorn**: ASGI server
- **pydantic**: Data validation

### Agent Capabilities
- **Skills**: Basic Arithmetic, Advanced Mathematics
- **Input/Output Modes**: Text-based
- **Protocol Version**: A2A v0.3.0
- **Transport**: JSON-RPC over HTTP

## 🤝 Integration

This agent is designed to work with:
- **Multi-Protocol Agent Orchestrator**: Automatic discovery and routing
- **Other A2A Agents**: Direct agent-to-agent communication
- **A2A-compatible clients**: Standard protocol compliance

## 📄 License

Apache 2.0 - See [LICENSE](../../LICENSE) for details.

## 🔗 References

- [A2A Protocol Specification](https://a2a-protocol.org/latest/)
- [A2A Python SDK](https://github.com/a2aproject/a2a-python)
- [Agent Network Sandbox](../../README.md)