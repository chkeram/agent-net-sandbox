# Agent Network Sandbox - React Frontend

A production-ready chat interface for the Multi-Protocol Agent Orchestrator with advanced real-time streaming and AI routing transparency.

## 🎯 Production Status: Phase 1-3 Complete ✅

### Advanced Features Delivered
- **🎨 Modern Chat Interface** - Professional UI with markdown rendering and code highlighting
- **⚡ Real-time Streaming** - Server-Sent Events with live chunk-by-chunk rendering  
- **🧠 AI Routing Transparency** - Expandable reasoning display showing agent selection logic
- **🔄 Smart Retry System** - Failed message recovery with history management
- **📋 Message Actions** - Copy, regenerate, and action buttons always accessible
- **🔌 Multi-Protocol Support** - Unified interface for ACP, A2A, and future protocols
- **🚀 Production Ready** - Error boundaries, loading states, comprehensive error handling

## Tech Stack

- **React 18** with functional components and hooks
- **Vite** for fast build tooling and hot reload
- **TypeScript** for complete type safety (1,935+ lines)
- **Tailwind CSS** for utility-first styling
- **Server-Sent Events** for real-time streaming
- **react-markdown** with syntax highlighting
- **Docker** multi-stage builds for production deployment

## 🚀 Quick Start

### Option 1: Docker Production (Recommended)
```bash
# From project root
docker-compose up -d

# Access at: http://localhost:3000
```

### Option 2: Docker Development (Hot Reload)
```bash
# Start backend services
docker-compose up -d orchestrator acp-hello-world a2a-math-agent

# Start frontend in dev mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up frontend

# Access at: http://localhost:5173 (with hot reload)
```

### Option 3: Local Development
```bash
# Prerequisites: Node.js 18+, backend services running
npm install
npm run dev

# Access at: http://localhost:5173
```

### Production Build
```bash
# Create optimized build
npm run build

# Preview production build
npm run preview

# Docker production image
docker build -t agent-frontend .
```

## 🏗️ Production Architecture

### Component Hierarchy
```
StreamingChatContainer.tsx (374 LOC) - Main interface
├── MessageList.tsx (auto-scroll, pagination)
│   └── Message.tsx (182 LOC) - Markdown, actions, syntax highlighting
│       └── RoutingReasoning.tsx - AI decision transparency
├── ChatInput.tsx - Smart input with shortcuts
└── useStreamingOrchestrator.ts (265 LOC) - Advanced state management
    ├── orchestratorApi.ts (307 LOC) - API service layer
    └── streamingApi.ts (197 LOC) - SSE streaming
```

### Project Structure
```
frontend/
├── src/
│   ├── components/Chat/          # Core chat components
│   │   ├── StreamingChatContainer.tsx    # Advanced chat with streaming
│   │   ├── ChatContainer.tsx            # Basic chat container  
│   │   ├── MessageList.tsx             # Message display with auto-scroll
│   │   ├── Message.tsx                 # Message with markdown & actions
│   │   ├── RoutingReasoning.tsx        # AI routing transparency
│   │   └── ChatInput.tsx              # Input with shortcuts
│   ├── hooks/                    # Custom React hooks
│   │   ├── useStreamingOrchestrator.ts # Advanced streaming state
│   │   └── useOrchestrator.ts         # Basic API integration
│   ├── services/                # API service layer
│   │   ├── orchestratorApi.ts    # Main orchestrator API
│   │   └── streamingApi.ts       # Server-Sent Events
│   ├── types/                   # TypeScript definitions
│   │   ├── chat.ts             # Chat-related types
│   │   └── agent.ts            # Agent-related types
│   └── utils/                  # Utility functions
├── Dockerfile                  # Multi-stage production build
├── nginx.conf                 # Production nginx configuration
├── docker-compose.dev.yml     # Development override
├── package.json              # Dependencies and scripts
└── README.md                # This file
```

## ✅ Implementation Status: Production Complete

### Phase 1-3 Delivered ✅
- **✅ Modern Chat Interface** - Professional UI with TypeScript and Tailwind CSS
- **✅ Real-time Streaming** - Server-Sent Events with chunk-by-chunk rendering
- **✅ AI Routing Transparency** - Expandable reasoning display with confidence scores  
- **✅ Multi-Protocol Integration** - Connects to ACP, A2A, and orchestrator APIs
- **✅ Advanced UX Features** - Message retry, copy actions, error boundaries
- **✅ Production Deployment** - Docker multi-stage builds with nginx
- **✅ Comprehensive Error Handling** - Graceful fallbacks and user-friendly errors

### Backend Integration ✅
Connected to these orchestrator endpoints:
- ✅ `POST /process` - Message processing with agent routing
- ✅ `GET /stream` - Real-time streaming responses  
- ✅ `GET /agents` - Agent discovery and capabilities
- ✅ `GET /health` - Service health monitoring

### Production Features ✅
- **✅ Docker Integration** - Production and development containers
- **✅ Performance Optimized** - Code splitting, lazy loading, efficient rendering
- **✅ Type Safety** - Complete TypeScript coverage (1,935+ lines)
- **✅ Responsive Design** - Works across desktop, tablet, and mobile
- **✅ Error Boundaries** - Comprehensive error handling and recovery
- **✅ Security Headers** - Production nginx configuration with CORS

## 🧪 Testing the Interface

### Quick Test
1. **Start services**: `docker-compose up -d`
2. **Open browser**: http://localhost:3000
3. **Try queries**:
   - "Hello there!" → Routes to ACP Hello World Agent
   - "What is 2 + 2?" → Routes to A2A Math Agent
   - "Calculate 15 * 7" → Routes to A2A Math Agent with streaming

### Expected Behavior
- ✅ Messages send immediately and appear in chat
- ✅ AI routing decisions show with confidence scores
- ✅ Responses stream in real-time (when supported)
- ✅ Failed messages can be retried
- ✅ Code blocks have copy buttons
- ✅ Routing reasoning can be expanded for transparency

## 📚 Learn More

- **[Complete Tutorial Series](../docs/tutorials/frontend/)** - 47 comprehensive guides
- **[Frontend Setup Guide](../FRONTEND_SETUP.md)** - Detailed setup instructions
- **[Manual Setup Guide](../MANUAL_SETUP.md)** - Development environment setup

---

**🎉 Status: Production Ready** - Full-stack multi-protocol agent communication platform