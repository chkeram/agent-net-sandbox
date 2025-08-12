# Example 5: API Service Layer Patterns - Production Service Architecture

## 🎯 **What You'll Learn**

This tutorial provides a **complete breakdown** of our production API service layer from the Agent Network Sandbox frontend. You'll understand:
- **Service layer architecture** patterns and separation of concerns
- **Error handling strategies** with comprehensive error types and recovery
- **Protocol-aware response parsing** for A2A, ACP, and custom protocols
- **Health monitoring and circuit breaker patterns** for resilient systems
- **Caching strategies** and performance optimization techniques
- **TypeScript patterns** for type-safe API interactions

## 🏗️ **Service Architecture Overview**

Our frontend uses **2 primary API services**:
1. **`orchestratorApi.ts`** (307 LOC) - Main orchestrator communication with health monitoring
2. **`streamingApi.ts`** (197 LOC) - Server-Sent Events and real-time streaming

## 🔍 **Complete Service Breakdowns**

---

## **Service 1: `orchestratorApi.ts` - Core API Pattern**

This is our main API service handling synchronous orchestrator communication, protocol parsing, and health monitoring.

### **TypeScript Interface Architecture**

```typescript
// src/services/orchestratorApi.ts
interface OrchestratorRequest {
  query: string
  preferred_protocol?: 'acp' | 'a2a' | 'mcp'
  preferred_agent?: string
  context?: Record<string, any>
  max_tokens?: number
  temperature?: number
}

interface OrchestratorResponse {
  request_id: string
  response: string
  selected_agent: {
    agent_id: string
    name: string
    protocol: string
    confidence: number
    endpoint: string
  }
  processing_time_ms: number
  simulated: boolean
  routing_metadata?: {
    reasoning: string
    alternatives: Array<{
      agent_id: string
      name: string
      rejection_reason: string
    }>
    decision_factors: Record<string, any>
  }
}

interface AgentInfo {
  agent_id: string
  name: string
  protocol: string
  capabilities: Array<{
    name: string
    description: string
    tags: string[]
  }>
  status: 'healthy' | 'degraded' | 'unhealthy'
  endpoint: string
  metadata: Record<string, any>
}

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy'
  version: string
  uptime: number
  agents: {
    total: number
    healthy: number
    unhealthy: number
  }
  last_check: string
}
```

**Key Patterns:**
- **Optional parameters**: Flexible request configuration
- **Union types**: Constrained protocol and status values
- **Nested interfaces**: Complex structured responses
- **Metadata containers**: Extensible data structures

### **Service Class Architecture**

```typescript
class OrchestratorApiService {
  private baseUrl: string
  private defaultTimeout: number
  private healthCache: Map<string, { status: HealthStatus; timestamp: number }> = new Map()
  private requestCache: Map<string, { response: OrchestratorResponse; timestamp: number }> = new Map()
  private circuitBreaker: CircuitBreakerState = { isOpen: false, failureCount: 0, lastFailure: 0 }
  
  constructor(baseUrl: string = 'http://localhost:8004', timeout: number = 30000) {
    this.baseUrl = baseUrl.replace(/\/$/, '') // Remove trailing slash
    this.defaultTimeout = timeout
  }
```

**Key Patterns:**
- **Configuration injection**: Flexible base URL and timeout
- **Internal caching**: Performance optimization with Map-based caches
- **Circuit breaker state**: Resilience pattern for handling failures
- **URL normalization**: Consistent endpoint handling

### **Core API Methods with Error Handling**

