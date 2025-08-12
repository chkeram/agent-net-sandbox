# Example 4: Custom Hooks Implementation Guide - Deep Dive into Production Patterns

## 🎯 **What You'll Learn**

This tutorial provides a **complete breakdown** of our production custom hooks from the Agent Network Sandbox frontend. You'll understand:
- **Advanced state management patterns** with useState and useRef
- **Async state handling** for streaming and API calls
- **Custom hook composition** and reusability patterns
- **Performance optimization techniques** with useMemo and useCallback
- **Error handling strategies** in custom hooks
- **Real-time data management** with Server-Sent Events

## 🏗️ **Hook Architecture Overview**

Our frontend uses **3 primary custom hooks**:
1. **`useOrchestrator`** (96 LOC) - Basic API integration and message management
2. **`useStreamingOrchestrator`** (265 LOC) - Advanced streaming with SSE and real-time features
3. **`useRoutingTransparency`** - AI routing decision parsing and display

## 🔍 **Complete Hook Breakdowns**

---

## **Hook 1: `useOrchestrator` - Foundation Pattern**

### **Interface & Core State**

```typescript
// src/hooks/useOrchestrator.ts
interface Message {
  id: string
  content: string
  sender: 'user' | 'assistant'
  timestamp: Date
  agentName?: string
}

interface OrchestratorState {
  messages: Message[]
  isLoading: boolean
  error: string | null
  agentInfo: AgentInfo | null
}

export const useOrchestrator = (apiUrl: string = 'http://localhost:8004') => {
  // Core state management
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [agentInfo, setAgentInfo] = useState<AgentInfo | null>(null)
  
  // Refs for stable references
  const abortControllerRef = useRef<AbortController | null>(null)
  const messageIdCounter = useRef(0)
```

**Key Patterns:**
- **Separated concerns**: State for data, loading, errors, and metadata
- **AbortController ref**: For cancelling in-flight requests
- **Counter ref**: For generating stable message IDs
- **Default parameters**: Makes hook flexible across environments

### **Message Management Functions**

```typescript
  const addMessage = useCallback((content: string, sender: 'user' | 'assistant', agentName?: string) => {
    const newMessage: Message = {
      id: `msg-${++messageIdCounter.current}`,
      content,
      sender,
      timestamp: new Date(),
      agentName,
    }
    
    setMessages(prev => [...prev, newMessage])
    return newMessage.id
  }, [])
  
  const updateMessage = useCallback((id: string, updates: Partial<Message>) => {
    setMessages(prev => prev.map(msg => 
      msg.id === id ? { ...msg, ...updates } : msg
    ))
  }, [])
  
  const clearMessages = useCallback(() => {
    setMessages([])
    setError(null)
    setAgentInfo(null)
  }, [])
```

**Key Patterns:**
- **useCallback optimization**: Prevents child components from re-rendering unnecessarily
- **Immutable state updates**: Using spread operators for React optimization
- **ID generation**: Simple counter-based IDs for local state
- **Atomic updates**: Each function does one thing clearly

### **Core API Integration**

```typescript
  const sendMessage = useCallback(async (content: string): Promise<string | null> => {
    // Cancel any existing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    
    // Create new abort controller
    abortControllerRef.current = new AbortController()
    
    // Add user message immediately
    const userMessageId = addMessage(content, 'user')
    
    // Set loading state
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`${apiUrl}/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: content }),
        signal: abortControllerRef.current.signal,
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const data = await response.json()
      
      // Extract agent information
      if (data.selected_agent) {
        setAgentInfo({
          id: data.selected_agent.agent_id,
          name: data.selected_agent.name,
          protocol: data.selected_agent.protocol,
          confidence: data.selected_agent.confidence,
        })
      }
      
      // Add assistant response
      const assistantMessageId = addMessage(
        data.response || 'No response received',
        'assistant',
        data.selected_agent?.name
      )
      
      return assistantMessageId
      
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Request was aborted')
        return null
      }
      
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      setError(errorMessage)
      
      // Add error message to chat
      addMessage(`Error: ${errorMessage}`, 'assistant', 'System')
      return null
    } finally {
      setIsLoading(false)
      abortControllerRef.current = null
    }
  }, [apiUrl, addMessage])
