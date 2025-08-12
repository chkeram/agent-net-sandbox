# Phase 3.3: Advanced Streaming State Management

## 🎯 **Learning Objectives**

By the end of this tutorial, you will:
- Master complex streaming state coordination across multiple components
- Build robust state machines for streaming phases and error recovery
- Implement optimistic UI updates with conflict resolution
- Handle streaming interruption and reconnection scenarios
- Create performant state updates during high-frequency streaming

## 🔄 **Streaming State Complexity**

Streaming introduces unique state management challenges:

```typescript
// Multiple concurrent state streams
interface StreamingState {
  // Connection state
  isConnected: boolean;
  connectionState: 'idle' | 'connecting' | 'connected' | 'reconnecting' | 'failed';
  
  // Streaming process state
  isStreaming: boolean;
  streamPhase: 'idle' | 'routing' | 'executing' | 'streaming' | 'completed' | 'error';
  
  // Content accumulation
  accumulatedResponse: string;
  chunkCount: number;
  lastChunkTime: Date | null;
  
  // Routing information
  routingInfo: {
    agentId: string;
    agentName: string;
    protocol: string;
    confidence: number;
    reasoning: string;
  } | null;
  
  // Error handling
  error: string | null;
  retryCount: number;
  lastErrorTime: Date | null;
}
```

### **State Machine Design**

Our streaming follows a clear state machine:

```
[idle] → [routing] → [executing] → [streaming] → [completed]
   ↓         ↓           ↓             ↓
[error] ←—————————————————————————————————————————————————
   ↓
[reconnecting] → [routing] (retry)
```

## 🏗️ **Building the Streaming State Hook**

### **Step 1: Core State Structure**

```typescript
// src/hooks/useStreamingOrchestrator.ts
import { useState, useRef, useCallback, useEffect } from 'react';
import { StreamingAPI } from '../services/streamingApi';

interface StreamingState {
  isConnected: boolean;
  connectionState: 'idle' | 'connecting' | 'connected' | 'reconnecting' | 'failed';
  isStreaming: boolean;
  streamPhase: 'idle' | 'routing' | 'executing' | 'streaming' | 'completed' | 'error';
  accumulatedResponse: string;
  chunkCount: number;
  lastChunkTime: Date | null;
  routingInfo: RoutingInfo | null;
  error: string | null;
  retryCount: number;
  lastErrorTime: Date | null;
}

const initialStreamingState: StreamingState = {
  isConnected: false,
  connectionState: 'idle',
  isStreaming: false,
  streamPhase: 'idle',
  accumulatedResponse: '',
  chunkCount: 0,
  lastChunkTime: null,
  routingInfo: null,
  error: null,
  retryCount: 0,
  lastErrorTime: null,
};

export const useStreamingOrchestrator = () => {
  const [state, setState] = useState<StreamingState>(initialStreamingState);
  const streamingApiRef = useRef<StreamingAPI>(new StreamingAPI());
  const abortControllerRef = useRef<AbortController | null>(null);
  
  // Performance optimization: Use refs for high-frequency updates
  const accumulatedRef = useRef('');
  const routingInfoRef = useRef<RoutingInfo | null>(null);
  
  // ... methods will go here
};
```

### **Step 2: State Update Patterns**

```typescript
// Atomic state updates with proper typing
const updateStreamingState = useCallback((updates: Partial<StreamingState>) => {
  setState(prevState => ({
    ...prevState,
    ...updates,
    // Always update timestamp for debugging
    lastUpdated: Date.now(),
  }));
}, []);

// Batch multiple related updates
const updateStreamingPhase = useCallback((
  phase: StreamingState['streamPhase'], 
  additionalUpdates: Partial<StreamingState> = {}
) => {
  updateStreamingState({
    streamPhase: phase,
    isStreaming: phase === 'streaming',
    error: phase === 'error' ? state.error : null, // Clear error on success
    ...additionalUpdates,
  });
}, [updateStreamingState, state.error]);

// Performance-optimized accumulation updates
const updateAccumulatedResponse = useCallback((newChunk: string) => {
  // Update ref immediately (no re-render)
  accumulatedRef.current += newChunk;
  
  // Debounced state update to prevent excessive re-renders
  const updateState = () => {
    setState(prevState => ({
      ...prevState,
      accumulatedResponse: accumulatedRef.current,
      chunkCount: prevState.chunkCount + 1,
      lastChunkTime: new Date(),
    }));
  };
  
  // Use requestAnimationFrame for smooth UI updates
  requestAnimationFrame(updateState);
}, []);
```

### **Step 3: Event Handlers and State Transitions**

