# ACP Protocol Tutorial Series

## 📚 Complete Learning Path for Agent Connect Protocol

This comprehensive tutorial series will take you from understanding the basics of the Agent Connect Protocol (ACP) to building production-ready agents with advanced features.

## 🎯 Who This Is For

- **Developers** wanting to build ACP-compliant agents
- **System Architects** designing multi-agent systems
- **Students** learning about agent protocols
- **Teams** implementing the AGNTCY Internet of Agents

## 📖 Tutorial Structure

### [Part 1: Understanding ACP Fundamentals](./01-understanding-acp.md)
**Duration: 45 minutes**

Learn the core concepts of ACP, understand the five required endpoints, and explore our real Hello World agent implementation.

**You'll learn:**
- What ACP is and why it matters
- The five required endpoints (`/auth`, `/schema`, `/config`, `/invoke`, `/capabilities`)
- How to read and understand ACP agent code
- Testing agents with curl commands

---

### [Part 2: Configuration & Discovery](./02-configuration-discovery.md)
**Duration: 60 minutes**

Master agent configuration files, understand discovery mechanisms, and learn how agents advertise their capabilities.

**You'll learn:**
- `agent-manifest.yaml` structure and purpose
- `acp-descriptor.json` for protocol compliance
- Tag-based discovery patterns
- Integration with orchestrator discovery

---

### [Part 3: Building Your First ACP Agent](./03-building-first-agent.md)
**Duration: 90 minutes**

Build a complete Weather Advisor Agent from scratch with all required endpoints, proper error handling, and Docker deployment.

**You'll learn:**
- Setting up an ACP agent project
- Implementing all five required endpoints
- Using Pydantic for type validation
- Testing and deploying your agent

---

### [Part 4: Advanced Features](./04-advanced-features.md)
**Duration: 90 minutes**

Explore streaming responses, advanced configuration management, orchestrator integration, and production deployment strategies.

**You'll learn:**
- Streaming for real-time updates
- Caching and performance optimization
- Production error handling
- Monitoring and metrics
- Security best practices

## 🛠️ Prerequisites

### Required
- Python 3.11+ installed
- Basic understanding of REST APIs
- Familiarity with JSON and YAML

### Recommended
- Docker and Docker Compose
- Basic FastAPI knowledge
- Understanding of async programming

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/chkeram/agent-net-sandbox.git
   cd agent-net-sandbox
   ```

2. **Start the example agent**
   ```bash
   docker-compose up acp-hello-world
   ```

3. **Test it's working**
   ```bash
   curl http://localhost:8000/health
   ```

4. **Begin with Part 1** and follow the tutorials sequentially

## 📂 Repository Structure

```
docs/tutorials/acp/
├── README.md                    # This file
├── 01-understanding-acp.md      # Part 1: Fundamentals
├── 02-configuration-discovery.md # Part 2: Configuration
├── 03-building-first-agent.md   # Part 3: Building
├── 04-advanced-features.md      # Part 4: Advanced
└── examples/                    # Code examples
    ├── minimal-agent.py         # Minimal ACP agent
    ├── config-examples.yaml     # Configuration samples
    └── test-commands.sh         # Testing scripts
```

## 💡 Learning Tips

### For Beginners
- Start with Part 1 and work through sequentially
- Run the Hello World agent while reading
- Experiment with the curl commands
- Don't skip the exercises

### For Experienced Developers
- You can skip to Part 3 for hands-on building
- Part 4 covers production considerations
- Check examples folder for quick references
- Focus on patterns that differ from REST APIs

## 🔗 Quick Reference

### Five Required Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth` | GET | Authentication requirements |
| `/schema` | GET | Input/output/config schemas |
| `/config` | POST | Store configuration |
| `/invoke` | POST | Execute agent task |
| `/capabilities` | GET | Discover agent abilities |

### Key Concepts

- **Protocol Compliance**: Agents must implement all five endpoints
- **Schema-Driven**: All data validated against JSON schemas
- **Stateless Design**: Each request is independent
- **Discovery-Enabled**: Agents advertise capabilities via tags

## 📝 Example: Minimal ACP Agent

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

@app.get("/auth")
async def auth():
    return {"type": "none", "description": "No auth required"}

@app.get("/schema")
async def schema():
    return {
        "input": {"type": "object"},
        "output": {"type": "object"},
        "config": {"type": "object"}
    }

@app.post("/config")
async def config(data: dict):
    return {"config_id": "cfg_123", "status": "created"}

@app.post("/invoke")
async def invoke(data: dict):
    return {"output": {"result": "Hello, ACP!"}}

@app.get("/capabilities")
async def capabilities():
    return {"capabilities": [{"name": "hello"}]}
```

## 🧪 Testing Your Knowledge

After completing the series, you should be able to:

- [ ] Explain what ACP is and its benefits
- [ ] List all five required endpoints and their purposes
- [ ] Build an ACP agent from scratch
- [ ] Configure agent discovery with tags
- [ ] Implement streaming responses
- [ ] Deploy agents to production
- [ ] Handle errors gracefully
- [ ] Monitor agent performance

## 🤝 Getting Help

- **GitHub Issues**: [Report problems or ask questions](https://github.com/chkeram/agent-net-sandbox/issues)
- **Official Docs**: [AGNTCY Documentation](https://docs.agntcy.org/)
- **Protocol Spec**: [ACP Specification](https://spec.acp.agntcy.org/)

## 📜 License

This tutorial series is part of the Agent Network Sandbox project, licensed under Apache 2.0.

---

**Ready to start?** → [Begin with Part 1: Understanding ACP Fundamentals](./01-understanding-acp.md)

**Have questions?** → [Open an issue](https://github.com/chkeram/agent-net-sandbox/issues/new)