# Architecture 4: Performance Optimization Strategies - Production Performance Patterns

## 🎯 **Learning Objectives**

By the end of this tutorial, you will understand:
- Performance optimization strategies for streaming React applications
- Memory management patterns for long-running conversations
- Rendering optimization techniques for large datasets
- Network optimization for real-time communication
- Profiling and monitoring performance bottlenecks
- Progressive loading and code splitting strategies

## ⚡ **The Performance Challenge**

Production React applications face unique performance challenges:
- **Streaming Data**: High-frequency updates can overwhelm the UI thread
- **Memory Growth**: Long conversations consume increasing memory
- **Large Datasets**: Thousands of messages need efficient rendering
- **Network Latency**: Real-time features require optimized connections
- **Bundle Size**: Growing features increase initial load time
- **Mobile Performance**: Lower-powered devices need special consideration

**Our goal**: Build **production-grade performance optimizations** that scale to enterprise-level usage.

## 🏎️ **Performance Architecture Overview**

### **Performance Layer Strategy**

```
┌─────────────────────────────────────────────┐
│          Performance Monitoring             │ ← Metrics & alerts
├─────────────────────────────────────────────┤
│         Rendering Optimization              │ ← Virtual scrolling, memoization  
├─────────────────────────────────────────────┤
│          Memory Management                  │ ← Cleanup, weak references
├─────────────────────────────────────────────┤
│         Network Optimization                │ ← Compression, caching, streaming
├─────────────────────────────────────────────┤
│          Code Splitting                     │ ← Dynamic imports, lazy loading
└─────────────────────────────────────────────┘
```

## 🧠 **Memory Management Strategies**

### **Pattern 1: Conversation Memory Manager**

**Problem**: Long conversations with thousands of messages consume excessive memory and slow down rendering.

**Solution**: Intelligent memory management with pagination and cleanup.

