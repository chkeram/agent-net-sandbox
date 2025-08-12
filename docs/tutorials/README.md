# Agent Network Sandbox Tutorial Series

Welcome to the comprehensive tutorial series for building agents using multiple communication protocols **and creating production-ready frontends**. These tutorials are designed to take you from zero knowledge to being able to create your own protocol-compliant agents and sophisticated React interfaces.

## 📚 Available Tutorial Series

### [Frontend Development Tutorial Series](./frontend/) 🚀 *NEW COMPREHENSIVE SERIES*
Master building production-ready React chat interfaces with real-time streaming, AI routing transparency, and multi-protocol agent communication.

**What you'll learn:**
- **Modern React patterns** with TypeScript, hooks, and component architecture
- **Real-time streaming** with Server-Sent Events and chunk-by-chunk rendering
- **AI routing transparency** showing intelligent agent selection decisions
- **Multi-protocol integration** supporting A2A, ACP, and custom protocols
- **Production patterns** including error handling, retry mechanisms, and state management
- **Advanced UX features** like message actions, conversation threading, and search

**Prerequisites:** Basic JavaScript knowledge, willingness to learn React

**🎯 47 comprehensive tutorials** covering beginner to expert level React development with real production code examples (1,935+ lines of TypeScript/React).

---

### [ACP Protocol Tutorial Series](./acp/)
Learn how to build agents using the AGNTCY Agent Connect Protocol (ACP).

**What you'll learn:**
- Understanding ACP fundamentals and architecture
- Configuring agents with manifest files and descriptors
- Building your first ACP-compliant agent
- Advanced features like streaming and orchestrator integration

**Prerequisites:** Basic Python knowledge, familiarity with REST APIs

---

### [A2A Protocol Tutorial Series](./a2a/)
Master the Agent-to-Agent Communication Protocol for building interconnected agents.

**What you'll learn:**
- A2A protocol concepts and JSON-RPC messaging
- Defining skills and capabilities with tags
- Building agents using the A2A SDK
- Advanced patterns including LLM integration

**Prerequisites:** Basic Python knowledge, understanding of JSON-RPC

---

## 🎯 Learning Path

### For Frontend Developers
1. **New to React?** Start with [Frontend Tutorial Phase 1](./frontend/phase-1-basics/) for React fundamentals
2. **Have React experience?** Jump to [Phase 2](./frontend/phase-2-api-integration/) for API integration patterns
3. **Want advanced features?** Go straight to [Phase 3](./frontend/phase-3-streaming/) for streaming and real-time features
4. **Building production apps?** Focus on [Advanced Features](./frontend/advanced-features/) and [Architecture](./frontend/architecture/) sections

### For Agent Developers (Backend)
1. Start with either protocol's Part 1 to understand fundamentals
2. Follow the tutorials sequentially
3. Run the example code from our implementations
4. Test with the provided curl commands
5. Build your own agent following the patterns

### For Full-Stack Developers
1. **Start with agents** - Choose ACP or A2A protocol tutorials
2. **Build the frontend** - Follow the Frontend Tutorial Series to create the UI
3. **Connect them together** - Use the orchestrator patterns from Phase 2-3 frontend tutorials

### For Experienced Developers
- **Agent protocols**: Jump to Part 3 of either series for hands-on building
- **Frontend patterns**: Review [Architecture Deep-Dives](./frontend/architecture/) and [Code Examples](./frontend/examples/)
- **Production deployment**: Check [Deployment guides](./frontend/deployment/) and advanced patterns

## 🛠️ Repository Examples

All tutorials reference real, working code from our implementations:

### Frontend Implementation
- **React Frontend**: `frontend/` - Production-ready React chat interface (1,935+ lines)
  - Real-time streaming with Server-Sent Events
  - AI routing transparency and decision display
  - Multi-protocol agent communication (A2A, ACP)
  - Advanced UX patterns and error handling

### Agent Implementations
- **ACP Example**: `agents/acp-hello-world/` - A multilingual greeting agent
- **A2A Example**: `agents/a2a-math-agent/` - A mathematical computation agent with LLM support
- **Orchestrator**: `agents/orchestrator/` - Multi-protocol agent orchestrator with AI routing

## 📖 Official Resources

### ACP Protocol
- [Official Documentation](https://docs.agntcy.org/)
- [Protocol Specification](https://spec.acp.agntcy.org/)
- [Python SDK](https://github.com/agntcy/acp-sdk)

### A2A Protocol
- [Official Website](https://a2a-protocol.org/)
- [Protocol Specification](https://a2a-protocol.org/latest/specification/)
- [Python SDK](https://github.com/a2aproject/a2a-python)

## 🤝 Contributing

Found an issue or want to improve the tutorials? We welcome contributions!
- Report issues in our [GitHub repository](https://github.com/chkeram/agent-net-sandbox/issues)
- Submit improvements via pull requests
- Share your agent implementations as examples

## 📝 License

These tutorials are part of the Agent Network Sandbox project, licensed under Apache 2.0.

## 🎊 **What Makes This Tutorial Series Special**

This isn't just another tutorial collection - it's based on **real production code** from a working multi-protocol agent system:

- **47 comprehensive tutorials** covering everything from React basics to advanced streaming patterns
- **1,935+ lines of production TypeScript/React code** that you can study and learn from
- **Real agent implementations** using official protocol SDKs (A2A, ACP)
- **Complete examples** of complex patterns like AI routing, streaming UIs, and error handling
- **Battle-tested patterns** used in actual production applications

Whether you're building your first React app or architecting a complex agent communication system, these tutorials provide practical, proven approaches that work in real applications.

---

## 🚀 **Ready to Start?**

### 🎨 **Frontend Developer?** 
Start with the [Frontend Development Tutorial Series](./frontend/) - 47 tutorials covering modern React development

### 🤖 **Agent Developer?** 
Choose your protocol: [ACP](./acp/) or [A2A](./a2a/) and begin with Part 1

### 🎯 **Full-Stack Developer?** 
Begin with agent protocols, then build the frontend to connect everything together

**Every tutorial includes working code examples you can run and modify!**