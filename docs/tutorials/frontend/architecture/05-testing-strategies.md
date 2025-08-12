# Architecture 5: Testing Strategies - Comprehensive Testing Approaches

## 🎯 **Learning Objectives**

By the end of this tutorial, you will understand:
- Testing strategies for complex streaming React applications
- How to test real-time features like Server-Sent Events
- Integration testing patterns for multi-protocol agent systems
- Performance testing and monitoring strategies
- Mock strategies for external services and streaming data
- End-to-end testing patterns for conversation flows

## 🧪 **The Testing Challenge**

Testing streaming applications presents unique challenges:
- **Asynchronous Streams**: Hard to test time-based data flows
- **Real-time Events**: SSE and WebSocket connections are complex to mock
- **Multi-Protocol Integration**: Testing ACP, A2A, and MCP interactions
- **State Management**: Complex state transitions need thorough testing
- **Performance Testing**: Memory leaks and rendering performance
- **User Flows**: End-to-end conversation testing across multiple agents

**Our goal**: Build **comprehensive test coverage** that ensures reliability in production.

## 📋 **Testing Architecture Overview**

### **Testing Pyramid for Streaming Apps**

```
┌─────────────────────────────────────────────┐
│              E2E Tests                      │ ← Full user journeys
├─────────────────────────────────────────────┤
│         Integration Tests                   │ ← API + component integration
├─────────────────────────────────────────────┤
│          Component Tests                    │ ← React component behavior
├─────────────────────────────────────────────┤
│            Unit Tests                       │ ← Individual functions/hooks
└─────────────────────────────────────────────┘
```

## 🔧 **Unit Testing Patterns**

### **Pattern 1: Testing Custom Hooks with Async Behavior**

```typescript
// src/hooks/__tests__/useStreamingOrchestrator.test.ts
import { renderHook, act, waitFor } from '@testing-library/react'
import { useStreamingOrchestrator } from '../useStreamingOrchestrator'

// Mock the streaming API
jest.mock('../../services/streamingApi', () => ({
  processMessage: jest.fn(),
}))

// Mock fetch for SSE
global.fetch = jest.fn()

describe('useStreamingOrchestrator', () => {
  let mockProcessMessage: jest.MockedFunction<any>

  beforeEach(() => {
    jest.clearAllMocks()
    mockProcessMessage = require('../../services/streamingApi').processMessage
    
    // Mock fetch implementation for EventSource polyfill
    ;(global.fetch as jest.Mock).mockImplementation(() =>
      Promise.resolve({
        ok: true,
        headers: new Headers({ 'content-type': 'text/plain' }),
        body: {
          getReader: () => ({
            read: jest.fn().mockResolvedValue({ done: true, value: undefined })
          })
        }
      })
    )
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('should handle successful streaming', async () => {
    const mockCallbacks = {
      onData: jest.fn(),
      onComplete: jest.fn(),
      onError: jest.fn(),
    }

    // Mock successful streaming response
    mockProcessMessage.mockImplementation(async (query, callbacks) => {
      // Simulate streaming chunks
      callbacks.onData('Hello')
      callbacks.onData(' World')
      callbacks.onComplete({ 
        content: 'Hello World', 
        agent: 'test-agent',
        confidence: 0.9 
      })
    })

    const { result } = renderHook(() => useStreamingOrchestrator())

    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBe(null)

    // Start streaming
    await act(async () => {
      await result.current.streamMessage('Test query', mockCallbacks)
    })

    // Verify state updates
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.response).toEqual({
      content: 'Hello World',
      agent: 'test-agent',
      confidence: 0.9
    })

    expect(mockCallbacks.onData).toHaveBeenCalledWith('Hello')
    expect(mockCallbacks.onData).toHaveBeenCalledWith(' World')
    expect(mockCallbacks.onComplete).toHaveBeenCalledWith({
      content: 'Hello World',
      agent: 'test-agent',
      confidence: 0.9
    })
  })

  it('should handle streaming errors', async () => {
    const mockError = new Error('Network error')
    const mockCallbacks = {
      onData: jest.fn(),
      onComplete: jest.fn(),
      onError: jest.fn(),
    }

    mockProcessMessage.mockRejectedValue(mockError)

    const { result } = renderHook(() => useStreamingOrchestrator())

    await act(async () => {
      await result.current.streamMessage('Test query', mockCallbacks)
    })

    await waitFor(() => {
      expect(result.current.error).toEqual(mockError)
    })

    expect(result.current.isLoading).toBe(false)
    expect(result.current.response).toBe(null)
  })

  it('should handle streaming cancellation', async () => {
    mockProcessMessage.mockImplementation(async (query, callbacks, signal) => {
      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          callbacks.onComplete({ content: 'Completed' })
          resolve(undefined)
        }, 1000)

        signal?.addEventListener('abort', () => {
          clearTimeout(timeout)
          reject(new Error('Aborted'))
        })
      })
    })

    const { result } = renderHook(() => useStreamingOrchestrator())

    // Start streaming
    const streamPromise = act(async () => {
      result.current.streamMessage('Test query')
    })

    // Cancel immediately
    act(() => {
      result.current.cancelStream()
    })

    await expect(streamPromise).rejects.toThrow('Aborted')
    
    expect(result.current.isLoading).toBe(false)
  })

  it('should maintain ref consistency during streaming', async () => {
    const { result } = renderHook(() => useStreamingOrchestrator())

    const initialContent = result.current.getCurrentContent()
    expect(initialContent).toBe('')

    mockProcessMessage.mockImplementation(async (query, callbacks) => {
      callbacks.onData('Chunk 1')
      callbacks.onData('Chunk 2')
    })

    await act(async () => {
      await result.current.streamMessage('Test')
    })

    // Content should be accumulated in ref
    const finalContent = result.current.getCurrentContent()
    expect(finalContent).toBe('Chunk 1Chunk 2')
  })
})

// Testing memory management hooks
describe('useConversationMemory', () => {
  beforeEach(() => {
    // Reset memory manager state
    conversationMemory.destroy()
  })

  it('should manage conversation windows correctly', async () => {
    const { result } = renderHook(() => useConversationState('test-conversation'))

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    // Add messages and verify memory management
    const testMessage = {
      id: 'msg-1',
      content: 'Test message',
      role: 'user' as const,
      timestamp: new Date(),
    }

    await act(async () => {
      await result.current.addMessage(testMessage)
    })

    expect(result.current.messages).toContain(testMessage)
  })
})
```