```typescript
// src/services/conversationMemoryManager.ts
interface MemoryConfig {
  maxMessagesInMemory: number
  maxConversationsInMemory: number
  cleanupInterval: number
  memoryThresholdMB: number
  enablePerformanceMonitoring: boolean
}

interface MemoryStats {
  totalMessages: number
  activeConversations: number
  estimatedMemoryUsage: number
  lastCleanup: Date
  cleanupCount: number
}

interface ConversationWindow {
  conversationId: string
  visibleMessages: StoredMessage[]
  totalMessageCount: number
  startIndex: number
  endIndex: number
  lastAccessed: Date
}

export class ConversationMemoryManager {
  private config: MemoryConfig
  private conversationWindows = new Map<string, ConversationWindow>()
  private cleanupTimer?: NodeJS.Timeout
  private performanceObserver?: PerformanceObserver
  private memoryStats: MemoryStats

  constructor(config: Partial<MemoryConfig> = {}) {
    this.config = {
      maxMessagesInMemory: 1000,
      maxConversationsInMemory: 10,
      cleanupInterval: 30000, // 30 seconds
      memoryThresholdMB: 100,
      enablePerformanceMonitoring: true,
      ...config
    }

    this.memoryStats = {
      totalMessages: 0,
      activeConversations: 0,
      estimatedMemoryUsage: 0,
      lastCleanup: new Date(),
      cleanupCount: 0,
    }

    this.setupCleanupTimer()
    
    if (this.config.enablePerformanceMonitoring) {
      this.setupPerformanceMonitoring()
    }
  }

  /**
   * Get messages for conversation with memory management
   */
  async getConversationWindow(
    conversationId: string,
    startIndex: number = 0,
    windowSize: number = 50
  ): Promise<ConversationWindow> {
    let window = this.conversationWindows.get(conversationId)
    
    if (!window || !this.isWindowValid(window, startIndex, windowSize)) {
      window = await this.loadConversationWindow(conversationId, startIndex, windowSize)
    }

    // Update access time
    window.lastAccessed = new Date()
    
    return window
  }

  private async loadConversationWindow(
    conversationId: string,
    startIndex: number,
    windowSize: number
  ): Promise<ConversationWindow> {
    // Load messages from storage with pagination
    const messages = await messageStorage.loadMessages(conversationId, {
      offset: startIndex,
      limit: windowSize,
    })

    // Get total count for pagination
    const totalCount = await messageStorage.getMessageCount(conversationId)

    const window: ConversationWindow = {
      conversationId,
      visibleMessages: messages,
      totalMessageCount: totalCount,
      startIndex,
      endIndex: startIndex + messages.length - 1,
      lastAccessed: new Date(),
    }

    // Store window and trigger cleanup if needed
    this.conversationWindows.set(conversationId, window)
    this.updateMemoryStats()
    
    if (this.shouldCleanup()) {
      await this.performCleanup()
    }

    return window
  }

  private isWindowValid(
    window: ConversationWindow,
    requestedStart: number,
    requestedSize: number
  ): boolean {
    // Check if requested range is within the current window
    const requestedEnd = requestedStart + requestedSize - 1
    
    return (
      requestedStart >= window.startIndex &&
      requestedEnd <= window.endIndex &&
      window.visibleMessages.length > 0
    )
  }

  /**
   * Add new message with memory management
   */
  async addMessage(conversationId: string, message: StoredMessage): Promise<void> {
    const window = this.conversationWindows.get(conversationId)
    
    if (window) {
      // Add to window if it's at the end
      if (window.endIndex === window.totalMessageCount - 1) {
        window.visibleMessages.push(message)
        window.endIndex++
        window.totalMessageCount++
        
        // Trim window if too large
        if (window.visibleMessages.length > this.config.maxMessagesInMemory) {
          const trimAmount = Math.floor(this.config.maxMessagesInMemory * 0.2) // Remove 20%
          window.visibleMessages.splice(0, trimAmount)
          window.startIndex += trimAmount
        }
      } else {
        // Message added in middle, invalidate window
        this.conversationWindows.delete(conversationId)
      }
    }

    this.updateMemoryStats()
  }

  /**
   * Cleanup old conversations and messages
   */
  private async performCleanup(): Promise<void> {
    const now = new Date()
    const conversationsToRemove: string[] = []
    const windows = Array.from(this.conversationWindows.entries())
    
    // Sort by last accessed (oldest first)
    windows.sort(([,a], [,b]) => a.lastAccessed.getTime() - b.lastAccessed.getTime())

    // Remove excess conversations
    const excessConversations = Math.max(0, windows.length - this.config.maxConversationsInMemory)
    for (let i = 0; i < excessConversations; i++) {
      conversationsToRemove.push(windows[i][0])
    }

    // Remove conversations that haven't been accessed recently (older than 5 minutes)
    const staleThreshold = now.getTime() - (5 * 60 * 1000)
    for (const [conversationId, window] of windows) {
      if (window.lastAccessed.getTime() < staleThreshold) {
        conversationsToRemove.push(conversationId)
      }
    }

    // Perform cleanup
    for (const conversationId of conversationsToRemove) {
      this.conversationWindows.delete(conversationId)
    }

    // Force garbage collection hint (if available)
    if (window.gc && typeof window.gc === 'function') {
      window.gc()
    }

    this.memoryStats.lastCleanup = now
    this.memoryStats.cleanupCount++
    this.updateMemoryStats()

    console.log(`Memory cleanup completed. Removed ${conversationsToRemove.length} conversations.`, {
      stats: this.memoryStats,
      removedConversations: conversationsToRemove,
    })
  }

  private shouldCleanup(): boolean {
    const memoryUsage = this.estimateMemoryUsage()
    const conversationCount = this.conversationWindows.size
    
    return (
      memoryUsage > this.config.memoryThresholdMB ||
      conversationCount > this.config.maxConversationsInMemory ||
      this.getTotalMessageCount() > this.config.maxMessagesInMemory * conversationCount
    )
  }

  private updateMemoryStats(): void {
    this.memoryStats.totalMessages = this.getTotalMessageCount()
    this.memoryStats.activeConversations = this.conversationWindows.size
    this.memoryStats.estimatedMemoryUsage = this.estimateMemoryUsage()
  }

  private getTotalMessageCount(): number {
    return Array.from(this.conversationWindows.values())
      .reduce((total, window) => total + window.visibleMessages.length, 0)
  }

  private estimateMemoryUsage(): number {
    let totalSize = 0
    
    for (const window of this.conversationWindows.values()) {
      for (const message of window.visibleMessages) {
        // Rough estimation: 1KB per message on average
        totalSize += JSON.stringify(message).length
      }
    }

    // Convert to MB
    return totalSize / (1024 * 1024)
  }

  private setupCleanupTimer(): void {
    this.cleanupTimer = setInterval(() => {
      if (this.shouldCleanup()) {
        this.performCleanup()
      }
    }, this.config.cleanupInterval)
  }

  private setupPerformanceMonitoring(): void {
    if (!window.PerformanceObserver) return

    this.performanceObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'measure' && entry.name.startsWith('conversation-')) {
          console.log(`Performance measure: ${entry.name} took ${entry.duration}ms`)
          
          // Alert on slow operations
          if (entry.duration > 100) {
            console.warn(`Slow operation detected: ${entry.name} (${entry.duration}ms)`)
          }
        }
      }
    })

    this.performanceObserver.observe({ entryTypes: ['measure', 'navigation', 'resource'] })
  }

  /**
   * Performance measurement utilities
   */
  startMeasure(name: string): void {
    if (performance.mark) {
      performance.mark(`${name}-start`)
    }
  }

  endMeasure(name: string): void {
    if (performance.mark && performance.measure) {
      performance.mark(`${name}-end`)
      performance.measure(name, `${name}-start`, `${name}-end`)
    }
  }

  getMemoryStats(): MemoryStats {
    return { ...this.memoryStats }
  }

  destroy(): void {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer)
    }
    
    if (this.performanceObserver) {
      this.performanceObserver.disconnect()
    }
    
    this.conversationWindows.clear()
  }
}

export const conversationMemory = new ConversationMemoryManager()
```