```typescript
  /**
   * Send a query to the orchestrator with comprehensive error handling
   */
  async processQuery(request: OrchestratorRequest): Promise<OrchestratorResponse> {
    // Check circuit breaker
    if (this.isCircuitBreakerOpen()) {
      throw new OrchestratorError(
        'Service temporarily unavailable (circuit breaker open)',
        'CIRCUIT_BREAKER_OPEN'
      )
    }
    
    // Check cache first
    const cacheKey = this.generateCacheKey(request)
    const cachedResponse = this.getCachedResponse(cacheKey)
    if (cachedResponse) {
      console.log('🎯 Returning cached response')
      return cachedResponse
    }
    
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.defaultTimeout)
    
    try {
      const response = await fetch(`${this.baseUrl}/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(request),
        signal: controller.signal,
      })
      
      clearTimeout(timeoutId)
      
      if (!response.ok) {
        throw await this.createErrorFromResponse(response)
      }
      
      const data = await response.json()
      const parsedResponse = this.parseResponse(data)
      
      // Cache successful responses
      this.setCachedResponse(cacheKey, parsedResponse)
      
      // Reset circuit breaker on success
      this.resetCircuitBreaker()
      
      return parsedResponse
      
    } catch (error) {
      clearTimeout(timeoutId)
      
      if (error.name === 'AbortError') {
        throw new OrchestratorError('Request timeout', 'TIMEOUT')
      }
      
      // Update circuit breaker
      this.recordFailure()
      
      if (error instanceof OrchestratorError) {
        throw error
      }
      
      // Network or other errors
      throw new OrchestratorError(
        `Network error: ${error.message}`,
        'NETWORK_ERROR',
        error
      )
    }
  }
```

**Key Patterns:**
- **Circuit breaker protection**: Prevents cascade failures
- **Request caching**: Performance optimization for identical queries
- **Timeout management**: AbortController with proper cleanup
- **Error classification**: Different error types for different failure modes
- **Response parsing**: Structured data handling

### **Protocol-Aware Response Parsing**

```typescript
  /**
   * Parse orchestrator response based on protocol type
   */
  private parseResponse(data: any): OrchestratorResponse {
    const response: OrchestratorResponse = {
      request_id: data.request_id || `req-${Date.now()}`,
      response: '',
      selected_agent: {
        agent_id: data.agent_id || 'unknown',
        name: data.agent_name || 'Unknown Agent',
        protocol: data.protocol || 'unknown',
        confidence: data.confidence || 0.8,
        endpoint: data.endpoint || 'unknown',
      },
      processing_time_ms: data.processing_time_ms || data.duration_ms || 0,
      simulated: data.simulated || false,
    }
    
    // Protocol-specific response parsing
    switch (data.protocol?.toLowerCase()) {
      case 'a2a':
        response.response = this.parseA2AResponse(data)
        break
        
      case 'acp':
        response.response = this.parseACPResponse(data)
        break
        
      case 'mcp':
        response.response = this.parseMCPResponse(data)
        break
        
      default:
        response.response = data.response || data.content || 'No response received'
    }
    
    // Parse routing metadata if available
    if (data.routing_metadata || data._routing) {
      response.routing_metadata = this.parseRoutingMetadata(data.routing_metadata || data._routing)
    }
    
    return response
  }
  
  /**
   * Parse A2A protocol response format
   */
  private parseA2AResponse(data: any): string {
    if (data.result?.message) {
      // Handle A2A message format
      const message = data.result.message
      if (message.parts) {
        return message.parts
          .filter((part: any) => part.kind === 'text')
          .map((part: any) => part.text)
          .join('\n')
      }
      return message.content || message.text || String(message)
    }
    
    return data.response || data.content || String(data.result || '')
  }
  
  /**
   * Parse ACP protocol response format
   */
  private parseACPResponse(data: any): string {
    if (data.result?.response) {
      return data.result.response
    }
    
    if (data.result?.content) {
      // Handle structured ACP content
      if (Array.isArray(data.result.content)) {
        return data.result.content
          .map((item: any) => item.text || String(item))
          .join('\n')
      }
      return String(data.result.content)
    }
    
    return data.response || data.content || String(data.result || '')
  }
  
  /**
   * Parse MCP protocol response format  
   */
  private parseMCPResponse(data: any): string {
    // MCP protocol parsing (future implementation)
    return data.response || data.content || 'MCP response received'
  }
