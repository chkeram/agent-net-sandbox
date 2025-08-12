# Phase 3.2: Building the Complete Streaming API Service

## 🎯 **Learning Objectives**

By the end of this tutorial, you will:
- Build a production-ready EventSource wrapper for SSE streaming
- Implement callback-based architecture for real-time events
- Handle streaming lifecycle management and error recovery
- Parse streaming events with protocol-aware content extraction
- Create a robust service that integrates seamlessly with React hooks

## 🌊 **Streaming Service Architecture**

Our streaming service acts as a bridge between the raw EventSource API and our React application:

```
React Hook  ←→  StreamingAPI Service  ←→  EventSource  ←→  Backend SSE
(State Mgmt)    (Event Processing)        (Browser API)    (Live Events)
```

### **Key Responsibilities**
1. **Event Management**: Handle all SSE event types from orchestrator
2. **Lifecycle Management**: Connection, disconnection, cleanup
3. **Error Recovery**: Automatic reconnection and fallback strategies
4. **Content Parsing**: Extract clean content from protocol-specific chunks
5. **Callback Coordination**: Notify React components of state changes

## 🛠️ **Core Streaming Service Implementation**

### **Step 1: Event Type Definitions**

```typescript
// src/services/streamingApi.ts

// Events our orchestrator sends
export interface BaseStreamEvent {
  event: string;
}

export interface RequestReceivedEvent extends BaseStreamEvent {
  event: 'request_received';
  request_id: string;
}

export interface RoutingStartedEvent extends BaseStreamEvent {
  event: 'routing_started';
}

export interface RoutingEvent extends BaseStreamEvent {
  event: 'routing_completed';
  agent_id: string;
  agent_name: string;
  protocol: string;
  confidence: number;
  reasoning: string;
}

export interface AgentExecutionStartedEvent extends BaseStreamEvent {
  event: 'agent_execution_started';
  agent_id: string;
}

export interface ResponseChunkEvent extends BaseStreamEvent {
  event: 'response_chunk';
  response_data: any;        // Raw chunk data
  protocol: string;          // Protocol for parsing
}

export interface CompletedEvent extends BaseStreamEvent {
  event: 'completed';
  agent_id: string;
  agent_name: string;
  protocol: string;
  confidence: number;
  response_data: any;        // Final complete response
  timestamp: string;
}

export interface ErrorEvent extends BaseStreamEvent {
  event: 'error';
  error_message: string;
  error_type?: string;
}

// Union type for all possible events
export type StreamEvent = 
  | RequestReceivedEvent 
  | RoutingStartedEvent 
  | RoutingEvent 
  | AgentExecutionStartedEvent 
  | ResponseChunkEvent 
  | CompletedEvent 
  | ErrorEvent;
```

### **Step 2: Callback Interface**

```typescript
// Callbacks that React components can provide
export interface StreamingCallbacks {
  onRequestReceived?: (data: RequestReceivedEvent) => void;
  onRoutingStarted?: () => void;
  onRoutingCompleted?: (data: RoutingEvent) => void;
  onAgentExecutionStarted?: (agentId: string) => void;
  onResponseChunk?: (chunk: string) => void;  // Parsed content, not raw data
  onCompleted?: (data: CompletedEvent) => void;
  onError?: (errorMessage: string) => void;
}

// Optional context data to send with request
export interface StreamingContext {
  user_id?: string;
  session_id?: string;
  conversation_id?: string;
  metadata?: Record<string, any>;
}
```

### **Step 3: Core StreamingAPI Class**