### **Pattern 2: Virtual Scrolling for Large Lists**

**Problem**: Rendering thousands of messages causes performance issues and memory bloat.

**Solution**: Virtual scrolling that only renders visible items.

```typescript
// src/components/VirtualizedMessageList.tsx
import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { FixedSizeList as List, VariableSizeList } from 'react-window'
import { AutoSizer } from 'react-virtualized-auto-sizer'
import { conversationMemory } from '../services/conversationMemoryManager'

interface VirtualizedMessageListProps {
  conversationId: string
  onLoadMore?: () => void
  className?: string
  itemHeight?: number // Fixed height mode
  estimatedItemHeight?: number // Variable height mode
}

interface MessageItemData {
  messages: StoredMessage[]
  conversationId: string
  onLoadMore?: () => void
  itemHeights: Map<number, number>
  setItemHeight: (index: number, height: number) => void
}

export const VirtualizedMessageList: React.FC<VirtualizedMessageListProps> = ({
  conversationId,
  onLoadMore,
  className = '',
  itemHeight,
  estimatedItemHeight = 100,
}) => {
  const [messages, setMessages] = useState<StoredMessage[]>([])
  const [totalMessageCount, setTotalMessageCount] = useState(0)
  const [isLoading, setIsLoading] = useState(false)
  const [hasMore, setHasMore] = useState(true)
  
  // For variable height virtualization
  const [itemHeights, setItemHeights] = useState(new Map<number, number>())
  const listRef = useRef<VariableSizeList | List>(null)
  const loadingRef = useRef(false)

  // Load initial messages
  useEffect(() => {
    loadMessages(0, 50)
  }, [conversationId])

  const loadMessages = useCallback(async (startIndex: number, count: number) => {
    if (loadingRef.current) return

    loadingRef.current = true
    setIsLoading(true)
    conversationMemory.startMeasure(`load-messages-${startIndex}`)

    try {
      const window = await conversationMemory.getConversationWindow(
        conversationId,
        startIndex,
        count
      )

      if (startIndex === 0) {
        // Initial load
        setMessages(window.visibleMessages)
      } else {
        // Append more messages
        setMessages(prev => [...prev, ...window.visibleMessages])
      }

      setTotalMessageCount(window.totalMessageCount)
      setHasMore(window.endIndex < window.totalMessageCount - 1)

    } catch (error) {
      console.error('Failed to load messages:', error)
    } finally {
      setIsLoading(false)
      loadingRef.current = false
      conversationMemory.endMeasure(`load-messages-${startIndex}`)
    }
  }, [conversationId])

  // Handle infinite scrolling
  const handleItemsRendered = useCallback(({ visibleStartIndex, visibleStopIndex }) => {
    const totalVisible = visibleStopIndex - visibleStartIndex + 1
    const remainingItems = messages.length - visibleStopIndex
    
    // Load more when approaching end
    if (remainingItems < totalVisible && hasMore && !isLoading) {
      loadMessages(messages.length, 50)
      onLoadMore?.()
    }
  }, [messages.length, hasMore, isLoading, loadMessages, onLoadMore])

  // Variable height management
  const setItemHeight = useCallback((index: number, height: number) => {
    setItemHeights(prev => {
      const newHeights = new Map(prev)
      newHeights.set(index, height)
      return newHeights
    })
    
    // Reset cache for this item
    if (listRef.current && 'resetAfterIndex' in listRef.current) {
      listRef.current.resetAfterIndex(index)
    }
  }, [])

  const getItemHeight = useCallback((index: number) => {
    return itemHeights.get(index) ?? estimatedItemHeight
  }, [itemHeights, estimatedItemHeight])

  // Memoized item data
  const itemData: MessageItemData = useMemo(() => ({
    messages,
    conversationId,
    onLoadMore,
    itemHeights,
    setItemHeight,
  }), [messages, conversationId, onLoadMore, itemHeights, setItemHeight])

  if (messages.length === 0 && !isLoading) {
    return (
      <div className={`flex items-center justify-center h-64 text-gray-500 ${className}`}>
        No messages yet
      </div>
    )
  }

  return (
    <div className={`virtualized-message-list ${className}`}>
      <AutoSizer>
        {({ height, width }) => (
          itemHeight ? (
            // Fixed height virtualization
            <List
              ref={listRef as React.RefObject<List>}
              height={height}
              width={width}
              itemCount={messages.length}
              itemSize={itemHeight}
              itemData={itemData}
              onItemsRendered={handleItemsRendered}
              overscanCount={5}
            >
              {MessageItemRenderer}
            </List>
          ) : (
            // Variable height virtualization
            <VariableSizeList
              ref={listRef as React.RefObject<VariableSizeList>}
              height={height}
              width={width}
              itemCount={messages.length}
              itemSize={getItemHeight}
              itemData={itemData}
              onItemsRendered={handleItemsRendered}
              overscanCount={5}
              estimatedItemSize={estimatedItemHeight}
            >
              {VariableMessageItemRenderer}
            </VariableSizeList>
          )
        )}
      </AutoSizer>
      
      {isLoading && (
        <div className="flex items-center justify-center p-4">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Loading messages...</span>
        </div>
      )}
    </div>
  )
}

// Fixed height message renderer
const MessageItemRenderer: React.FC<{
  index: number
  style: React.CSSProperties
  data: MessageItemData
}> = ({ index, style, data }) => {
  const message = data.messages[index]
  
  if (!message) {
    return <div style={style} />
  }

  return (
    <div style={style}>
      <MessageComponent message={message} />
    </div>
  )
}

// Variable height message renderer with height measurement
const VariableMessageItemRenderer: React.FC<{
  index: number
  style: React.CSSProperties
  data: MessageItemData
}> = ({ index, style, data }) => {
  const message = data.messages[index]
  const rowRef = useRef<HTMLDivElement>(null)
  const { setItemHeight } = data

  useEffect(() => {
    if (rowRef.current) {
      const height = rowRef.current.offsetHeight
      setItemHeight(index, height)
    }
  }, [index, setItemHeight, message])

  if (!message) {
    return <div style={style} />
  }

  return (
    <div ref={rowRef} style={style}>
      <MessageComponent message={message} />
    </div>
  )
}

// Optimized message component
const MessageComponent = React.memo<{ message: StoredMessage }>(({ message }) => {
  return (
    <div className="message-item p-4 border-b border-gray-100">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
          <span className="text-sm font-medium text-blue-600">
            {message.role === 'user' ? 'U' : 'A'}
          </span>
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-medium text-gray-900 capitalize">
              {message.role}
            </span>
            <span className="text-xs text-gray-500">
              {new Date(message.timestamp).toLocaleTimeString()}
            </span>
          </div>
          
          <div className="text-gray-700 whitespace-pre-wrap break-words">
            {message.content}
          </div>
          
          {message.metadata?.agent && (
            <div className="mt-2 text-xs text-gray-500">
              via {message.metadata.agent}
            </div>
          )}
        </div>
      </div>
    </div>
  )
})
```