```typescript
// Streaming event handlers with proper state transitions
const handleStreamingEvents = useCallback(() => {
  const callbacks = {
    onRequestReceived: () => {
      console.log('🔄 Request received, starting routing...');
      updateStreamingPhase('routing');
      
      // Reset accumulation state
      accumulatedRef.current = '';
      routingInfoRef.current = null;
      updateStreamingState({
        accumulatedResponse: '',
        chunkCount: 0,
        routingInfo: null,
        error: null,
      });
    },
    
    onRoutingStarted: () => {
      console.log('🧠 Routing analysis started...');
      updateStreamingPhase('routing');
    },
    
    onRoutingCompleted: (data: RoutingEvent) => {
      console.log('🎯 Routing completed:', data);
      
      // Cache routing info in ref for performance
      routingInfoRef.current = {
        agentId: data.agent,
        agentName: data.agentName,
        protocol: data.protocol,
        confidence: data.confidence,
        reasoning: data.reasoning,
      };
      
      updateStreamingPhase('executing', {
        routingInfo: routingInfoRef.current,
      });
    },
    
    onAgentExecutionStarted: (agentId: string) => {
      console.log('⚡ Agent execution started:', agentId);
      updateStreamingPhase('executing');
    },
    
    onResponseChunk: (chunk: string) => {
      console.log('📝 Response chunk received:', chunk.slice(0, 50) + '...');
      
      // Ensure we're in streaming phase
      if (state.streamPhase !== 'streaming') {
        updateStreamingPhase('streaming');
      }
      
      // Update accumulated response
      updateAccumulatedResponse(chunk);
    },
    
    onCompleted: (data: CompletedEvent) => {
      console.log('✅ Streaming completed:', data);
      
      updateStreamingPhase('completed', {
        accumulatedResponse: data.content || accumulatedRef.current,
        routingInfo: routingInfoRef.current,
      });
    },
    
    onError: (error: string) => {
      console.error('❌ Streaming error:', error);
      
      updateStreamingPhase('error', {
        error,
        retryCount: state.retryCount + 1,
        lastErrorTime: new Date(),
      });
    },
  };
  
  return callbacks;
}, [updateStreamingPhase, updateAccumulatedResponse, updateStreamingState, state.streamPhase, state.retryCount]);
```

### **Step 4: Main Streaming Function**

```typescript
const processMessageStream = useCallback(async (query: string): Promise<void> => {
  // Prevent multiple concurrent streams
  if (state.isStreaming) {
    throw new Error('Another streaming request is already in progress');
  }
  
  // Abort any existing stream
  if (abortControllerRef.current) {
    abortControllerRef.current.abort();
  }
  
  // Create new abort controller
  abortControllerRef.current = new AbortController();
  
  try {
    // Update connection state
    updateStreamingState({
      connectionState: 'connecting',
      isStreaming: true,
      error: null,
    });
    
    // Process the streaming request
    await streamingApiRef.current.processMessageStream(
      query,
      handleStreamingEvents(),
      abortControllerRef.current.signal
    );
    
    // Update connection state on success
    updateStreamingState({
      connectionState: 'connected',
      isConnected: true,
    });
    
  } catch (error) {
    console.error('Streaming failed:', error);
    
    // Handle different error types
    if (error.name === 'AbortError') {
      console.log('Streaming was aborted');
      updateStreamingState({
        connectionState: 'idle',
        isStreaming: false,
        streamPhase: 'idle',
      });
    } else {
      // Connection or processing error
      updateStreamingState({
        connectionState: 'failed',
        isStreaming: false,
        streamPhase: 'error',
        error: error.message || 'Streaming failed',
        lastErrorTime: new Date(),
        retryCount: state.retryCount + 1,
      });
      
      throw error; // Re-throw for container to handle fallback
    }
  }
}, [state.isStreaming, state.retryCount, updateStreamingState, handleStreamingEvents]);
```

### **Step 5: Connection Management**