### **Pattern 2: Testing Server-Sent Events**

```typescript
// src/services/__tests__/streamingApi.test.ts
import { streamingApi } from '../streamingApi'

// Mock EventSource
class MockEventSource {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSED = 2

  readyState = MockEventSource.CONNECTING
  url = ''
  
  onopen: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null

  constructor(url: string) {
    this.url = url
    
    // Simulate connection opening
    setTimeout(() => {
      this.readyState = MockEventSource.OPEN
      this.onopen?.(new Event('open'))
    }, 10)
  }

  close() {
    this.readyState = MockEventSource.CLOSED
  }

  // Helper method to simulate messages
  simulateMessage(data: string, type = 'message') {
    if (this.readyState === MockEventSource.OPEN) {
      const event = new MessageEvent('message', { 
        data, 
        lastEventId: '',
        origin: this.url 
      })
      this.onmessage?.(event)
    }
  }

  simulateError() {
    this.onerror?.(new Event('error'))
  }
}

// Replace global EventSource
;(global as any).EventSource = MockEventSource

describe('streamingApi', () => {
  let mockEventSource: MockEventSource

  beforeEach(() => {
    jest.clearAllMocks()
  })

  afterEach(() => {
    if (mockEventSource) {
      mockEventSource.close()
    }
  })

  it('should handle successful message streaming', async () => {
    const callbacks = {
      onData: jest.fn(),
      onComplete: jest.fn(),
      onError: jest.fn(),
    }

    const streamPromise = streamingApi.processMessage('Hello', callbacks)

    // Wait for connection to open
    await new Promise(resolve => setTimeout(resolve, 20))

    // Find the created EventSource
    mockEventSource = (global as any).lastCreatedEventSource

    // Simulate streaming data
    mockEventSource.simulateMessage(JSON.stringify({
      type: 'data',
      content: 'Hello'
    }))

    mockEventSource.simulateMessage(JSON.stringify({
      type: 'data', 
      content: ' World'
    }))

    mockEventSource.simulateMessage(JSON.stringify({
      type: 'complete',
      content: 'Hello World',
      agent: 'test-agent'
    }))

    await streamPromise

    expect(callbacks.onData).toHaveBeenCalledWith('Hello')
    expect(callbacks.onData).toHaveBeenCalledWith(' World')
    expect(callbacks.onComplete).toHaveBeenCalledWith({
      content: 'Hello World',
      agent: 'test-agent'
    })
  })

  it('should handle streaming errors', async () => {
    const callbacks = {
      onData: jest.fn(),
      onComplete: jest.fn(),
      onError: jest.fn(),
    }

    const streamPromise = streamingApi.processMessage('Hello', callbacks)

    await new Promise(resolve => setTimeout(resolve, 20))

    mockEventSource = (global as any).lastCreatedEventSource
    mockEventSource.simulateError()

    await expect(streamPromise).rejects.toThrow()
    expect(callbacks.onError).toHaveBeenCalled()
  })

  it('should handle connection timeout', async () => {
    // Mock shorter timeout for testing
    const originalTimeout = streamingApi.timeout
    streamingApi.timeout = 100

    const callbacks = {
      onData: jest.fn(),
      onComplete: jest.fn(),
      onError: jest.fn(),
    }

    await expect(
      streamingApi.processMessage('Hello', callbacks)
    ).rejects.toThrow('Connection timeout')

    // Restore timeout
    streamingApi.timeout = originalTimeout
  })
})
```

