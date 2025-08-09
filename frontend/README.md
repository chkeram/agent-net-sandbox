# Agent Network Sandbox - React Frontend

A modern, production-ready chat interface for the Multi-Protocol Agent Orchestrator.

## Tech Stack

- **React 18** with functional components and hooks
- **Vite** for fast build tooling
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **react-markdown** with syntax highlighting for message rendering

## Phase 1 Features ✅

- ✅ Basic chat layout with message list and input field
- ✅ User/assistant message distinction with avatars
- ✅ Markdown rendering with syntax highlighting
- ✅ Code block copy buttons
- ✅ Auto-scrolling to latest message
- ✅ Local storage for conversation history
- ✅ Loading indicator for responses
- ✅ Dark mode support (follows system preference)
- ✅ Responsive design

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- The orchestrator service running on `http://localhost:8004`

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at `http://localhost:5173`

### Build for Production

```bash
# Build the application
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Chat/
│   │   │   ├── ChatContainer.tsx   # Main chat container
│   │   │   ├── MessageList.tsx     # Message list component
│   │   │   ├── Message.tsx         # Individual message
│   │   │   └── ChatInput.tsx       # Chat input field
│   ├── types/
│   │   ├── chat.ts                 # Chat-related types
│   │   └── agent.ts                # Agent-related types
│   ├── App.tsx                     # Main app component
│   ├── main.tsx                    # Application entry point
│   └── index.css                   # Global styles with Tailwind
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## Current Status

### Phase 1 (Completed) ✅
- Core chat UI with TypeScript and Tailwind CSS
- Markdown message rendering with syntax highlighting
- Local storage persistence
- Basic error handling
- Responsive design

### Next Steps (Phase 2)
- Connect to orchestrator API endpoints
- Implement streaming responses
- Add agent discovery and selection
- Display routing decisions

## API Integration (Pending)

The frontend is prepared to connect to these orchestrator endpoints:

- `POST /process` - Send messages and receive responses
- `GET /agents` - Discover available agents
- `GET /health` - Check orchestrator health

## Development Notes

- The chat interface saves conversation history to localStorage
- Dark mode follows system preferences
- Messages support full Markdown with GFM (GitHub Flavored Markdown)
- Code blocks include syntax highlighting and copy buttons

## Testing the UI

1. Start the dev server: `npm run dev`
2. Open `http://localhost:5173` in your browser
3. Type a message and press Enter
4. The UI will attempt to connect to the orchestrator at `http://localhost:8004`
5. Messages are persisted in localStorage

## Known Issues

- API connection to orchestrator not yet implemented (returns error)
- Streaming responses not yet implemented
- Agent selection UI not yet available

---

**Phase 1 Complete** - Ready for verification and commit