```

**Key Patterns:**
- **Request cancellation**: AbortController for cleanup
- **Optimistic updates**: Add user message immediately
- **Comprehensive error handling**: Network, HTTP, and parsing errors
- **Loading state management**: Clear start and end states
- **Response parsing**: Extract structured data from API response

---

## **Hook 2: `useStreamingOrchestrator` - Advanced Pattern**

This is our most complex hook (265 LOC) handling real-time streaming, chunk processing, and advanced state management.

### **Advanced State Architecture**

```typescript
// src/hooks/useStreamingOrchestrator.ts
interface StreamingState {
  messages: StreamingMessage[]
  isStreaming: boolean
  isLoading: boolean
  error: string | null
  streamingContent: string
  currentPhase: 'idle' | 'routing' | 'processing' | 'streaming' | 'complete'
  agentInfo: AgentInfo | null
  routingReasoning: string
}

export const useStreamingOrchestrator = (apiUrl: string = 'http://localhost:8004') => {
  // Advanced state management
  const [state, setState] = useState<StreamingState>({
    messages: [],
    isStreaming: false,
    isLoading: false,
    error: null,
    streamingContent: '',
    currentPhase: 'idle',
    agentInfo: null,
    routingReasoning: '',
  })
  
  // Refs for streaming management
  const eventSourceRef = useRef<EventSource | null>(null)
  const streamingMessageIdRef = useRef<string | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const messageIdCounter = useRef(0)
  const mountedRef = useRef(true)
```

**Key Patterns:**
- **Single state object**: Reduces setState calls and keeps related data together
- **Phase tracking**: Explicit states for different stages of the process
- **Multiple refs**: Each ref has a specific purpose (EventSource, message ID, abort controller)
- **Mount tracking**: Prevents state updates after component unmount

### **Streaming State Management**

```typescript
  // Optimized state updater
  const updateState = useCallback((updates: Partial<StreamingState>) => {
    if (!mountedRef.current) return
    
    setState(prevState => ({
      ...prevState,
      ...updates
    }))
  }, [])
  
  // Phase transition with logging
  const setPhase = useCallback((phase: StreamingState['currentPhase']) => {
    console.log(`🔄 Phase transition: ${state.currentPhase} → ${phase}`)
    updateState({ currentPhase: phase })
  }, [state.currentPhase, updateState])
  
  // Streaming content accumulator
  const appendStreamingContent = useCallback((chunk: string) => {
    if (!mountedRef.current) return
    
    setState(prevState => ({
      ...prevState,
      streamingContent: prevState.streamingContent + chunk
    }))
  }, [])
```

**Key Patterns:**
- **Mount checking**: Prevents memory leaks and React warnings
- **Phase logging**: Development debugging for complex state flows
- **Atomic updates**: Each function has a single responsibility
- **Performance optimization**: Minimal state updates

### **Server-Sent Events Implementation**

```typescript
  const startStreaming = useCallback(async (query: string) => {
    // Cleanup any existing stream
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    
    // Reset state
    updateState({
      isStreaming: true,
      isLoading: true,
      error: null,
      streamingContent: '',
      currentPhase: 'routing',
      agentInfo: null,
      routingReasoning: '',
    })
    
    // Add user message immediately
    const userMessage: StreamingMessage = {
      id: `msg-${++messageIdCounter.current}`,
      content: query,
      sender: 'user',
      timestamp: new Date(),
      status: 'sent',
    }
    
    updateState({
      messages: [...state.messages, userMessage]
    })
    
    // Create streaming message placeholder
    const streamingMessageId = `msg-${++messageIdCounter.current}`
    streamingMessageIdRef.current = streamingMessageId
    
    const streamingMessage: StreamingMessage = {
      id: streamingMessageId,
      content: '',
      sender: 'assistant',
      timestamp: new Date(),
      status: 'streaming',
      isStreaming: true,
    }
    
    updateState({
      messages: [...state.messages, userMessage, streamingMessage]
    })
    
    try {
      // Establish EventSource connection
      const eventSource = new EventSource(`${apiUrl}/stream?query=${encodeURIComponent(query)}`)
      eventSourceRef.current = eventSource
      
      // Handle routing phase
      eventSource.addEventListener('routing', (event) => {
        try {
          const routingData = JSON.parse(event.data)
          updateState({
            currentPhase: 'processing',
            agentInfo: routingData.selected_agent,
            routingReasoning: routingData.reasoning,
          })
        } catch (error) {
          console.warn('Failed to parse routing data:', error)
        }
      })
      
      // Handle streaming content
      eventSource.addEventListener('chunk', (event) => {
        setPhase('streaming')
        appendStreamingContent(event.data)
      })
      
      // Handle completion
      eventSource.addEventListener('complete', (event) => {
        try {
          const completeData = JSON.parse(event.data)
          
          // Update final message
          updateState({
            messages: state.messages.map(msg =>
              msg.id === streamingMessageId
                ? {
                    ...msg,
                    content: state.streamingContent,
                    status: 'delivered',
                    isStreaming: false,
                    agentName: state.agentInfo?.name,
                    processingTime: completeData.processing_time,
                  }
                : msg
            ),
            isStreaming: false,
            isLoading: false,
            currentPhase: 'complete',
            streamingContent: '',
          })
        } catch (error) {
          console.error('Failed to handle completion:', error)
        } finally {
          eventSource.close()
          eventSourceRef.current = null
          streamingMessageIdRef.current = null
        }
      })
      
      // Handle errors
      eventSource.addEventListener('error', (event) => {
        console.error('EventSource error:', event)
        
        const errorMessage = 'Streaming connection failed'
        updateState({
          error: errorMessage,
          isStreaming: false,
          isLoading: false,
          currentPhase: 'idle',
          messages: state.messages.map(msg =>
            msg.id === streamingMessageId
              ? { ...msg, content: `Error: ${errorMessage}`, status: 'error', isStreaming: false }
              : msg
          ),
        })
        
        eventSource.close()
        eventSourceRef.current = null
      })
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to start streaming'
      updateState({
        error: errorMessage,
        isStreaming: false,
        isLoading: false,
        currentPhase: 'idle',
      })
    }
  }, [apiUrl, state.messages, state.streamingContent, state.agentInfo, updateState, setPhase, appendStreamingContent])
```

**Key Patterns:**
- **EventSource lifecycle**: Proper setup, event handling, and cleanup
- **Multiple event types**: Different handlers for different streaming phases
- **Optimistic UI**: Add placeholder message immediately
- **Error boundaries**: Comprehensive error handling at each step
- **State reconciliation**: Careful management of streaming vs final state

### **Cleanup and Effect Management**

```typescript
  // Cleanup function
  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    streamingMessageIdRef.current = null
  }, [])
  
  // Cleanup on unmount
  useEffect(() => {
    mountedRef.current = true
    
    return () => {
      mountedRef.current = false
      cleanup()
    }
  }, [cleanup])
  
  // Return hook interface
  return {
    ...state,
    sendMessage: startStreaming,
    stopStreaming: cleanup,
    clearMessages: () => updateState({ 
      messages: [], 
      error: null, 
      streamingContent: '', 
      currentPhase: 'idle' 
    }),
    retryLastMessage: () => {
      const lastUserMessage = state.messages
        .filter(msg => msg.sender === 'user')
        .pop()
      
      if (lastUserMessage) {
        startStreaming(lastUserMessage.content)
      }
    },
  }
}
```

**Key Patterns:**
- **Cleanup isolation**: Single function handles all cleanup logic
- **Effect dependencies**: Careful dependency management
- **Hook interface**: Clean, consistent API for consumers
- **Retry functionality**: Built-in retry mechanism

---

## **Hook 3: `useRoutingTransparency` - Data Processing Pattern**

### **Parsing and State Management**

```typescript
// src/hooks/useRoutingTransparency.ts
interface RoutingDecision {
  agentInfo: AgentInfo
  reasoning: string
  processingTime: number
  confidence: number
  alternatives: Array<{
    agent: string
    reason: string
    confidence: number
  }>
}