```

**Key Patterns:**
- **Protocol abstraction**: Unified interface despite different protocols
- **Defensive parsing**: Multiple fallback strategies
- **Type coercion**: Safe conversion to strings
- **Structured data handling**: Arrays and nested objects

### **Health Monitoring and Circuit Breaker**

```typescript
  /**
   * Check orchestrator health with caching
   */
  async checkHealth(): Promise<HealthStatus> {
    const cacheKey = 'health'
    const cached = this.healthCache.get(cacheKey)
    
    // Return cached health if recent (30 seconds)
    if (cached && Date.now() - cached.timestamp < 30000) {
      return cached.status
    }
    
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000) // Short timeout for health
      
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        signal: controller.signal,
      })
      
      clearTimeout(timeoutId)
      
      if (!response.ok) {
        throw new Error(`Health check failed: ${response.status}`)
      }
      
      const health = await response.json()
      const status: HealthStatus = {
        status: health.status || 'healthy',
        version: health.version || 'unknown',
        uptime: health.uptime || 0,
        agents: health.agents || { total: 0, healthy: 0, unhealthy: 0 },
        last_check: new Date().toISOString(),
      }
      
      // Cache the result
      this.healthCache.set(cacheKey, { status, timestamp: Date.now() })
      
      return status
      
    } catch (error) {
      const unhealthyStatus: HealthStatus = {
        status: 'unhealthy',
        version: 'unknown',
        uptime: 0,
        agents: { total: 0, healthy: 0, unhealthy: 0 },
        last_check: new Date().toISOString(),
      }
      
      // Cache unhealthy status for shorter time
      this.healthCache.set(cacheKey, { 
        status: unhealthyStatus, 
        timestamp: Date.now() - 20000 // Expire sooner
      })
      
      return unhealthyStatus
    }
  }
  
  /**
   * Circuit breaker implementation
   */
  private isCircuitBreakerOpen(): boolean {
    const { isOpen, failureCount, lastFailure } = this.circuitBreaker
    
    if (!isOpen) return false
    
    // Auto-recover after 60 seconds
    if (Date.now() - lastFailure > 60000) {
      this.circuitBreaker.isOpen = false
      this.circuitBreaker.failureCount = 0
      return false
    }
    
    return true
  }
  
  private recordFailure(): void {
    this.circuitBreaker.failureCount++
    this.circuitBreaker.lastFailure = Date.now()
    
    // Open circuit after 5 failures
    if (this.circuitBreaker.failureCount >= 5) {
      this.circuitBreaker.isOpen = true
      console.warn('🚨 Circuit breaker opened due to repeated failures')
    }
  }
  
  private resetCircuitBreaker(): void {
    this.circuitBreaker.isOpen = false
    this.circuitBreaker.failureCount = 0
    this.circuitBreaker.lastFailure = 0
  }
```

**Key Patterns:**
- **Health caching**: Avoid excessive health checks
- **Circuit breaker**: Automatic failure protection
- **Timeout differentiation**: Different timeouts for different operations
- **Auto-recovery**: Circuit breaker automatically recovers

---

## **Service 2: `streamingApi.ts` - Real-time Pattern**

This service handles Server-Sent Events and real-time streaming communication.

### **Streaming Service Architecture**

```typescript
// src/services/streamingApi.ts
interface StreamingRequest {
  query: string
  preferred_protocol?: string
  preferred_agent?: string
  stream_config?: {
    chunk_size?: number
    flush_interval?: number
    enable_reasoning?: boolean
  }
}

interface StreamingCallbacks {
  onPhase?: (phase: StreamingPhase) => void
  onRouting?: (routing: RoutingInfo) => void
  onChunk?: (chunk: string) => void
  onComplete?: (response: StreamingResponse) => void
  onError?: (error: Error) => void
  onClose?: () => void
}

