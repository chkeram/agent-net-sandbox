# 🎨 Frontend Setup Guide

Complete guide for setting up and developing the React Frontend interface for the Agent Network Sandbox.

## 🚀 Quick Frontend Setup

### Option 1: Docker Production (Fastest)
```bash
# Clone and start everything
git clone https://github.com/your-org/agent-net-sandbox.git
cd agent-net-sandbox
docker-compose up -d

# Visit: http://localhost:3000
```

### Option 2: Docker Development Mode 
```bash
# Frontend only in dev mode
docker-compose up -d orchestrator acp-hello-world a2a-math-agent
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up frontend
# Visit: http://localhost:5173 (with hot reload)

# OR everything in dev mode (enhanced debugging)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
# Visit: http://localhost:5173 (with hot reload + enhanced logging)
```

### Option 3: Local Development
```bash
# Start backend services
docker-compose up -d orchestrator acp-hello-world a2a-math-agent

# Start frontend locally
cd frontend
npm install
npm run dev

# Visit: http://localhost:5173
```

## 🎯 What You Get

The React Frontend provides a modern chat interface with these features:

### 🌟 Core Features
- **Real-time Chat Interface** - Modern messaging UI with markdown support
- **Server-Sent Events Streaming** - Live message streaming as agents respond
- **AI Routing Transparency** - See which agent was selected and why
- **Multi-Protocol Support** - Unified interface for ACP, A2A, MCP, and custom agents
- **Advanced UX Patterns** - Message retry, copy actions, error boundaries

### 🔧 Technical Features
- **TypeScript** - Full type safety with 1,935+ lines of production code
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Performance Optimized** - Lazy loading, code splitting, efficient rendering
- **Production Ready** - Error boundaries, loading states, comprehensive error handling

## 📋 Prerequisites

### Required Software
```bash
# Node.js 18+ and npm
node --version  # Should be 18+
npm --version   # Should be 8+

# Docker (for backend services)
docker --version
docker-compose --version
```

### Installation
```bash
# macOS
brew install node docker

# Ubuntu
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs docker.io docker-compose-plugin

# Windows
# Download Node.js from https://nodejs.org/
# Download Docker Desktop from https://www.docker.com/products/docker-desktop
```

## 🛠️ Development Setup

### 1. Start Backend Services
```bash
# Navigate to project root
cd agent-net-sandbox

# Start required backend services
docker-compose up -d orchestrator acp-hello-world a2a-math-agent

# Verify services are running
./scripts/test_all_agents.sh
```

### 2. Frontend Development
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Open browser to: http://localhost:5173
```

### 3. Development Workflow
```bash
# Code formatting and linting
npm run lint

# Type checking
npm run build  # Will show TypeScript errors if any

# Production build test
npm run build && npm run preview
```

## 🏗️ Architecture Overview

### Component Architecture
```
StreamingChatContainer.tsx (374 LOC)
├── MessageList.tsx           # Message display with auto-scroll
│   └── Message.tsx          # Individual message with markdown
│       └── RoutingReasoning.tsx  # AI decision transparency
├── ChatInput.tsx            # Message input with shortcuts
└── useStreamingOrchestrator # Custom hook (265 LOC)
    ├── orchestratorApi.ts   # API service layer (307 LOC)
    └── streamingApi.ts      # SSE streaming (197 LOC)
```

### Key Files
- **`StreamingChatContainer.tsx`** (374 LOC) - Main chat interface with advanced features
- **`useStreamingOrchestrator.ts`** (265 LOC) - Advanced streaming state management
- **`orchestratorApi.ts`** (307 LOC) - API service layer with error handling
- **`streamingApi.ts`** (197 LOC) - Server-Sent Events implementation
- **`Message.tsx`** (182 LOC) - Message component with markdown and actions
- **`RoutingReasoning.tsx`** - AI routing transparency display

## 🔌 API Integration

### Backend Requirements
The frontend expects these backend services to be running:

| Service | Port | Required | Purpose |
|---------|------|----------|---------|
| **Orchestrator** | 8004 | ✅ Yes | Main API for agent routing |
| **ACP Hello World** | 8000 | ✅ Yes | Greeting agent |
| **A2A Math Agent** | 8002 | ✅ Yes | Mathematical computation |

### API Endpoints Used
```bash
# Health check
GET http://localhost:8004/health

# Process message (basic)
POST http://localhost:8004/process
Content-Type: application/json
{"query": "Hello there!"}

# Stream message (advanced)
GET http://localhost:8004/stream?query=Hello

# Agent discovery
GET http://localhost:8004/agents
```

### Environment Configuration
```env
# frontend/.env (optional)
VITE_API_BASE_URL=http://localhost:8004
VITE_APP_TITLE=Agent Network Sandbox
VITE_APP_VERSION=1.0.0
NODE_ENV=development
```

## 🎨 Customization

### Themes and Styling
The frontend uses **Tailwind CSS** for styling:

```bash
# Customize colors, fonts, spacing
vim frontend/tailwind.config.js

