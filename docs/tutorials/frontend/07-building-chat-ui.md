# Building the Chat UI: Step-by-Step Implementation

## Overview

Let's build our chat interface from scratch, understanding every decision along the way. We'll create a production-ready chat UI that connects to our agent orchestrator.

## Step 1: Project Setup

### Initialize the Project
```bash
# Create frontend directory
mkdir frontend
cd frontend

# Initialize with Vite
npm create vite@latest . -- --template react-ts

# Install dependencies
npm install

# Add our specific packages
npm install react-markdown remark-gfm react-syntax-highlighter
npm install clsx tailwind-merge lucide-react uuid
npm install -D @types/react-syntax-highlighter @types/uuid
npm install -D tailwindcss @tailwindcss/postcss autoprefixer
```

### Configure Tailwind
Create `tailwind.config.js`:
```javascript
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

Create `postcss.config.js`:
```javascript
export default {
  plugins: {
    '@tailwindcss/postcss': {},
  },
}
```

Update `src/index.css`:
```css
@import "tailwindcss";

:root {
  font-family: Inter, system-ui, Arial, sans-serif;
  line-height: 1.5;
  
  color-scheme: light dark;
  color: rgba(255, 255, 255, 0.87);
  background-color: #242424;
}

@media (prefers-color-scheme: light) {
  :root {
    color: #213547;
    background-color: #ffffff;
  }
}

body {
  margin: 0;
  min-height: 100vh;
}

#root {
  width: 100%;
  height: 100vh;
}
```

## Step 2: Define TypeScript Types

Create `src/types/chat.ts`:
```typescript
export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  agentId?: string;
  agentName?: string;
  protocol?: string;
  confidence?: number;
  isStreaming?: boolean;
  error?: string;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
}
```

Create `src/types/agent.ts`:
```typescript
export interface Agent {
  agent_id: string;
  name: string;
  protocol: 'acp' | 'a2a' | 'mcp' | 'custom';
  status: 'healthy' | 'degraded' | 'unhealthy';
  capabilities: string[];
  endpoint: string;
  last_seen: Date;
  description?: string;
}

export interface RoutingDecision {
  selected_agent: Agent | null;
  confidence: number;
  reasoning: string;
  fallback_agents?: Agent[];
}
```

## Step 3: Build the Message Component

Create `src/components/Chat/Message.tsx`:

```typescript
import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { User, Bot, AlertCircle } from 'lucide-react';
import type { Message as MessageType } from '../../types/chat.ts';
import { clsx } from 'clsx';

interface MessageProps {
  message: MessageType;
}