enum StreamingPhase {
  CONNECTING = 'connecting',
  ROUTING = 'routing', 
  PROCESSING = 'processing',
  STREAMING = 'streaming',
  COMPLETE = 'complete',
  ERROR = 'error'
}

class StreamingApiService {
  private baseUrl: string
  private activeStreams: Map<string, EventSource> = new Map()
  private streamCallbacks: Map<string, StreamingCallbacks> = new Map()
  
  constructor(baseUrl: string = 'http://localhost:8004') {
    this.baseUrl = baseUrl.replace(/\/$/, '')
  }
```

### **Core Streaming Implementation**

```typescript
  /**
   * Start a streaming request with comprehensive event handling
   */
  async startStream(
    request: StreamingRequest, 
    callbacks: StreamingCallbacks
  ): Promise<{ streamId: string; stop: () => void }> {
    
    const streamId = `stream-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    
    // Clean up any existing stream
    this.stopStream(streamId)
    
    // Build query parameters
    const params = new URLSearchParams({
      query: request.query,
    })
    
    if (request.preferred_protocol) {
      params.append('preferred_protocol', request.preferred_protocol)
    }
    
    if (request.preferred_agent) {
      params.append('preferred_agent', request.preferred_agent)
    }
    
    if (request.stream_config) {
      params.append('stream_config', JSON.stringify(request.stream_config))
    }
    
    try {
      // Create EventSource connection
      const eventSource = new EventSource(`${this.baseUrl}/stream?${params.toString()}`)
      
      // Store references
      this.activeStreams.set(streamId, eventSource)
      this.streamCallbacks.set(streamId, callbacks)
      
      // Set up event handlers
      this.setupEventHandlers(streamId, eventSource, callbacks)
      
      // Notify connection started
      callbacks.onPhase?.(StreamingPhase.CONNECTING)
      
      return {
        streamId,
        stop: () => this.stopStream(streamId)
      }
      
    } catch (error) {
      callbacks.onError?.(error as Error)
      throw error
    }
  }
  
  /**
   * Set up comprehensive event handling for streaming
   */
  private setupEventHandlers(
    streamId: string,
    eventSource: EventSource,
    callbacks: StreamingCallbacks
  ): void {
    
    // Connection opened
    eventSource.onopen = () => {
      console.log(`🔗 Stream ${streamId} connected`)
      callbacks.onPhase?.(StreamingPhase.ROUTING)
    }
    
    // Generic message handler
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.handleGenericMessage(data, callbacks)
      } catch (error) {
        console.warn('Failed to parse generic message:', event.data)
        callbacks.onChunk?.(event.data) // Fall back to raw data
      }
    }
    
    // Routing phase handler
    eventSource.addEventListener('routing', (event) => {
      try {
        const routingData = JSON.parse(event.data)
        callbacks.onPhase?.(StreamingPhase.PROCESSING)
        callbacks.onRouting?.(routingData)
      } catch (error) {
        console.error('Failed to parse routing data:', error)
      }
    })
    
    // Streaming content handler
    eventSource.addEventListener('chunk', (event) => {
      callbacks.onPhase?.(StreamingPhase.STREAMING)
      callbacks.onChunk?.(event.data)
    })
    
    // Completion handler
    eventSource.addEventListener('complete', (event) => {
      try {
        const completeData = JSON.parse(event.data)
        callbacks.onPhase?.(StreamingPhase.COMPLETE)
        callbacks.onComplete?.(completeData)
      } catch (error) {
        console.error('Failed to parse completion data:', error)
      } finally {
        this.cleanupStream(streamId)
      }
    })
    
    // Error handler
    eventSource.onerror = (event) => {
      console.error(`❌ Stream ${streamId} error:`, event)
      callbacks.onPhase?.(StreamingPhase.ERROR)
      callbacks.onError?.(new Error('Streaming connection failed'))
      this.cleanupStream(streamId)
    }
  }
  
  /**
   * Handle generic messages that don't match specific event types
   */
  private handleGenericMessage(data: any, callbacks: StreamingCallbacks): void {
    if (data.type === 'phase') {
      callbacks.onPhase?.(data.phase as StreamingPhase)
    } else if (data.type === 'chunk') {
      callbacks.onChunk?.(data.content)
    } else if (data.type === 'routing') {
      callbacks.onRouting?.(data)
    } else if (data.type === 'complete') {
      callbacks.onComplete?.(data)
    } else {
      // Unknown message type, treat as chunk
      callbacks.onChunk?.(JSON.stringify(data))
    }
  }
```

### **Stream Management and Cleanup**

```typescript
  /**
   * Stop a specific stream
   */
  stopStream(streamId: string): void {
    const eventSource = this.activeStreams.get(streamId)
    if (eventSource) {
      eventSource.close()
      console.log(`🔌 Stream ${streamId} stopped`)
    }
    this.cleanupStream(streamId)
  }
  
  /**
   * Stop all active streams
   */
  stopAllStreams(): void {
    console.log(`🛑 Stopping ${this.activeStreams.size} active streams`)
    for (const [streamId] of this.activeStreams) {
      this.stopStream(streamId)
    }
  }
  
  /**
   * Clean up stream resources
   */
  private cleanupStream(streamId: string): void {
    const eventSource = this.activeStreams.get(streamId)
    if (eventSource) {
      eventSource.close()
      this.activeStreams.delete(streamId)
    }
    
    const callbacks = this.streamCallbacks.get(streamId)
    if (callbacks) {
      callbacks.onClose?.()
      this.streamCallbacks.delete(streamId)
    }
  }
  
  /**
   * Get information about active streams
   */
  getActiveStreams(): Array<{ streamId: string; readyState: number }> {
    const streams: Array<{ streamId: string; readyState: number }> = []
    
    for (const [streamId, eventSource] of this.activeStreams) {
      streams.push({
        streamId,
        readyState: eventSource.readyState
      })
    }
    
    return streams
  }
}
```

## 🔧 **Error Handling Patterns**

### **Custom Error Classes**

```typescript
// src/services/errors.ts
export class OrchestratorError extends Error {
  constructor(
    message: string,
    public code: string,
    public cause?: Error,
    public response?: Response
  ) {
    super(message)
    this.name = 'OrchestratorError'
  }
  
  static fromResponse(response: Response, message?: string): OrchestratorError {
    const errorMessage = message || `HTTP ${response.status}: ${response.statusText}`
    const code = response.status >= 500 ? 'SERVER_ERROR' : 'CLIENT_ERROR'
    return new OrchestratorError(errorMessage, code, undefined, response)
  }
}

export class StreamingError extends Error {
  constructor(
    message: string,
    public phase: StreamingPhase,
    public cause?: Error
  ) {
    super(message)
    this.name = 'StreamingError'
  }
}

// Error recovery utilities
export const isRetryableError = (error: Error): boolean => {
  if (error instanceof OrchestratorError) {
    return ['NETWORK_ERROR', 'TIMEOUT', 'SERVER_ERROR'].includes(error.code)
  }
  return false
}

export const getRetryDelay = (attemptNumber: number): number => {
  // Exponential backoff: 1s, 2s, 4s, 8s, max 30s
  return Math.min(1000 * Math.pow(2, attemptNumber), 30000)
}
```

## 🎯 **Service Integration Pattern**

### **Combined Service Usage**

```typescript
// src/services/index.ts
export class AgentNetworkAPI {
  public readonly orchestrator: OrchestratorApiService
  public readonly streaming: StreamingApiService
  
  constructor(baseUrl: string = 'http://localhost:8004') {
    this.orchestrator = new OrchestratorApiService(baseUrl)
    this.streaming = new StreamingApiService(baseUrl)
  }
  
  /**
   * High-level method combining both services
   */
  async sendMessage(
    query: string,
    options: {
      useStreaming?: boolean
      preferred_protocol?: string
      preferred_agent?: string
    } = {}
  ): Promise<OrchestratorResponse | { streamId: string; stop: () => void }> {
    
    if (options.useStreaming) {
      // Use streaming service
      return this.streaming.startStream(
        {
          query,
          preferred_protocol: options.preferred_protocol,
          preferred_agent: options.preferred_agent,
        },
        {
          onError: (error) => console.error('Streaming error:', error),
          onComplete: (response) => console.log('Stream complete:', response),
        }
      )
    } else {
      // Use regular orchestrator service
      return this.orchestrator.processQuery({
        query,
        preferred_protocol: options.preferred_protocol as any,
        preferred_agent: options.preferred_agent,
      })
    }
  }
}

// Create singleton instance
export const agentNetworkAPI = new AgentNetworkAPI()
```

## 🎯 **Testing Patterns**

### **Service Testing with Mock Implementations**

```typescript
// src/services/__tests__/orchestratorApi.test.ts
import { OrchestratorApiService } from '../orchestratorApi'

describe('OrchestratorApiService', () => {
  let service: OrchestratorApiService
  let mockFetch: jest.Mock
  
  beforeEach(() => {
    mockFetch = jest.fn()
    global.fetch = mockFetch
    service = new OrchestratorApiService('http://test.com')
  })
  
  describe('processQuery', () => {
    it('should handle successful A2A response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          protocol: 'a2a',
          result: {
            message: {
              parts: [
                { kind: 'text', text: 'Hello from A2A agent' }
              ]
            }
          },
          agent_name: 'Math Agent',
          confidence: 0.95
        })
      })
      
      const response = await service.processQuery({ query: 'Test query' })
      
      expect(response.response).toBe('Hello from A2A agent')
      expect(response.selected_agent.name).toBe('Math Agent')
      expect(response.selected_agent.confidence).toBe(0.95)
    })
    
    it('should handle circuit breaker', async () => {
      // Simulate 5 failures to trigger circuit breaker
      mockFetch.mockRejectedValue(new Error('Network error'))
      
      for (let i = 0; i < 5; i++) {
        try {
          await service.processQuery({ query: 'Test' })
        } catch {}
      }
      
      // Next request should be blocked by circuit breaker
      await expect(service.processQuery({ query: 'Test' }))
        .rejects.toThrow('Service temporarily unavailable')
    })
  })
  
  describe('health monitoring', () => {
    it('should cache health status', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'healthy', version: '1.0.0' })
      })
      
      // First call
      const health1 = await service.checkHealth()
      expect(health1.status).toBe('healthy')
      
      // Second call should use cache
      const health2 = await service.checkHealth()
      expect(health2.status).toBe('healthy')
      
      // Should only have made one network request
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })
  })
})
```

## 🎯 **Key Production Patterns**

1. **Service Layer Separation**: Clear boundaries between API concerns and UI logic
2. **Protocol Abstraction**: Unified interface across different agent protocols  
3. **Error Classification**: Different error types enable appropriate handling strategies
4. **Circuit Breaker**: Prevents cascade failures in distributed systems
5. **Caching Strategy**: Performance optimization with appropriate cache invalidation
6. **Resource Management**: Proper cleanup of streams and network connections
7. **Type Safety**: Complete TypeScript coverage with runtime validation
8. **Monitoring**: Health checks and observable system state

These services demonstrate **enterprise-grade patterns** for building robust, scalable API layers that can handle complex multi-protocol communication with excellent error handling and performance characteristics.

---

**Next**: Back to [README.md](../README.md) - Complete Tutorial Series Overview  
**Previous**: [04-hooks-implementation-guide.md](./04-hooks-implementation-guide.md)