## 🧩 **Component Testing Patterns**

### **Pattern 3: Testing Streaming Components**

```typescript
// src/components/__tests__/StreamingMessage.test.tsx
import React from 'react'
import { render, screen, waitFor, act } from '@testing-library/react'
import { StreamingMessage } from '../StreamingMessage'

// Mock the streaming hook
jest.mock('../../hooks/useOptimizedStreaming', () => ({
  useOptimizedStreaming: jest.fn()
}))

describe('StreamingMessage', () => {
  let mockHook: jest.MockedFunction<any>

  beforeEach(() => {
    mockHook = require('../../hooks/useOptimizedStreaming').useOptimizedStreaming
    
    mockHook.mockReturnValue({
      content: '',
      isStreaming: false,
      addToStream: jest.fn(),
      startStream: jest.fn(),
      endStream: jest.fn(),
      stats: {
        totalUpdates: 0,
        droppedUpdates: 0,
        averageLatency: 0,
        lastUpdateTime: 0,
        queueSize: 0,
      }
    })
  })

  it('should render initial message content', () => {
    render(<StreamingMessage initialContent="Hello" />)
    
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })

  it('should update content during streaming', async () => {
    const mockAddToStream = jest.fn()
    mockHook.mockReturnValue({
      content: 'Hello World',
      isStreaming: true,
      addToStream: mockAddToStream,
      startStream: jest.fn(),
      endStream: jest.fn(),
      stats: { totalUpdates: 2, droppedUpdates: 0, averageLatency: 15, lastUpdateTime: Date.now(), queueSize: 0 }
    })

    render(<StreamingMessage onStreamChunk={mockAddToStream} />)

    expect(screen.getByText('Hello World')).toBeInTheDocument()
    
    // Verify streaming indicator is shown
    expect(screen.getByTestId('streaming-indicator')).toBeInTheDocument()
  })

  it('should handle streaming completion', async () => {
    const onComplete = jest.fn()
    
    mockHook.mockReturnValue({
      content: 'Complete message',
      isStreaming: false,
      addToStream: jest.fn(),
      startStream: jest.fn(),
      endStream: jest.fn(),
      stats: { totalUpdates: 5, droppedUpdates: 0, averageLatency: 20, lastUpdateTime: Date.now(), queueSize: 0 }
    })

    render(<StreamingMessage onComplete={onComplete} />)

    await waitFor(() => {
      expect(onComplete).toHaveBeenCalledWith('Complete message')
    })
  })

  it('should display performance warnings in development', () => {
    // Mock development environment
    const originalEnv = process.env.NODE_ENV
    process.env.NODE_ENV = 'development'

    mockHook.mockReturnValue({
      content: 'Test content',
      isStreaming: false,
      addToStream: jest.fn(),
      startStream: jest.fn(),
      endStream: jest.fn(),
      stats: { totalUpdates: 100, droppedUpdates: 15, averageLatency: 150, lastUpdateTime: Date.now(), queueSize: 10 }
    })

    render(<StreamingMessage showDebugInfo />)

    expect(screen.getByText(/Dropped: 15/)).toBeInTheDocument()
    expect(screen.getByText(/Latency: 150.0ms/)).toBeInTheDocument()

    // Restore environment
    process.env.NODE_ENV = originalEnv
  })
})

// Testing virtualized lists
describe('VirtualizedMessageList', () => {
  beforeEach(() => {
    // Mock react-window
    jest.mock('react-window', () => ({
      FixedSizeList: ({ children, itemData, itemCount }: any) => (
        <div data-testid="virtualized-list">
          {Array.from({ length: Math.min(itemCount, 5) }, (_, index) => 
            children({ index, style: {}, data: itemData })
          )}
        </div>
      ),
      VariableSizeList: ({ children, itemData, itemCount }: any) => (
        <div data-testid="virtualized-list">
          {Array.from({ length: Math.min(itemCount, 5) }, (_, index) => 
            children({ index, style: {}, data: itemData })
          )}
        </div>
      )
    }))

    // Mock AutoSizer
    jest.mock('react-virtualized-auto-sizer', () => ({
      AutoSizer: ({ children }: any) => children({ width: 800, height: 600 })
    }))
  })

  it('should render messages in virtualized list', () => {
    const mockMessages = [
      { id: '1', content: 'Message 1', role: 'user' as const, timestamp: new Date() },
      { id: '2', content: 'Message 2', role: 'assistant' as const, timestamp: new Date() },
    ]

    render(
      <VirtualizedMessageList 
        conversationId="test-conv"
        messages={mockMessages}
      />
    )

    expect(screen.getByTestId('virtualized-list')).toBeInTheDocument()
    expect(screen.getByText('Message 1')).toBeInTheDocument()
    expect(screen.getByText('Message 2')).toBeInTheDocument()
  })

  it('should handle infinite scrolling', async () => {
    const onLoadMore = jest.fn()
    const mockMessages = Array.from({ length: 50 }, (_, i) => ({
      id: `msg-${i}`,
      content: `Message ${i}`,
      role: 'user' as const,
      timestamp: new Date()
    }))

    render(
      <VirtualizedMessageList
        conversationId="test-conv"
        messages={mockMessages}
        onLoadMore={onLoadMore}
      />
    )

    // Simulate scrolling to trigger load more
    // This would typically involve mocking the onItemsRendered callback
    await act(async () => {
      // Trigger the load more condition
      const list = screen.getByTestId('virtualized-list')
      // In a real scenario, you'd simulate the scroll event that triggers onItemsRendered
    })

    // Verify that onLoadMore was called when appropriate
    expect(onLoadMore).toHaveBeenCalled()
  })
})
```