```typescript
import { orchestratorApi } from './orchestratorApi';

class StreamingAPI {
  private baseUrl: string;
  private currentEventSource: EventSource | null = null;
  private currentCallbacks: StreamingCallbacks | null = null;
  
  constructor(baseUrl = 'http://localhost:8004') {
    this.baseUrl = baseUrl;
  }
  
  /**
   * Start streaming a message processing request
   */
  async processMessageStream(
    query: string,
    callbacks: StreamingCallbacks,
    context?: StreamingContext
  ): Promise<void> {
    // Clean up any existing connection
    this.abort();
    
    // Store callbacks for use in event handlers
    this.currentCallbacks = callbacks;
    
    try {
      // Create request payload
      const requestBody = {
        query,
        ...(context && { context }),
      };
      
      // Create EventSource for streaming endpoint
      const eventSource = new EventSource(
        `${this.baseUrl}/process/stream?${new URLSearchParams({
          data: JSON.stringify(requestBody)
        })}`
      );
      
      this.currentEventSource = eventSource;
      
      // Set up event listeners
      this.setupEventListeners(eventSource);
      
      // Handle connection establishment
      eventSource.onopen = () => {
        console.log('SSE connection established');
      };
      
      // Handle connection errors
      eventSource.onerror = (error) => {
        console.error('SSE connection error:', error);
        this.handleConnectionError(error);
      };
      
    } catch (error) {
      this.cleanup();
      throw error;
    }
  }
  
  /**
   * Abort current streaming request
   */
  abort(): void {
    if (this.currentEventSource) {
      console.log('Aborting SSE connection');
      this.currentEventSource.close();
      this.cleanup();
    }
  }
  
  private cleanup(): void {
    this.currentEventSource = null;
    this.currentCallbacks = null;
  }
}
```

### **Step 4: Event Handler Setup**

```typescript
class StreamingAPI {
  // ... previous methods ...
  
  private setupEventListeners(eventSource: EventSource): void {
    // Generic message handler for all events
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as StreamEvent;
        this.handleStreamEvent(data);
      } catch (error) {
        console.error('Failed to parse streaming event:', error, event.data);
        this.currentCallbacks?.onError?.('Failed to parse streaming data');
      }
    };
    
    // Handle specific event types if server sends them with event names
    eventSource.addEventListener('routing_completed', (event) => {
      try {
        const data = JSON.parse(event.data) as RoutingEvent;
        this.currentCallbacks?.onRoutingCompleted?.(data);
      } catch (error) {
        console.error('Failed to parse routing_completed event:', error);
      }
    });
    
    eventSource.addEventListener('response_chunk', (event) => {
      try {
        const data = JSON.parse(event.data) as ResponseChunkEvent;
        this.handleResponseChunk(data);
      } catch (error) {
        console.error('Failed to parse response_chunk event:', error);
      }
    });
  }
  
  private handleStreamEvent(event: StreamEvent): void {
    console.log('Received stream event:', event.event, event);
    
    switch (event.event) {
      case 'request_received':
        this.currentCallbacks?.onRequestReceived?.(event as RequestReceivedEvent);
        break;
        
      case 'routing_started':
        this.currentCallbacks?.onRoutingStarted?.();
        break;
        
      case 'routing_completed':
        this.currentCallbacks?.onRoutingCompleted?.(event as RoutingEvent);
        break;
        
      case 'agent_execution_started':
        const execEvent = event as AgentExecutionStartedEvent;
        this.currentCallbacks?.onAgentExecutionStarted?.(execEvent.agent_id);
        break;
        
      case 'response_chunk':
        this.handleResponseChunk(event as ResponseChunkEvent);
        break;
        
      case 'completed':
        this.handleCompleted(event as CompletedEvent);
        break;
        
      case 'error':
        const errorEvent = event as ErrorEvent;
        this.currentCallbacks?.onError?.(errorEvent.error_message);
        this.cleanup();
        break;
        
      default:
        console.warn('Unknown stream event type:', event.event);
    }
  }
}
```

### **Step 5: Content Parsing for Streaming Chunks**

This is the crucial part - extracting clean content from streaming chunks:

```typescript
class StreamingAPI {
  // ... previous methods ...
  
  private handleResponseChunk(chunkEvent: ResponseChunkEvent): void {
    if (!chunkEvent.response_data || !chunkEvent.protocol) {
      console.warn('Response chunk missing data or protocol');
      return;
    }
    
    try {
      // Use orchestratorApi's parsing logic for consistency
      const extractedContent = orchestratorApi.extractResponseContent({
        response_data: chunkEvent.response_data,
        protocol: chunkEvent.protocol,
      });
      
      // Only send non-empty content
      if (extractedContent.trim()) {
        this.currentCallbacks?.onResponseChunk?.(extractedContent);
      }
      
    } catch (error) {
      console.warn('Failed to extract content from response chunk:', error);
      // Still try to send something to UI
      this.currentCallbacks?.onResponseChunk?.(
        JSON.stringify(chunkEvent.response_data)
      );
    }
  }
  
  private handleCompleted(completedEvent: CompletedEvent): void {
    // Notify callback
    this.currentCallbacks?.onCompleted?.(completedEvent);
    
    // Clean up connection - streaming is done
    this.cleanup();
  }
  
  private handleConnectionError(error: Event): void {
    let errorMessage = 'Streaming connection failed';
    
    if (this.currentEventSource?.readyState === EventSource.CLOSED) {
      errorMessage = 'Streaming connection was closed';
    } else if (this.currentEventSource?.readyState === EventSource.CONNECTING) {
      errorMessage = 'Failed to establish streaming connection';
    }
    
    this.currentCallbacks?.onError?.(errorMessage);
    this.cleanup();
  }
}
```

### **Step 6: Connection Management**

```typescript
class StreamingAPI {
  // ... previous methods ...
  
  /**
   * Check if currently streaming
   */
  isStreaming(): boolean {
    return this.currentEventSource !== null && 
           this.currentEventSource.readyState === EventSource.OPEN;
  }
  
  /**
   * Get current connection state
   */
  getConnectionState(): 'connecting' | 'open' | 'closed' | 'none' {
    if (!this.currentEventSource) {
      return 'none';
    }
    
    switch (this.currentEventSource.readyState) {
      case EventSource.CONNECTING:
        return 'connecting';
      case EventSource.OPEN:
        return 'open';
      case EventSource.CLOSED:
        return 'closed';
      default:
        return 'none';
    }
  }
  
  /**
   * Get connection statistics
   */
  getConnectionInfo() {
    if (!this.currentEventSource) {
      return null;
    }
    
    return {
      url: this.currentEventSource.url,
      readyState: this.currentEventSource.readyState,
      withCredentials: this.currentEventSource.withCredentials,
    };
  }
}

// Export singleton instance
export const streamingApi = new StreamingAPI();
```

## 🔧 **Advanced Streaming Patterns**

### **Reconnection Strategy**

```typescript
class ResilientStreamingAPI extends StreamingAPI {
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;
  private reconnectDelay = 1000; // Start with 1 second
  private lastQuery: string | null = null;
  private lastCallbacks: StreamingCallbacks | null = null;
  private lastContext: StreamingContext | undefined;
  
  async processMessageStream(
    query: string,
    callbacks: StreamingCallbacks,
    context?: StreamingContext
  ): Promise<void> {
    // Store for potential reconnection
    this.lastQuery = query;
    this.lastCallbacks = callbacks;
    this.lastContext = context;
    this.reconnectAttempts = 0;
    
    return super.processMessageStream(query, callbacks, context);
  }
  
  private handleConnectionError(error: Event): void {
    console.warn(`Streaming connection error (attempt ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
    
    if (this.reconnectAttempts < this.maxReconnectAttempts && this.lastQuery && this.lastCallbacks) {
      // Try to reconnect
      this.attemptReconnection();
    } else {
      // Give up and notify error
      super.handleConnectionError(error);
    }
  }
  
  private async attemptReconnection(): Promise<void> {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff
    
    console.log(`Attempting to reconnect in ${delay}ms...`);
    
    setTimeout(async () => {
      try {
        if (this.lastQuery && this.lastCallbacks) {
          await this.processMessageStream(this.lastQuery, this.lastCallbacks, this.lastContext);
        }
      } catch (error) {
        console.error('Reconnection failed:', error);
        this.handleConnectionError(new Event('error'));
      }
    }, delay);
  }
}
```

### **Request/Response Middleware**

```typescript
interface StreamingMiddleware {
  onRequest?: (query: string, context?: StreamingContext) => { query: string; context?: StreamingContext };
  onEvent?: (event: StreamEvent) => StreamEvent;
  onError?: (error: string) => string;
}