export const useRoutingTransparency = () => {
  const [routingHistory, setRoutingHistory] = useState<RoutingDecision[]>([])
  
  const parseRoutingDecision = useCallback((orchestratorResponse: any): RoutingDecision | null => {
    try {
      // Handle different response formats
      if (orchestratorResponse.routing_metadata) {
        return parseStructuredRouting(orchestratorResponse.routing_metadata)
      }
      
      if (orchestratorResponse.selected_agent) {
        return parseBasicRouting(orchestratorResponse)
      }
      
      return null
    } catch (error) {
      console.warn('Failed to parse routing decision:', error)
      return null
    }
  }, [])
  
  const addRoutingDecision = useCallback((decision: RoutingDecision) => {
    setRoutingHistory(prev => [decision, ...prev].slice(0, 100)) // Keep last 100
  }, [])
  
  const getRoutingStats = useCallback(() => {
    if (routingHistory.length === 0) return null
    
    const avgConfidence = routingHistory.reduce((sum, d) => sum + d.confidence, 0) / routingHistory.length
    const avgProcessingTime = routingHistory.reduce((sum, d) => sum + d.processingTime, 0) / routingHistory.length
    const agentCounts = routingHistory.reduce((counts, d) => {
      const agent = d.agentInfo.name
      counts[agent] = (counts[agent] || 0) + 1
      return counts
    }, {} as Record<string, number>)
    
    return {
      totalDecisions: routingHistory.length,
      avgConfidence,
      avgProcessingTime,
      mostUsedAgent: Object.entries(agentCounts).sort(([,a], [,b]) => b - a)[0]?.[0],
      agentDistribution: agentCounts,
    }
  }, [routingHistory])
  
  return {
    routingHistory,
    parseRoutingDecision,
    addRoutingDecision,
    getRoutingStats,
    clearHistory: () => setRoutingHistory([]),
  }
}
```

## 🎯 **Hook Composition Patterns**

### **Combining Multiple Hooks**

```typescript
// src/components/StreamingChatContainer.tsx
export const StreamingChatContainer: React.FC = () => {
  // Combine multiple hooks for full functionality
  const streaming = useStreamingOrchestrator()
  const routing = useRoutingTransparency()
  const persistence = useMessagePersistence()
  
  // Handle message completion with routing analysis
  useEffect(() => {
    if (streaming.currentPhase === 'complete' && streaming.agentInfo) {
      const decision = routing.parseRoutingDecision({
        selected_agent: streaming.agentInfo,
        reasoning: streaming.routingReasoning,
        processing_time: 1000, // Would come from actual response
      })
      
      if (decision) {
        routing.addRoutingDecision(decision)
      }
      
      // Persist to storage
      const lastMessage = streaming.messages[streaming.messages.length - 1]
      if (lastMessage) {
        persistence.saveMessage({
          ...lastMessage,
          routingDecision: decision,
        })
      }
    }
  }, [streaming.currentPhase, streaming.agentInfo])
  
  return (
    <div className="streaming-chat">
      {/* Chat interface */}
    </div>
  )
}
```

## 🔧 **Testing Patterns**

### **Hook Testing with React Testing Library**

```typescript
// src/hooks/__tests__/useOrchestrator.test.ts
import { renderHook, act, waitFor } from '@testing-library/react'
import { useOrchestrator } from '../useOrchestrator'