## 🔗 **Integration Testing Patterns**

### **Pattern 4: Testing Multi-Protocol Agent Integration**

```typescript
// src/integration/__tests__/agentOrchestration.test.ts
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { ChatInterface } from '../../components/ChatInterface'
import { orchestratorApi } from '../../services/orchestratorApi'
import { a2aApi } from '../../services/a2aApi'
import { acpApi } from '../../services/acpApi'

// Mock all the APIs
jest.mock('../../services/orchestratorApi')
jest.mock('../../services/a2aApi')  
jest.mock('../../services/acpApi')

describe('Agent Orchestration Integration', () => {
  let mockOrchestratorApi: jest.Mocked<typeof orchestratorApi>
  let mockA2AApi: jest.Mocked<typeof a2aApi>
  let mockACPApi: jest.Mocked<typeof acpApi>

  beforeEach(() => {
    mockOrchestratorApi = orchestratorApi as jest.Mocked<typeof orchestratorApi>
    mockA2AApi = a2aApi as jest.Mocked<typeof a2aApi>
    mockACPApi = acpApi as jest.Mocked<typeof acpApi>

    // Clear all mocks
    jest.clearAllMocks()
  })

  it('should route math questions to A2A agent', async () => {
    // Mock orchestrator routing decision
    mockOrchestratorApi.processMessage.mockResolvedValue({
      selectedAgent: {
        id: 'a2a-math-agent',
        protocol: 'a2a',
        endpoint: 'http://localhost:8002',
        confidence: 0.95
      },
      routingReason: 'Math operation detected',
      content: 'The answer is 4'
    })

    // Mock A2A API response
    mockA2AApi.sendMessage.mockResolvedValue({
      id: 'response-1',
      content: 'The answer is 4',
      role: 'assistant',
      timestamp: new Date()
    })

    render(<ChatInterface />)

    // Send math question
    const input = screen.getByPlaceholderText('Type your message...')
    const sendButton = screen.getByText('Send')

    fireEvent.change(input, { target: { value: 'What is 2 + 2?' } })
    fireEvent.click(sendButton)

    // Wait for orchestrator to route the message
    await waitFor(() => {
      expect(mockOrchestratorApi.processMessage).toHaveBeenCalledWith('What is 2 + 2?')
    })

    // Verify the correct agent was selected and response displayed
    await waitFor(() => {
      expect(screen.getByText('The answer is 4')).toBeInTheDocument()
      expect(screen.getByText('via a2a-math-agent')).toBeInTheDocument()
    })
  })

  it('should route greetings to ACP agent', async () => {
    mockOrchestratorApi.processMessage.mockResolvedValue({
      selectedAgent: {
        id: 'acp-hello-world',
        protocol: 'acp',
        endpoint: 'http://localhost:8000',
        confidence: 0.88
      },
      routingReason: 'Greeting detected',
      content: 'Hello! How can I help you today?'
    })

    mockACPApi.sendMessage.mockResolvedValue({
      id: 'response-2',
      content: 'Hello! How can I help you today?',
      role: 'assistant',
      timestamp: new Date()
    })

    render(<ChatInterface />)

    const input = screen.getByPlaceholderText('Type your message...')
    const sendButton = screen.getByText('Send')

    fireEvent.change(input, { target: { value: 'Hello there!' } })
    fireEvent.click(sendButton)

    await waitFor(() => {
      expect(mockOrchestratorApi.processMessage).toHaveBeenCalledWith('Hello there!')
    })

    await waitFor(() => {
      expect(screen.getByText('Hello! How can I help you today?')).toBeInTheDocument()
      expect(screen.getByText('via acp-hello-world')).toBeInTheDocument()
    })
  })

  it('should handle agent failures gracefully', async () => {
    // Mock orchestrator success but agent failure
    mockOrchestratorApi.processMessage.mockResolvedValue({
      selectedAgent: {
        id: 'a2a-math-agent',
        protocol: 'a2a',
        endpoint: 'http://localhost:8002',
        confidence: 0.95
      },
      routingReason: 'Math operation detected',
      content: ''
    })

    // Mock A2A API failure
    mockA2AApi.sendMessage.mockRejectedValue(new Error('Agent unavailable'))

    render(<ChatInterface />)

    const input = screen.getByPlaceholderText('Type your message...')
    const sendButton = screen.getByText('Send')

    fireEvent.change(input, { target: { value: 'What is 5 * 5?' } })
    fireEvent.click(sendButton)

    await waitFor(() => {
      expect(mockOrchestratorApi.processMessage).toHaveBeenCalled()
    })

    // Should display error message
    await waitFor(() => {
      expect(screen.getByText(/agent unavailable/i)).toBeInTheDocument()
    })
  })

  it('should handle streaming responses from agents', async () => {
    const mockCallbacks = {
      onData: jest.fn(),
      onComplete: jest.fn(),
      onError: jest.fn()
    }

    // Mock streaming orchestrator response
    mockOrchestratorApi.processMessage.mockImplementation(async (query, callbacks) => {
      callbacks?.onData('Calculating...')
      callbacks?.onData(' The answer is ')
      callbacks?.onData('25')
      callbacks?.onComplete({
        content: 'Calculating... The answer is 25',
        agent: 'a2a-math-agent',
        confidence: 0.98
      })
    })

    render(<ChatInterface />)

    const input = screen.getByPlaceholderText('Type your message...')
    const sendButton = screen.getByText('Send')

    fireEvent.change(input, { target: { value: 'What is 5 * 5?' } })
    fireEvent.click(sendButton)

    // Wait for streaming to complete
    await waitFor(() => {
      expect(screen.getByText('Calculating... The answer is 25')).toBeInTheDocument()
    })
  })
})

// Testing conversation persistence
describe('Conversation Persistence Integration', () => {
  beforeEach(() => {
    // Clear IndexedDB
    jest.clearAllMocks()
  })

  it('should save and load conversation history', async () => {
    const { rerender } = render(<ChatInterface conversationId="test-conv-1" />)

    // Send a message
    const input = screen.getByPlaceholderText('Type your message...')
    fireEvent.change(input, { target: { value: 'Hello' } })
    fireEvent.click(screen.getByText('Send'))

    await waitFor(() => {
      expect(screen.getByText('Hello')).toBeInTheDocument()
    })

    // Unmount and remount component (simulating page reload)
    rerender(<div />)
    rerender(<ChatInterface conversationId="test-conv-1" />)

    // Should load previous messages
    await waitFor(() => {
      expect(screen.getByText('Hello')).toBeInTheDocument()
    })
  })
})
```