class MiddlewareStreamingAPI extends StreamingAPI {
  private middleware: StreamingMiddleware[] = [];
  
  addMiddleware(middleware: StreamingMiddleware): void {
    this.middleware.push(middleware);
  }
  
  async processMessageStream(
    query: string,
    callbacks: StreamingCallbacks,
    context?: StreamingContext
  ): Promise<void> {
    // Apply request middleware
    let processedQuery = query;
    let processedContext = context;
    
    for (const mw of this.middleware) {
      if (mw.onRequest) {
        const result = mw.onRequest(processedQuery, processedContext);
        processedQuery = result.query;
        processedContext = result.context;
      }
    }
    
    return super.processMessageStream(processedQuery, callbacks, processedContext);
  }
  
  private handleStreamEvent(event: StreamEvent): void {
    // Apply event middleware
    let processedEvent = event;
    
    for (const mw of this.middleware) {
      if (mw.onEvent) {
        processedEvent = mw.onEvent(processedEvent);
      }
    }
    
    super.handleStreamEvent(processedEvent);
  }
}

// Example middleware usage
const loggingMiddleware: StreamingMiddleware = {
  onRequest: (query, context) => {
    console.log('Streaming request:', query, context);
    return { query, context };
  },
  onEvent: (event) => {
    console.log('Streaming event:', event.event);
    return event;
  },
  onError: (error) => {
    console.error('Streaming error:', error);
    return error;
  },
};

streamingApi.addMiddleware(loggingMiddleware);
```

### **Batched Chunk Processing**

```typescript
class BatchedStreamingAPI extends StreamingAPI {
  private chunkBuffer: string[] = [];
  private batchTimeout: number | null = null;
  private batchSize = 3; // Send chunks in batches of 3
  private batchDelayMs = 100; // Or after 100ms
  
  private handleResponseChunk(chunkEvent: ResponseChunkEvent): void {
    const content = this.extractChunkContent(chunkEvent);
    
    if (content.trim()) {
      this.chunkBuffer.push(content);
      this.scheduleBatchFlush();
    }
  }
  
  private scheduleBatchFlush(): void {
    // Cancel existing timeout
    if (this.batchTimeout) {
      clearTimeout(this.batchTimeout);
    }
    
    // Send batch if we have enough chunks
    if (this.chunkBuffer.length >= this.batchSize) {
      this.flushChunkBatch();
      return;
    }
    
    // Or send after delay
    this.batchTimeout = window.setTimeout(() => {
      this.flushChunkBatch();
    }, this.batchDelayMs);
  }
  
  private flushChunkBatch(): void {
    if (this.chunkBuffer.length === 0) return;
    
    const batchContent = this.chunkBuffer.join('');
    this.chunkBuffer = [];
    
    if (this.batchTimeout) {
      clearTimeout(this.batchTimeout);
      this.batchTimeout = null;
    }
    
    this.currentCallbacks?.onResponseChunk?.(batchContent);
  }
  
  private handleCompleted(completedEvent: CompletedEvent): void {
    // Flush any remaining chunks before completion
    this.flushChunkBatch();
    super.handleCompleted(completedEvent);
  }
}
```

## 🧪 **Testing Your Streaming Service**

### **Mock EventSource for Testing**

```typescript
// src/services/__tests__/streamingApi.test.ts

// Mock EventSource
class MockEventSource {
  public onopen: ((event: Event) => void) | null = null;
  public onmessage: ((event: MessageEvent) => void) | null = null;
  public onerror: ((event: Event) => void) | null = null;
  public readyState = EventSource.CONNECTING;
  