## 🌊 **Streaming Performance Optimization**

### **Pattern 3: Optimized Streaming Renderer**

**Problem**: High-frequency streaming updates can block the UI thread and cause janky animations.

**Solution**: Throttled updates with efficient batching.

```typescript
// src/hooks/useOptimizedStreaming.ts
import { useRef, useCallback, useEffect, useState } from 'react'
import { throttle, debounce } from 'lodash'

interface StreamingConfig {
  throttleMs: number
  batchSize: number
  maxQueueSize: number
  enableRAF: boolean // Use requestAnimationFrame
  prioritizeLatestUpdates: boolean
}

interface StreamingStats {
  totalUpdates: number
  droppedUpdates: number
  averageLatency: number
  lastUpdateTime: number
  queueSize: number
}

export const useOptimizedStreaming = (config: Partial<StreamingConfig> = {}) => {
  const {
    throttleMs = 16, // ~60fps
    batchSize = 10,
    maxQueueSize = 100,
    enableRAF = true,
    prioritizeLatestUpdates = true
  } = config

  const [content, setContent] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [stats, setStats] = useState<StreamingStats>({
    totalUpdates: 0,
    droppedUpdates: 0,
    averageLatency: 0,
    lastUpdateTime: 0,
    queueSize: 0,
  })

  // Refs for performance
  const contentRef = useRef('')
  const updateQueueRef = useRef<Array<{ content: string; timestamp: number }>>([])
  const isProcessingRef = useRef(false)
  const rafIdRef = useRef<number>()
  const statsRef = useRef(stats)

  // Update stats ref
  useEffect(() => {
    statsRef.current = stats
  }, [stats])

  // Batch processing function
  const processBatch = useCallback(() => {
    if (isProcessingRef.current || updateQueueRef.current.length === 0) {
      return
    }

    isProcessingRef.current = true
    const startTime = performance.now()

    // Get batch of updates
    const batchSize = Math.min(config.batchSize || 10, updateQueueRef.current.length)
    const batch = updateQueueRef.current.splice(0, batchSize)
    
    if (batch.length === 0) {
      isProcessingRef.current = false
      return
    }

    // Process batch - either latest only or accumulated
    let newContent: string
    if (prioritizeLatestUpdates && batch.length > 1) {
      // Use only the latest update for better performance
      newContent = batch[batch.length - 1].content
    } else {
      // Accumulate all updates
      newContent = batch[batch.length - 1].content
    }

    // Update content
    contentRef.current = newContent
    setContent(newContent)

    // Update stats
    const processingTime = performance.now() - startTime
    const latency = startTime - (batch[0]?.timestamp || startTime)
    
    setStats(prev => ({
      ...prev,
      totalUpdates: prev.totalUpdates + batch.length,
      averageLatency: (prev.averageLatency * prev.totalUpdates + latency) / (prev.totalUpdates + 1),
      lastUpdateTime: Date.now(),
      queueSize: updateQueueRef.current.length,
    }))

    isProcessingRef.current = false

    // Schedule next batch if queue has items
    if (updateQueueRef.current.length > 0) {
      scheduleNextBatch()
    }
  }, [batchSize, prioritizeLatestUpdates])

  // Schedule batch processing
  const scheduleNextBatch = useCallback(() => {
    if (enableRAF && window.requestAnimationFrame) {
      rafIdRef.current = requestAnimationFrame(processBatch)
    } else {
      setTimeout(processBatch, 0)
    }
  }, [enableRAF, processBatch])

  // Throttled update function
  const throttledUpdate = useCallback(
    throttle(() => {
      if (!isProcessingRef.current && updateQueueRef.current.length > 0) {
        scheduleNextBatch()
      }
    }, throttleMs),
    [throttleMs, scheduleNextBatch]
  )

  // Add content to stream
  const addToStream = useCallback((chunk: string) => {
    const now = performance.now()
    
    // Manage queue size
    if (updateQueueRef.current.length >= maxQueueSize) {
      if (prioritizeLatestUpdates) {
        // Remove oldest updates
        const removeCount = Math.floor(maxQueueSize * 0.2) // Remove 20%
        updateQueueRef.current.splice(0, removeCount)
        
        setStats(prev => ({
          ...prev,
          droppedUpdates: prev.droppedUpdates + removeCount
        }))
      } else {
        // Drop this update
        setStats(prev => ({
          ...prev,
          droppedUpdates: prev.droppedUpdates + 1
        }))
        return
      }
    }

    // Add to queue
    const newContent = contentRef.current + chunk
    updateQueueRef.current.push({
      content: newContent,
      timestamp: now
    })

    // Trigger throttled update
    throttledUpdate()
  }, [maxQueueSize, prioritizeLatestUpdates, throttledUpdate])

  // Stream control functions
  const startStream = useCallback(() => {
    setIsStreaming(true)
    contentRef.current = ''
    setContent('')
    updateQueueRef.current = []
    
    setStats({
      totalUpdates: 0,
      droppedUpdates: 0,
      averageLatency: 0,
      lastUpdateTime: 0,
      queueSize: 0,
    })
  }, [])

  const endStream = useCallback(() => {
    setIsStreaming(false)
    
    // Process any remaining updates
    while (updateQueueRef.current.length > 0 && !isProcessingRef.current) {
      processBatch()
    }
  }, [processBatch])

  const clearStream = useCallback(() => {
    contentRef.current = ''
    setContent('')
    updateQueueRef.current = []
    
    if (rafIdRef.current) {
      cancelAnimationFrame(rafIdRef.current)
    }
  }, [])

  // Cleanup
  useEffect(() => {
    return () => {
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current)
      }
      throttledUpdate.cancel()
    }
  }, [throttledUpdate])

  return {
    content,
    isStreaming,
    addToStream,
    startStream,
    endStream,
    clearStream,
    stats,
    getCurrentContent: () => contentRef.current,
  }
}

// Hook for streaming with automatic performance optimization
export const usePerformantStreamingChat = () => {
  const streaming = useOptimizedStreaming({
    throttleMs: 16, // 60fps
    batchSize: 5,
    maxQueueSize: 50,
    enableRAF: true,
    prioritizeLatestUpdates: true,
  })

  const [renderStats, setRenderStats] = useState({
    frameDrops: 0,
    averageFPS: 60,
    lastFrameTime: performance.now(),
  })

  // Monitor frame rate
  useEffect(() => {
    let frameCount = 0
    let lastTime = performance.now()
    let animationId: number

    const measureFPS = () => {
      const now = performance.now()
      frameCount++
      
      if (now - lastTime >= 1000) { // Every second
        const fps = Math.round((frameCount * 1000) / (now - lastTime))
        
        setRenderStats(prev => ({
          frameDrops: fps < 50 ? prev.frameDrops + 1 : prev.frameDrops,
          averageFPS: fps,
          lastFrameTime: now,
        }))

        frameCount = 0
        lastTime = now
      }

      animationId = requestAnimationFrame(measureFPS)
    }

    if (streaming.isStreaming) {
      animationId = requestAnimationFrame(measureFPS)
    }

    return () => {
      if (animationId) {
        cancelAnimationFrame(animationId)
      }
    }
  }, [streaming.isStreaming])

  return {
    ...streaming,
    renderStats,
  }
}
```