describe('useOrchestrator', () => {
  let mockFetch: jest.Mock
  
  beforeEach(() => {
    mockFetch = jest.fn()
    global.fetch = mockFetch
  })
  
  it('should send message and update state', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        response: 'Test response',
        selected_agent: { name: 'Test Agent', confidence: 0.9 }
      })
    })
    
    const { result } = renderHook(() => useOrchestrator())
    
    await act(async () => {
      await result.current.sendMessage('Hello')
    })
    
    expect(result.current.messages).toHaveLength(2) // User + assistant
    expect(result.current.messages[1].content).toBe('Test response')
    expect(result.current.agentInfo?.name).toBe('Test Agent')
  })
  
  it('should handle errors gracefully', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'))
    
    const { result } = renderHook(() => useOrchestrator())
    
    await act(async () => {
      await result.current.sendMessage('Hello')
    })
    
    expect(result.current.error).toBe('Network error')
    expect(result.current.isLoading).toBe(false)
  })
  
  it('should cancel requests on abort', async () => {
    const { result } = renderHook(() => useOrchestrator())
    
    // Start a request
    const sendPromise = act(async () => {
      return result.current.sendMessage('Hello')
    })
    
    // Cancel immediately
    act(() => {
      result.current.sendMessage('Another message')
    })
    
    await sendPromise
    
    // Verify the first request was cancelled
    expect(mockFetch).toHaveBeenCalledTimes(2)
  })
})
```

## 🎯 **Key Production Patterns**

1. **State Management**: Single source of truth with atomic updates
2. **Error Boundaries**: Comprehensive error handling at every level
3. **Cleanup**: Proper resource management and memory leak prevention
4. **Performance**: Strategic use of useCallback and useMemo
5. **Composability**: Hooks work together to build complex features
6. **Testing**: Full test coverage with realistic scenarios
7. **TypeScript**: Complete type safety with interfaces and generics

These hooks demonstrate **production-grade patterns** for building complex, real-time React applications with excellent performance and reliability.

---

**Next**: [05-api-service-patterns.md](./05-api-service-patterns.md) - Service Layer Architecture  
**Previous**: [03-routing-reasoning-component.md](./03-routing-reasoning-component.md)