  constructor(public url: string) {
    // Simulate connection opening
    setTimeout(() => {
      this.readyState = EventSource.OPEN;
      this.onopen?.(new Event('open'));
    }, 10);
  }
  
  close() {
    this.readyState = EventSource.CLOSED;
  }
  
  addEventListener(type: string, listener: EventListener) {
    // Mock implementation
  }
  
  // Test helpers
  mockMessage(data: any) {
    const event = new MessageEvent('message', {
      data: JSON.stringify(data)
    });
    this.onmessage?.(event);
  }
  
  mockError() {
    this.onerror?.(new Event('error'));
  }
}

// Replace global EventSource
global.EventSource = MockEventSource as any;

describe('StreamingAPI', () => {
  let api: StreamingAPI;
  let mockCallbacks: StreamingCallbacks;
  
  beforeEach(() => {
    api = new StreamingAPI('http://test-api');
    mockCallbacks = {
      onRoutingStarted: jest.fn(),
      onRoutingCompleted: jest.fn(),
      onResponseChunk: jest.fn(),
      onCompleted: jest.fn(),
      onError: jest.fn(),
    };
  });
  
  it('should handle routing events', async () => {
    await api.processMessageStream('test message', mockCallbacks);
    
    // Simulate routing event
    const mockEventSource = api['currentEventSource'] as any;
    mockEventSource.mockMessage({
      event: 'routing_completed',
      agent_id: 'test-agent',
      agent_name: 'Test Agent',
      protocol: 'a2a',
      confidence: 0.9,
      reasoning: 'Test reasoning'
    });
    
    expect(mockCallbacks.onRoutingCompleted).toHaveBeenCalledWith({
      event: 'routing_completed',
      agent_id: 'test-agent',
      agent_name: 'Test Agent',
      protocol: 'a2a',
      confidence: 0.9,
      reasoning: 'Test reasoning'
    });
  });
  
  it('should parse response chunks correctly', async () => {
    await api.processMessageStream('test message', mockCallbacks);
    
    const mockEventSource = api['currentEventSource'] as any;
    mockEventSource.mockMessage({
      event: 'response_chunk',
      protocol: 'a2a',
      response_data: {
        raw_response: {
          parts: [{ kind: 'text', text: 'Hello world' }]
        }
      }
    });
    
    expect(mockCallbacks.onResponseChunk).toHaveBeenCalledWith('Hello world');
  });
  
  it('should clean up on abort', async () => {
    await api.processMessageStream('test message', mockCallbacks);
    expect(api.isStreaming()).toBe(true);
    
    api.abort();
    expect(api.isStreaming()).toBe(false);
  });
});
```

## 🎯 **Key Takeaways**

1. **EventSource is complex** - Wrap it in a service for easier React integration
2. **Protocol parsing is essential** - Different agents send different chunk formats
3. **Callback architecture works well** - Allows React hooks to handle UI updates
4. **Error recovery is crucial** - Networks fail during streaming more than regular requests
5. **Cleanup is mandatory** - Always close EventSource connections to prevent memory leaks
6. **Testing requires mocking** - EventSource isn't available in Node.js test environments
7. **Batching improves performance** - Don't update UI for every tiny chunk

## 📋 **Next Steps**

In the next tutorial, we'll build the React hook that uses this streaming service:
- **useStreamingOrchestrator**: Complete state management for streaming chat
- **React state patterns**: Managing complex streaming state with useRef and useState
- **Error boundary integration**: Graceful error handling in React
- **Performance optimization**: Preventing unnecessary re-renders during streaming

## 🔗 **Helpful Resources**

- [EventSource API Documentation](https://developer.mozilla.org/en-US/docs/Web/API/EventSource)
- [Server-Sent Events Guide](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Jest Mock Functions](https://jestjs.io/docs/mock-functions)

---

**Next**: [03-streaming-state-management.md](./03-streaming-state-management.md) - useStreamingOrchestrator Hook

**Previous**: [01-understanding-sse.md](./01-understanding-sse.md)