## 📦 **Bundle Optimization Strategies**

### **Pattern 4: Advanced Code Splitting**

```typescript
// src/components/LazyComponents.tsx
import React, { lazy, Suspense } from 'react'
import { ErrorBoundary } from './ErrorBoundary'

// Lazy load heavy components
const AdvancedChatInterface = lazy(() => 
  import('./AdvancedChatInterface').then(module => ({
    default: module.AdvancedChatInterface
  }))
)

const ConversationAnalytics = lazy(() => 
  import('./ConversationAnalytics').then(module => ({
    default: module.ConversationAnalytics
  }))
)

const MessageExporter = lazy(() => 
  import('./MessageExporter').then(module => ({
    default: module.MessageExporter
  }))
)

// Component with intelligent preloading
export const ChatContainer: React.FC = () => {
  const [activeFeature, setActiveFeature] = useState<string>('chat')
  
  // Preload components based on user behavior
  useEffect(() => {
    const preloadTimer = setTimeout(() => {
      // Preload likely-to-be-used components
      import('./ConversationAnalytics')
      import('./MessageExporter')
    }, 2000) // Preload after 2 seconds

    return () => clearTimeout(preloadTimer)
  }, [])

  return (
    <div className="chat-container">
      <ErrorBoundary>
        <Suspense fallback={<ComponentLoadingSkeleton />}>
          {activeFeature === 'chat' && <AdvancedChatInterface />}
          {activeFeature === 'analytics' && <ConversationAnalytics />}
          {activeFeature === 'export' && <MessageExporter />}
        </Suspense>
      </ErrorBoundary>
    </div>
  )
}

// Optimized loading skeleton
const ComponentLoadingSkeleton: React.FC = () => (
  <div className="animate-pulse">
    <div className="h-8 bg-gray-200 rounded mb-4"></div>
    <div className="space-y-3">
      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      <div className="h-4 bg-gray-200 rounded w-5/6"></div>
    </div>
  </div>
)
```