## 🎭 **End-to-End Testing Patterns**

### **Pattern 5: Complete User Journey Testing**

```typescript
// e2e/conversation-flows.spec.ts (Playwright)
import { test, expect } from '@playwright/test'

test.describe('Conversation Flows', () => {
  test.beforeEach(async ({ page }) => {
    // Start with a clean state
    await page.goto('http://localhost:3000')
    await page.waitForLoadState('networkidle')
  })

  test('should handle complete math conversation flow', async ({ page }) => {
    // Start a new conversation
    const messageInput = page.getByPlaceholder('Type your message...')
    const sendButton = page.getByRole('button', { name: 'Send' })

    // Send initial math question
    await messageInput.fill('What is 15 * 23?')
    await sendButton.click()

    // Wait for agent routing and response
    await expect(page.locator('[data-testid="message-list"]')).toContainText('What is 15 * 23?')
    
    // Should route to A2A math agent and show calculation
    await expect(page.locator('[data-testid="agent-indicator"]')).toContainText('a2a-math-agent')
    await expect(page.locator('[data-testid="message-list"]')).toContainText('345')

    // Ask follow-up question
    await messageInput.fill('Can you show me how you calculated that?')
    await sendButton.click()

    // Should stay with same agent for related question
    await expect(page.locator('[data-testid="message-list"]')).toContainText('15 × 23 = 345')
    
    // Switch to greeting (should route to different agent)
    await messageInput.fill('Thanks for your help!')
    await sendButton.click()

    // Should route to ACP agent
    await expect(page.locator('[data-testid="agent-indicator"]').last()).toContainText('acp-hello-world')
    await expect(page.locator('[data-testid="message-list"]')).toContainText('You\'re welcome!')
  })

  test('should handle streaming responses', async ({ page }) => {
    await page.goto('http://localhost:3000')

    const messageInput = page.getByPlaceholder('Type your message...')
    await messageInput.fill('Write me a short story')
    await page.getByRole('button', { name: 'Send' }).click()

    // Wait for streaming to start
    await expect(page.locator('[data-testid="streaming-indicator"]')).toBeVisible()

    // Wait for content to appear progressively
    await expect(page.locator('[data-testid="streaming-content"]')).toContainText('Once upon a time')
    
    // Wait for streaming to complete
    await expect(page.locator('[data-testid="streaming-indicator"]')).toBeHidden({ timeout: 30000 })
    
    // Verify complete story is present
    const storyContent = await page.locator('[data-testid="message-content"]').last().textContent()
    expect(storyContent).toBeTruthy()
    expect(storyContent!.length).toBeGreaterThan(100)
  })

  test('should handle network errors gracefully', async ({ page }) => {
    // Intercept and fail API requests
    await page.route('**/api/**', route => {
      route.abort('failed')
    })

    const messageInput = page.getByPlaceholder('Type your message...')
    await messageInput.fill('Hello')
    await page.getByRole('button', { name: 'Send' }).click()

    // Should show error state
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible()
    await expect(page.locator('[data-testid="error-message"]')).toContainText('network error')
    
    // Should show retry option
    await expect(page.getByRole('button', { name: 'Retry' })).toBeVisible()
    
    // Test retry functionality
    await page.unroute('**/api/**') // Remove network failure
    await page.getByRole('button', { name: 'Retry' }).click()
    
    // Should succeed on retry
    await expect(page.locator('[data-testid="message-list"]')).toContainText('Hello')
  })

  test('should maintain conversation state across page reloads', async ({ page }) => {
    const messageInput = page.getByPlaceholder('Type your message...')
    
    // Send several messages
    const messages = ['Hello', 'How are you?', 'What can you help me with?']
    
    for (const message of messages) {
      await messageInput.fill(message)
      await page.getByRole('button', { name: 'Send' }).click()
      await expect(page.locator('[data-testid="message-list"]')).toContainText(message)
    }

    // Reload the page
    await page.reload()
    await page.waitForLoadState('networkidle')

    // All messages should still be present
    for (const message of messages) {
      await expect(page.locator('[data-testid="message-list"]')).toContainText(message)
    }
  })

  test('should handle concurrent conversations', async ({ context }) => {
    // Open multiple tabs for concurrent testing
    const page1 = await context.newPage()
    const page2 = await context.newPage()
    
    await page1.goto('http://localhost:3000')
    await page2.goto('http://localhost:3000')

    // Send different messages in each tab
    await page1.getByPlaceholder('Type your message...').fill('What is 2 + 2?')
    await page2.getByPlaceholder('Type your message...').fill('Hello there!')
    
    await Promise.all([
      page1.getByRole('button', { name: 'Send' }).click(),
      page2.getByRole('button', { name: 'Send' }).click()
    ])

    // Each should get appropriate responses
    await expect(page1.locator('[data-testid="message-list"]')).toContainText('4')
    await expect(page2.locator('[data-testid="message-list"]')).toContainText('Hello')
    
    // Messages shouldn't leak between conversations
    await expect(page1.locator('[data-testid="message-list"]')).not.toContainText('Hello')
    await expect(page2.locator('[data-testid="message-list"]')).not.toContainText('4')
  })
})

// Performance testing
test.describe('Performance Tests', () => {
  test('should handle large conversation loads', async ({ page }) => {
    await page.goto('http://localhost:3000/conversation/large-test')

    // Wait for large conversation to load
    await page.waitForSelector('[data-testid="message-list"]')
    
    // Measure initial render time
    const renderTime = await page.evaluate(() => {
      const start = performance.now()
      // Trigger a re-render by scrolling
      document.querySelector('[data-testid="message-list"]')?.scrollTo(0, 1000)
      return performance.now() - start
    })

    // Should render within reasonable time (less than 100ms)
    expect(renderTime).toBeLessThan(100)
    
    // Test memory usage doesn't grow excessively
    const initialMemory = await page.evaluate(() => (performance as any).memory?.usedJSHeapSize || 0)
    
    // Scroll through large conversation
    for (let i = 0; i < 10; i++) {
      await page.evaluate((scrollAmount) => {
        document.querySelector('[data-testid="message-list"]')?.scrollBy(0, scrollAmount)
      }, 500)
      await page.waitForTimeout(100)
    }
    
    const finalMemory = await page.evaluate(() => (performance as any).memory?.usedJSHeapSize || 0)
    
    // Memory shouldn't grow by more than 50MB
    expect(finalMemory - initialMemory).toBeLessThan(50 * 1024 * 1024)
  })
})
```