```typescript
// Health monitoring and reconnection logic
const [healthState, setHealthState] = useState({
  isHealthy: false,
  lastCheckTime: null,
  checkCount: 0,
});

const checkHealth = useCallback(async (): Promise<boolean> => {
  try {
    updateStreamingState({ connectionState: 'connecting' });
    
    const health = await streamingApiRef.current.checkHealth();
    const isHealthy = health.status === 'healthy';
    
    setHealthState({
      isHealthy,
      lastCheckTime: new Date(),
      checkCount: healthState.checkCount + 1,
    });
    
    updateStreamingState({
      connectionState: isHealthy ? 'connected' : 'failed',
      isConnected: isHealthy,
      error: isHealthy ? null : 'Health check failed',
    });
    
    return isHealthy;
  } catch (error) {
    console.error('Health check failed:', error);
    
    setHealthState({
      isHealthy: false,
      lastCheckTime: new Date(),
      checkCount: healthState.checkCount + 1,
    });
    
    updateStreamingState({
      connectionState: 'failed',
      isConnected: false,
      error: error.message || 'Health check failed',
    });
    
    return false;
  }
}, [healthState.checkCount, updateStreamingState]);

// Auto-reconnection logic
const attemptReconnection = useCallback(async (maxAttempts = 3): Promise<boolean> => {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    console.log(`Reconnection attempt ${attempt}/${maxAttempts}`);
    
    updateStreamingState({
      connectionState: 'reconnecting',
      retryCount: state.retryCount + attempt,
    });
    
    // Exponential backoff
    if (attempt > 1) {
      const delay = Math.min(1000 * Math.pow(2, attempt - 1), 10000);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
    
    const success = await checkHealth();
    if (success) {
      console.log('Reconnection successful');
      return true;
    }
  }
  
  console.log('Reconnection failed after all attempts');
  updateStreamingState({
    connectionState: 'failed',
    error: 'Unable to reconnect to streaming service',
  });
  
  return false;
}, [checkHealth, updateStreamingState, state.retryCount]);

// Abort streaming
const abortStream = useCallback(() => {
  if (abortControllerRef.current) {
    abortControllerRef.current.abort();
    abortControllerRef.current = null;
  }
  
  updateStreamingState({
    isStreaming: false,
    streamPhase: 'idle',
    connectionState: 'idle',
  });
}, [updateStreamingState]);

// Clear error state
const clearError = useCallback(() => {
  updateStreamingState({
    error: null,
    streamPhase: state.streamPhase === 'error' ? 'idle' : state.streamPhase,
  });
}, [updateStreamingState, state.streamPhase]);
```

### **Step 6: Cleanup and Effect Management**

```typescript
// Cleanup on unmount
useEffect(() => {
  return () => {
    // Abort any ongoing streams
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    // Cleanup streaming API
    if (streamingApiRef.current) {
      streamingApiRef.current.destroy?.();
    }
  };
}, []);

// Auto health check on mount
useEffect(() => {
  checkHealth();
}, [checkHealth]);

// Auto-retry on connection failure (with exponential backoff)
useEffect(() => {
  if (state.connectionState === 'failed' && state.retryCount < 3) {
    const timeoutId = setTimeout(() => {
      attemptReconnection(1);
    }, Math.min(1000 * Math.pow(2, state.retryCount), 10000));
    
    return () => clearTimeout(timeoutId);
  }
}, [state.connectionState, state.retryCount, attemptReconnection]);

// Return hook API
return {
  // State
  isConnected: state.isConnected,
  connectionState: state.connectionState,
  isStreaming: state.isStreaming,
  streamPhase: state.streamPhase,
  accumulatedResponse: state.accumulatedResponse,
  chunkCount: state.chunkCount,
  routingInfo: state.routingInfo,
  error: state.error,
  retryCount: state.retryCount,
  
  // Health state
  isHealthy: healthState.isHealthy,
  lastHealthCheck: healthState.lastCheckTime,
  
  // Actions
  processMessageStream,
  abortStream,
  checkHealth,
  attemptReconnection,
  clearError,
  
  // Debug info
  _debugState: process.env.NODE_ENV === 'development' ? state : undefined,
};
```

## 🎭 **Advanced State Patterns**

### **State Persistence and Recovery**

```typescript
// Persist streaming state to sessionStorage for recovery
const persistStreamingState = useCallback((state: StreamingState) => {
  try {
    const persistableState = {
      accumulatedResponse: state.accumulatedResponse,
      routingInfo: state.routingInfo,
      error: state.error,
      retryCount: state.retryCount,
      timestamp: Date.now(),
    };
    
    sessionStorage.setItem('streaming-state', JSON.stringify(persistableState));
  } catch (error) {
    console.warn('Failed to persist streaming state:', error);
  }
}, []);

// Recover state on page reload/navigation back
const recoverStreamingState = useCallback((): Partial<StreamingState> | null => {
  try {
    const saved = sessionStorage.getItem('streaming-state');
    if (!saved) return null;
    
    const parsed = JSON.parse(saved);
    
    // Only recover recent state (within 5 minutes)
    const isRecent = Date.now() - parsed.timestamp < 5 * 60 * 1000;
    if (!isRecent) {
      sessionStorage.removeItem('streaming-state');
      return null;
    }
    
    return {
      accumulatedResponse: parsed.accumulatedResponse,
      routingInfo: parsed.routingInfo,
      error: parsed.error,
      retryCount: parsed.retryCount,
    };
  } catch (error) {
    console.warn('Failed to recover streaming state:', error);
    return null;
  }
}, []);

// Use recovery on initialization
useEffect(() => {
  const recovered = recoverStreamingState();
  if (recovered) {
    console.log('Recovered streaming state from session');
    updateStreamingState(recovered);
  }
}, []);

// Persist on state changes
useEffect(() => {
  if (state.accumulatedResponse || state.routingInfo) {
    persistStreamingState(state);
  }
}, [state, persistStreamingState]);
```