export const Message: React.FC<MessageProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const isError = !!message.error;

  return (
    <div className={clsx(
      'flex gap-3 p-4',
      isUser ? 'bg-white dark:bg-gray-800' : 'bg-gray-50 dark:bg-gray-900'
    )}>
      {/* Avatar */}
      <div className="flex-shrink-0">
        <div className={clsx(
          'w-8 h-8 rounded-full flex items-center justify-center',
          isUser ? 'bg-blue-500' : isError ? 'bg-red-500' : 'bg-green-500'
        )}>
          {isUser ? (
            <User className="w-5 h-5 text-white" />
          ) : isError ? (
            <AlertCircle className="w-5 h-5 text-white" />
          ) : (
            <Bot className="w-5 h-5 text-white" />
          )}
        </div>
      </div>
      
      {/* Content */}
      <div className="flex-1 min-w-0">
        {/* Header */}
        <div className="flex items-center gap-2 mb-1">
          <span className="font-semibold text-sm">
            {isUser ? 'You' : message.agentName || 'Assistant'}
          </span>
          
          {/* Protocol Badge */}
          {message.protocol && (
            <span className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded">
              {message.protocol.toUpperCase()}
            </span>
          )}
          
          {/* Confidence Score */}
          {message.confidence !== undefined && (
            <span className="text-xs text-gray-500">
              {Math.round(message.confidence * 100)}% confidence
            </span>
          )}
        </div>
        
        {/* Message Content */}
        {isError ? (
          <div className="text-red-600 dark:text-red-400">
            {message.error}
          </div>
        ) : (
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                // Custom code block rendering
                code({ inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <div className="relative group">
                      <SyntaxHighlighter
                        style={tomorrow}
                        language={match[1]}
                        PreTag="div"
                        {...props}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                      
                      {/* Copy button */}
                      <button
                        className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity px-2 py-1 text-xs bg-gray-700 text-white rounded"
                        onClick={() => navigator.clipboard.writeText(String(children))}
                      >
                        Copy
                      </button>
                    </div>
                  ) : (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        )}
        
        {/* Timestamp */}
        <div className="text-xs text-gray-400 mt-1">
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};
```

**Key Features:**
- User/Assistant distinction with avatars
- Markdown rendering with syntax highlighting
- Protocol badges for agent identification
- Confidence score display
- Error state handling
- Copy button for code blocks
- Dark mode support

## Step 4: Create the Message List

Create `src/components/Chat/MessageList.tsx`:

```typescript
import React, { useEffect, useRef } from 'react';
import { Message } from './Message.tsx';
import type { Message as MessageType } from '../../types/chat.ts';

interface MessageListProps {
  messages: MessageType[];
  isLoading?: boolean;
}

export const MessageList: React.FC<MessageListProps> = ({ 
  messages, 
  isLoading 
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto">
      {messages.length === 0 ? (
        // Welcome message
        <div className="flex items-center justify-center h-full text-gray-500">
          <div className="text-center">
            <p className="text-lg mb-2">Welcome to Agent Network Sandbox</p>
            <p className="text-sm">Start a conversation with the multi-protocol orchestrator</p>
          </div>
        </div>
      ) : (
        // Message list
        <div className="max-w-4xl mx-auto">
          {messages.map((message) => (
            <Message key={message.id} message={message} />
          ))}
          
          {/* Loading indicator */}
          {isLoading && (
            <div className="flex gap-3 p-4 bg-gray-50 dark:bg-gray-900">
              <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center">
                <div className="animate-pulse w-5 h-5 bg-white rounded-full" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" 
                       style={{ animationDelay: '0ms' }} />
                  <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" 
                       style={{ animationDelay: '150ms' }} />
                  <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" 
                       style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Scroll anchor */}
      <div ref={bottomRef} />
    </div>
  );
};
```

**Features:**
- Auto-scrolling to latest message
- Welcome message for empty state
- Loading animation with bouncing dots
- Centered content with max-width

## Step 5: Build the Chat Input

Create `src/components/Chat/ChatInput.tsx`:

```typescript
import React, { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { Send, StopCircle } from 'lucide-react';
import { clsx } from 'clsx';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
  onStopGeneration?: () => void;
  placeholder?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  isLoading = false,
  onStopGeneration,
  placeholder = "Type your message..."
}) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  const handleSubmit = () => {
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t dark:border-gray-700 p-4 bg-white dark:bg-gray-800">
      <div className="max-w-4xl mx-auto">
        <div className="flex gap-2 items-end">
          {/* Input field */}
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={isLoading}
            rows={1}
            className={clsx(
              "flex-1 resize-none rounded-lg border bg-white dark:bg-gray-900",
              "px-4 py-2 text-sm focus:outline-none focus:ring-2",
              "dark:border-gray-700 dark:text-white",
              isLoading ? "opacity-50 cursor-not-allowed" : "focus:ring-blue-500"
            )}
            style={{ maxHeight: '200px' }}
          />
          
          {/* Action button */}
          {isLoading && onStopGeneration ? (
            <button
              onClick={onStopGeneration}
              className="p-2 rounded-lg bg-red-500 text-white hover:bg-red-600 transition-colors"
              aria-label="Stop generation"
            >
              <StopCircle className="w-5 h-5" />
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!input.trim() || isLoading}
              className={clsx(
                "p-2 rounded-lg transition-colors",
                input.trim() && !isLoading
                  ? "bg-blue-500 text-white hover:bg-blue-600"
                  : "bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-not-allowed"
              )}
              aria-label="Send message"
            >
              <Send className="w-5 h-5" />
            </button>
          )}
        </div>
        
        {/* Help text */}
        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          Press Enter to send, Shift+Enter for new line
        </div>
      </div>
    </div>
  );
};
```

**Features:**
- Auto-resizing textarea
- Keyboard shortcuts (Enter to send)
- Loading state with disabled input
- Stop generation button
- Visual feedback for sendable state

## Step 6: Create the Main Container

Create `src/components/Chat/ChatContainer.tsx`:

```typescript
import React, { useState, useCallback, useEffect } from 'react';
import { MessageList } from './MessageList.tsx';
import { ChatInput } from './ChatInput.tsx';
import type { Message } from '../../types/chat.ts';
import { v4 as uuidv4 } from 'uuid';

export const ChatContainer: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Load messages from localStorage on mount
  useEffect(() => {
    const savedMessages = localStorage.getItem('chat-messages');
    if (savedMessages) {
      try {
        const parsed = JSON.parse(savedMessages);
        setMessages(parsed.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        })));
      } catch (error) {
        console.error('Failed to load messages from localStorage:', error);
      }
    }
  }, []);

  // Save messages to localStorage whenever they change
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem('chat-messages', JSON.stringify(messages));
    }
  }, [messages]);

  const handleSendMessage = useCallback(async (content: string) => {
    // Create user message
    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // API call to orchestrator
      const response = await fetch('http://localhost:8004/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: content,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Create assistant message
      const assistantMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: data.content || 'No response received',
        timestamp: new Date(),
        agentId: data.agent_id,
        agentName: data.agent_name,
        protocol: data.protocol,
        confidence: data.confidence,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
      
      // Add error message
      const errorMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        error: error instanceof Error ? error.message : 'Failed to send message',
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleStopGeneration = useCallback(() => {
    // TODO: Implement abort controller for streaming
    setIsLoading(false);
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    localStorage.removeItem('chat-messages');
  }, []);

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-800">
      {/* Header */}
      <div className="border-b dark:border-gray-700 p-4">
        <div className="max-w-4xl mx-auto flex justify-between items-center">
          <h1 className="text-xl font-semibold dark:text-white">
            Agent Network Sandbox
          </h1>
          <button
            onClick={clearMessages}
            className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            Clear chat
          </button>
        </div>
      </div>
      
      {/* Messages */}
      <MessageList messages={messages} isLoading={isLoading} />
      
      {/* Input */}
      <ChatInput
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
        onStopGeneration={handleStopGeneration}
      />
    </div>
  );
};
```

**Key Features:**
- Complete state management
- Local storage persistence
- API integration setup
- Error handling
- Clear chat functionality

## Step 7: Wire Up the App

Update `src/App.tsx`:

```typescript
import React from 'react';
import { ChatContainer } from './components/Chat/ChatContainer.tsx';

function App() {
  return (
    <div className="h-screen bg-gray-100 dark:bg-gray-900">
      <ChatContainer />
    </div>
  );
}

export default App;
```

Update `src/main.tsx`:

```typescript
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

## Step 8: File Structure

Your final structure should look like:

```
frontend/
├── src/
│   ├── components/
│   │   └── Chat/
│   │       ├── ChatContainer.tsx
│   │       ├── ChatInput.tsx
│   │       ├── Message.tsx
│   │       └── MessageList.tsx
│   ├── types/
│   │   ├── agent.ts
│   │   └── chat.ts
│   ├── App.tsx
│   ├── index.css
│   └── main.tsx
├── package.json
├── postcss.config.js
├── tailwind.config.js
├── tsconfig.json
└── vite.config.ts
```

## Step 9: Running the Application

```bash
# Install dependencies if not done
npm install

# Start development server
npm run dev

# Visit http://localhost:5173
```

## Step 10: Testing the Chat

1. **Basic Message**: Type "Hello" and press Enter
2. **Markdown**: Try "Here's some **bold** and *italic* text"
3. **Code Block**: Send a message with:
   ````
   ```javascript
   function hello() {
     console.log("Hello World");
   }
   ```
   ````
4. **Clear Chat**: Click "Clear chat" to reset
5. **Refresh**: Messages should persist after refresh

## Key Design Decisions

### 1. Component Architecture
- **Separation of Concerns**: Each component has a single responsibility
- **Props Down, Events Up**: Data flows down, callbacks bubble up
- **Container/Presentation**: ChatContainer manages state, others display

### 2. State Management
- **Local State**: Simple useState for our needs
- **Local Storage**: Persistence without backend
- **Loading States**: User feedback during operations

### 3. Styling Approach
- **Utility-First**: Tailwind for rapid development
- **Dark Mode**: System preference detection
- **Responsive**: Mobile-first design

### 4. TypeScript Integration
- **Type Safety**: Interfaces for all data structures
- **Type-Only Imports**: Better tree-shaking
- **Strict Mode**: Catch errors early

### 5. User Experience
- **Auto-scroll**: Always see latest message
- **Keyboard Shortcuts**: Power user friendly
- **Visual Feedback**: Loading indicators, disabled states
- **Error Handling**: Graceful failure with user feedback

## Extending the Chat

### Add Streaming Support
```typescript
// Use Server-Sent Events
const eventSource = new EventSource('/api/stream');
eventSource.onmessage = (event) => {
  const chunk = JSON.parse(event.data);
  // Append to current message
};
```

### Add File Upload
```typescript
<input
  type="file"
  onChange={(e) => {
    const file = e.target.files?.[0];
    // Handle file upload
  }}
/>
```

### Add Voice Input
```typescript
const recognition = new webkitSpeechRecognition();
recognition.onresult = (event) => {
  const transcript = event.results[0][0].transcript;
  handleSendMessage(transcript);
};
```

### Add Message Actions
```typescript
// In Message component
<button onClick={() => regenerateMessage(message.id)}>
  Regenerate
</button>
<button onClick={() => editMessage(message.id)}>
  Edit
</button>
```

## Production Considerations

1. **Error Boundaries**: Catch and handle React errors
2. **Accessibility**: ARIA labels, keyboard navigation
3. **Performance**: Virtualization for long conversations
4. **Security**: Sanitize markdown content
5. **Testing**: Unit and integration tests
6. **Analytics**: Track user interactions
7. **Monitoring**: Error tracking (Sentry)

## Summary

We've built a complete chat interface with:
- ✅ TypeScript for type safety
- ✅ React for component architecture
- ✅ Tailwind for styling
- ✅ Markdown rendering with syntax highlighting
- ✅ Local storage persistence
- ✅ Dark mode support
- ✅ Responsive design
- ✅ Loading states and error handling

The chat is ready for Phase 2: connecting to the orchestrator API!

---

**Previous**: [06-state-management.md](./06-state-management.md) | **Next**: [08-troubleshooting.md](./08-troubleshooting.md)