## 🎯 **Performance Testing Utilities**

### **Pattern 6: Memory Leak Detection**

```typescript
// src/test-utils/memoryTesting.ts
export class MemoryTestHelper {
  private initialMemory: number = 0
  private measurements: number[] = []

  startMonitoring(): void {
    this.initialMemory = this.getCurrentMemoryUsage()
    this.measurements = [this.initialMemory]
  }

  recordMeasurement(label?: string): number {
    const current = this.getCurrentMemoryUsage()
    this.measurements.push(current)
    
    if (label && process.env.NODE_ENV === 'test') {
      console.log(`Memory measurement (${label}): ${(current / 1024 / 1024).toFixed(2)}MB`)
    }
    
    return current
  }

  getMemoryGrowth(): number {
    if (this.measurements.length < 2) return 0
    return this.measurements[this.measurements.length - 1] - this.initialMemory
  }

  checkForLeaks(maxGrowthMB: number = 10): boolean {
    const growthBytes = this.getMemoryGrowth()
    const growthMB = growthBytes / 1024 / 1024
    
    if (growthMB > maxGrowthMB) {
      console.warn(`Potential memory leak detected: ${growthMB.toFixed(2)}MB growth`)
      return true
    }
    
    return false
  }

  private getCurrentMemoryUsage(): number {
    if (typeof window !== 'undefined' && (window as any).performance?.memory) {
      return (window as any).performance.memory.usedJSHeapSize
    }
    
    // Fallback for Node.js environment
    if (typeof process !== 'undefined' && process.memoryUsage) {
      return process.memoryUsage().heapUsed
    }
    
    return 0
  }

  generateReport(): string {
    const growth = this.getMemoryGrowth()
    const growthMB = growth / 1024 / 1024
    
    return `Memory Report:
      Initial: ${(this.initialMemory / 1024 / 1024).toFixed(2)}MB
      Final: ${(this.measurements[this.measurements.length - 1] / 1024 / 1024).toFixed(2)}MB
      Growth: ${growthMB.toFixed(2)}MB
      Measurements: ${this.measurements.length}
      Leak Risk: ${this.checkForLeaks() ? 'HIGH' : 'LOW'}
    `
  }
}

// Usage in tests
describe('Memory Management', () => {
  let memoryHelper: MemoryTestHelper

  beforeEach(() => {
    memoryHelper = new MemoryTestHelper()
    memoryHelper.startMonitoring()
  })

  afterEach(() => {
    if (process.env.NODE_ENV === 'test') {
      console.log(memoryHelper.generateReport())
    }
    
    // Assert no significant memory leaks
    expect(memoryHelper.checkForLeaks(5)).toBe(false)
  })

  it('should not leak memory during streaming', async () => {
    const { result } = renderHook(() => useOptimizedStreaming())
    
    memoryHelper.recordMeasurement('initial')
    
    // Simulate heavy streaming
    for (let i = 0; i < 1000; i++) {
      act(() => {
        result.current.addToStream(`Chunk ${i} `)
      })
    }
    
    memoryHelper.recordMeasurement('after streaming')
    
    // Cleanup
    act(() => {
      result.current.clearStream()
    })
    
    // Force garbage collection if available
    if (global.gc) global.gc()
    
    memoryHelper.recordMeasurement('after cleanup')
    
    // Memory should return to reasonable levels
    const growthAfterCleanup = memoryHelper.getMemoryGrowth()
    expect(growthAfterCleanup).toBeLessThan(1024 * 1024) // Less than 1MB growth
  })
})
```

## 🎯 **Key Testing Strategies**

1. **Test streaming behavior with mocks** - Mock EventSource and WebSocket connections
2. **Use memory testing utilities** - Detect memory leaks in long-running tests
3. **Test error states thoroughly** - Network failures, timeouts, and edge cases
4. **Integration test multi-protocol flows** - Verify agent routing works correctly
5. **Performance test large datasets** - Ensure virtualization works under load
6. **E2E test complete user journeys** - Real browser testing with Playwright
7. **Mock external dependencies** - Don't test third-party services directly

---

**Next**: [06-deployment-patterns.md](./06-deployment-patterns.md) - Production Deployment Strategies

**Previous**: [04-performance-optimization-strategies.md](./04-performance-optimization-strategies.md)