### **Optimistic Updates and Conflict Resolution**

```typescript
// Optimistic update pattern for better UX
const optimisticUpdate = useCallback((
  update: Partial<StreamingState>,
  revert?: () => void
) => {
  // Apply optimistic update immediately
  updateStreamingState(update);
  
  // Store revert function for potential rollback
  if (revert) {
    const timeoutId = setTimeout(revert, 10000); // Auto-revert after 10s
    return () => clearTimeout(timeoutId);
  }
}, [updateStreamingState]);

// Example: Optimistic streaming start
const startStreamingOptimistically = useCallback((query: string) => {
  // Optimistic UI update
  const cancelOptimistic = optimisticUpdate({
    isStreaming: true,
    streamPhase: 'routing',
    error: null,
  }, () => {
    // Revert function
    updateStreamingState({
      isStreaming: false,
      streamPhase: 'error',
      error: 'Streaming failed to start',
    });
  });
  
  // Start actual streaming
  processMessageStream(query)
    .then(() => {
      // Success - cancel revert
      cancelOptimistic?.();
    })
    .catch(() => {
      // Error - revert will happen automatically
    });
}, [optimisticUpdate, processMessageStream, updateStreamingState]);
```

### **State Machine Validation**

```typescript
// Validate state transitions
const isValidTransition = (
  from: StreamingState['streamPhase'], 
  to: StreamingState['streamPhase']
): boolean => {
  const validTransitions = {
    idle: ['routing', 'error'],
    routing: ['executing', 'error'],
    executing: ['streaming', 'error'],
    streaming: ['completed', 'error'],
    completed: ['idle', 'routing'],
    error: ['idle', 'routing', 'reconnecting'],
    reconnecting: ['routing', 'error'],
  };
  
  return validTransitions[from]?.includes(to) ?? false;
};

// Enhanced state update with validation
const updateStreamingPhaseValidated = useCallback((
  newPhase: StreamingState['streamPhase'],
  additionalUpdates: Partial<StreamingState> = {}
) => {
  if (!isValidTransition(state.streamPhase, newPhase)) {
    console.warn(`Invalid state transition: ${state.streamPhase} -> ${newPhase}`);
    return;
  }
  
  updateStreamingPhase(newPhase, additionalUpdates);
}, [state.streamPhase, updateStreamingPhase]);
```

## 🧪 **Testing Streaming State Management**

### **Unit Testing with State Mocking**

```typescript
// __tests__/useStreamingOrchestrator.test.ts
import { renderHook, act } from '@testing-library/react';
import { useStreamingOrchestrator } from '../useStreamingOrchestrator';

// Mock streaming API
const mockStreamingApi = {
  processMessageStream: jest.fn(),
  checkHealth: jest.fn(),
  destroy: jest.fn(),
};

jest.mock('../services/streamingApi', () => ({
  StreamingAPI: jest.fn(() => mockStreamingApi),
}));

describe('useStreamingOrchestrator', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  it('should initialize with idle state', () => {
    const { result } = renderHook(() => useStreamingOrchestrator());
    
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.streamPhase).toBe('idle');
    expect(result.current.error).toBeNull();
  });
  
  it('should transition through streaming phases', async () => {
    const { result } = renderHook(() => useStreamingOrchestrator());
    
    // Mock successful streaming
    mockStreamingApi.processMessageStream.mockImplementation(async (query, callbacks) => {
      callbacks.onRequestReceived();
      await new Promise(resolve => setTimeout(resolve, 10));
      callbacks.onRoutingCompleted({ agent: 'test-agent' });
      callbacks.onResponseChunk('Hello');
      callbacks.onCompleted({ content: 'Hello world' });
    });
    
    await act(async () => {
      await result.current.processMessageStream('test query');
    });
    
    expect(result.current.streamPhase).toBe('completed');
    expect(result.current.accumulatedResponse).toBe('Hello world');
  });
  
  it('should handle streaming errors gracefully', async () => {
    const { result } = renderHook(() => useStreamingOrchestrator());
    
    mockStreamingApi.processMessageStream.mockRejectedValue(
      new Error('Connection failed')
    );
    
    await act(async () => {
      try {
        await result.current.processMessageStream('test query');
      } catch (error) {
        // Expected to throw
      }
    });
    
    expect(result.current.streamPhase).toBe('error');
    expect(result.current.error).toContain('Connection failed');
  });
  
  it('should support stream abortion', () => {
    const { result } = renderHook(() => useStreamingOrchestrator());
    
    act(() => {
      result.current.abortStream();
    });
    
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.streamPhase).toBe('idle');
  });
});
```