# Add custom CSS
vim frontend/src/index.css
```

### Component Customization
```typescript
// Customize chat container
frontend/src/components/Chat/StreamingChatContainer.tsx

// Customize message display
frontend/src/components/Chat/Message.tsx

// Customize input handling
frontend/src/components/Chat/ChatInput.tsx
```

## 🧪 Testing the Interface

### Manual Testing
1. **Start backend services**: `docker-compose up -d orchestrator acp-hello-world a2a-math-agent`
2. **Start frontend**: `npm run dev` or use Docker
3. **Test different queries**:
   - "Hello there!" → Should route to ACP Hello World Agent
   - "What is 2 + 2?" → Should route to A2A Math Agent
   - "Calculate the square root of 144" → Should route to A2A Math Agent
   - "Say hello in Spanish" → Should route to ACP Hello World Agent

### Expected Behavior
- ✅ **Messages send immediately** and show in chat
- ✅ **AI routing decisions** display with confidence scores
- ✅ **Streaming responses** appear in real-time (if supported)
- ✅ **Error handling** shows friendly error messages
- ✅ **Retry mechanism** allows retrying failed messages
- ✅ **Copy functionality** works on code blocks and messages

## 🚀 Production Deployment

### Docker Production Build
```bash
# Build production image
docker-compose build frontend

# Start production container
docker-compose up -d frontend

# Access at: http://localhost:3000
```

### Manual Production Build
```bash
# Create optimized build
npm run build

# Preview locally
npm run preview

# Deploy dist/ directory to your web server
```

### Nginx Configuration
The included `frontend/nginx.conf` provides:
- **Static file serving** with caching
- **API proxying** to orchestrator backend
- **Client-side routing** support for React Router
- **Security headers** and CORS handling
- **Health check endpoint** at `/health`

## 🔧 Advanced Configuration

### Development Mode Features
```bash
# Frontend only development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up frontend

# Full development mode (all services)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Features:
# - Hot reload for all source changes
# - Source maps for debugging
# - Development error overlays
# - Fast refresh for React components
# - Enhanced backend logging (DEBUG level)
# - Development environment variables
```

### Production Optimizations
```bash
# Production build includes:
# - Code splitting and tree shaking
# - Asset optimization and compression
# - Gzip compression via nginx
# - Static asset caching
# - Security headers
```

### Performance Monitoring
```typescript
// Built-in performance features:
// - useCallback/useMemo for render optimization
// - Lazy loading for large components
// - Efficient re-rendering patterns
// - Memory leak prevention with cleanup
```

## 🐛 Troubleshooting

### Common Issues

#### "Connection refused" errors
```bash
# Verify backend services are running
curl http://localhost:8004/health

# Restart backend if needed
docker-compose restart orchestrator
```

#### Frontend won't start
```bash
# Clear npm cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node.js version
node --version  # Should be 18+
```

#### API requests fail
```bash
# Check CORS in browser DevTools
# Verify API URL in environment
echo $VITE_API_BASE_URL

# Test API directly
curl -X POST "http://localhost:8004/process" \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

#### Build fails
```bash
# Check TypeScript errors
npm run build

# Clear build cache
rm -rf dist node_modules
npm install
npm run build
```

### Getting Help
1. **Check browser console** for JavaScript errors
2. **Use React DevTools** for component debugging
3. **Check network tab** for API request issues
4. **View Docker logs**: `docker-compose logs frontend`
5. **Consult tutorials**: [Frontend Tutorials](docs/tutorials/frontend/)

## 📚 Learning Resources

### Tutorials
- **[Complete Tutorial Series](docs/tutorials/frontend/)** - 47 guides from beginner to expert
- **[Phase 1: React Basics](docs/tutorials/frontend/phase-1-basics/)** - React fundamentals
- **[Phase 2: API Integration](docs/tutorials/frontend/phase-2-api-integration/)** - Backend connection
- **[Phase 3: Streaming Features](docs/tutorials/frontend/phase-3-streaming/)** - Real-time features

### Code Examples
- **[Component Breakdowns](docs/tutorials/frontend/examples/)** - Detailed code analysis
- **[Hook Implementations](docs/tutorials/frontend/examples/04-hooks-implementation-guide.md)** - Custom hook patterns
- **[Service Layer Patterns](docs/tutorials/frontend/examples/05-api-service-patterns.md)** - API architecture

## 🎉 Next Steps

After getting the frontend running:

1. **🧪 Experiment** - Try different queries and observe agent routing
2. **📚 Learn** - Work through the comprehensive tutorial series
3. **🛠️ Customize** - Modify components and styling to your needs
4. **🤝 Contribute** - Add new features or improve existing ones
5. **🚀 Deploy** - Set up production deployment

The frontend is production-ready with 1,935+ lines of TypeScript/React code, comprehensive error handling, and advanced UX patterns!

---

**Need help?** Check the [tutorials](docs/tutorials/frontend/), [troubleshooting guide](docs/tutorials/frontend/troubleshooting/), or [open an issue](https://github.com/your-org/agent-net-sandbox/issues).