## 🎯 **Usage Examples**

### **Complete Performance Integration**

```typescript
// High-performance chat component
export const PerformantChatInterface: React.FC = () => {
  const { content, addToStream, startStream, endStream, stats } = usePerformantStreamingChat()
  const [messages, setMessages] = useState<StoredMessage[]>([])
  
  // Performance monitoring
  useEffect(() => {
    if (stats.droppedUpdates > 10) {
      console.warn('High number of dropped updates:', stats)
    }
    
    if (stats.averageLatency > 100) {
      console.warn('High streaming latency:', stats.averageLatency)
    }
  }, [stats])

  return (
    <div className="performant-chat h-screen flex flex-col">
      <div className="flex-1 overflow-hidden">
        <VirtualizedMessageList
          conversationId={conversationId}
          estimatedItemHeight={120}
          onLoadMore={() => console.log('Load more messages')}
        />
      </div>
      
      <div className="border-t bg-white p-4">
        <ChatInput onSendMessage={handleSendMessage} />
        
        {/* Performance stats (development only) */}
        {process.env.NODE_ENV === 'development' && (
          <div className="mt-2 text-xs text-gray-500">
            Updates: {stats.totalUpdates} | 
            Dropped: {stats.droppedUpdates} |
            Latency: {stats.averageLatency.toFixed(1)}ms |
            Queue: {stats.queueSize}
          </div>
        )}
      </div>
    </div>
  )
}
```

## 🎯 **Key Takeaways**

1. **Memory management is crucial** - Long conversations need intelligent cleanup
2. **Virtual scrolling scales infinitely** - Only render what users can see  
3. **Streaming needs throttling** - Balance responsiveness with performance
4. **Bundle splitting improves load times** - Load features as needed
5. **Monitor performance continuously** - Track metrics and optimize bottlenecks
6. **Prioritize user experience** - 60fps rendering should be the goal
7. **Plan for mobile performance** - Lower-powered devices need special consideration

---

**Next**: [05-testing-strategies.md](./05-testing-strategies.md) - Comprehensive Testing Approaches

**Previous**: [03-component-composition-patterns.md](./03-component-composition-patterns.md)