### **Integration Testing with Real Streaming**

```typescript
// __tests__/streaming.integration.test.ts
describe('Streaming Integration', () => {
  it('should handle real streaming lifecycle', async () => {
    const TestComponent = () => {
      const streaming = useStreamingOrchestrator();
      const [messages, setMessages] = useState([]);
      
      useEffect(() => {
        if (streaming.streamPhase === 'completed') {
          setMessages(prev => [...prev, {
            content: streaming.accumulatedResponse,
            routingInfo: streaming.routingInfo,
          }]);
        }
      }, [streaming.streamPhase, streaming.accumulatedResponse]);
      
      return (
        <div>
          <div data-testid="stream-phase">{streaming.streamPhase}</div>
          <div data-testid="messages">{messages.length}</div>
          <button onClick={() => streaming.processMessageStream('test')}>
            Send
          </button>
        </div>
      );
    };
    
    render(<TestComponent />);
    
    // Start streaming
    fireEvent.click(screen.getByText('Send'));
    
    // Wait for completion
    await waitFor(() => {
      expect(screen.getByTestId('stream-phase')).toHaveTextContent('completed');
    });
    
    expect(screen.getByTestId('messages')).toHaveTextContent('1');
  });
});
```

## 🎯 **Performance Optimization Strategies**

### **Debouncing High-Frequency Updates**

```typescript
import { useDeferredValue, startTransition } from 'react';

const useOptimizedStreamingState = () => {
  const [state, setState] = useState(initialState);
  
  // Defer non-critical updates
  const deferredAccumulatedResponse = useDeferredValue(state.accumulatedResponse);
  const deferredChunkCount = useDeferredValue(state.chunkCount);
  
  const updateAccumulatedResponse = useCallback((chunk: string) => {
    // Critical update (immediate)
    accumulatedRef.current += chunk;
    
    // Non-critical UI update (deferred)
    startTransition(() => {
      setState(prev => ({
        ...prev,
        accumulatedResponse: accumulatedRef.current,
        chunkCount: prev.chunkCount + 1,
      }));
    });
  }, []);
  
  return {
    ...state,
    accumulatedResponse: deferredAccumulatedResponse,
    chunkCount: deferredChunkCount,
    updateAccumulatedResponse,
  };
};
```

### **Memory Management**

```typescript
// Prevent memory leaks in long streaming sessions
const useMemoryEfficientStreaming = () => {
  const maxChunkHistory = 1000; // Keep last 1000 chunks
  const chunkHistoryRef = useRef<string[]>([]);
  
  const addChunk = useCallback((chunk: string) => {
    chunkHistoryRef.current.push(chunk);
    
    // Clean old chunks to prevent memory leaks
    if (chunkHistoryRef.current.length > maxChunkHistory) {
      chunkHistoryRef.current = chunkHistoryRef.current.slice(-maxChunkHistory);
    }
    
    // Update accumulated response from recent chunks
    const recentChunks = chunkHistoryRef.current.slice(-100); // Last 100 for display
    updateState(prev => ({
      ...prev,
      accumulatedResponse: recentChunks.join(''),
      chunkCount: chunkHistoryRef.current.length,
    }));
  }, []);
  
  return { addChunk };
};
```

## 🎯 **Key Takeaways**

1. **State machines provide clarity** - Clear phase transitions prevent invalid states
2. **Performance matters in streaming** - Use refs and deferred updates for high-frequency changes
3. **Error recovery is critical** - Implement reconnection and fallback strategies
4. **Persistence improves UX** - Save state across page reloads when appropriate
5. **Validation prevents bugs** - Validate state transitions in development
6. **Memory management is essential** - Clean up resources and limit accumulation
7. **Testing streaming is complex** - Mock time-dependent behavior and async flows

---

**Next**: [Protocol-Aware Parsing](../protocol-aware-parsing/01-a2a-response-handling.md) - Understanding Different Agent Response Formats

**Previous**: [02-streaming-api-service.md](./02-streaming-api-service.md)