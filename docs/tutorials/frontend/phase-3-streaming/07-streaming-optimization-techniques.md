# Phase 3.7: Streaming Optimization Techniques - Performance & Memory Management

## 🎯 **Learning Objectives**

By the end of this tutorial, you will:
- Optimize streaming performance for high-frequency chunk updates
- Implement efficient memory management for long-running streams
- Build throttling and debouncing mechanisms for UI updates
- Create buffer management systems that prevent memory leaks
- Handle browser compatibility issues and performance monitoring
- Implement advanced optimization patterns for production streaming

## ⚡ **The Performance Challenge**

Streaming applications face unique performance challenges:
- **High-frequency updates**: Hundreds of chunks per second
- **Memory accumulation**: Large responses consume browser memory
- **UI blocking**: Too many DOM updates can freeze the interface
- **Browser limits**: EventSource connections and memory constraints
- **Mobile performance**: Limited resources and slower networks
- **Concurrent streams**: Multiple simultaneous streaming conversations

**Our goal**: Build **high-performance streaming** that scales to production workloads.

## 🚀 **Performance Optimization Architecture**

### **Step 1: Buffer Management System**

```typescript
// src/services/streamingBufferManager.ts
interface BufferConfig {
  maxBufferSize: number        // Maximum chunks to keep in memory
  flushThreshold: number       // Chunks before forced flush
  flushInterval: number        // Time-based flush interval (ms)
  compressionEnabled: boolean  // Enable content compression
  persistOldChunks: boolean    // Keep old chunks in IndexedDB
}

export class StreamingBufferManager {
  private config: BufferConfig
  private activeBuffers = new Map<string, ChunkBuffer>()
  private compressionWorker?: Worker

  constructor(config: Partial<BufferConfig> = {}) {
    this.config = {
      maxBufferSize: 1000,
      flushThreshold: 50,
      flushInterval: 1000,
      compressionEnabled: true,
      persistOldChunks: false,
      ...config
    }

    if (this.config.compressionEnabled) {
      this.initializeCompressionWorker()
    }
  }

  /**
   * Create a new buffer for a stream
   */
  createBuffer(streamId: string): ChunkBuffer {
    const buffer = new ChunkBuffer(streamId, {
      maxSize: this.config.maxBufferSize,
      flushThreshold: this.config.flushThreshold,
      flushInterval: this.config.flushInterval,
      onFlush: this.handleBufferFlush.bind(this),
      onMemoryPressure: this.handleMemoryPressure.bind(this),
    })

    this.activeBuffers.set(streamId, buffer)
    return buffer
  }

  /**
   * Add chunk to buffer with automatic optimization
   */
  addChunk(streamId: string, chunk: string): void {
    const buffer = this.activeBuffers.get(streamId)
    if (!buffer) {
      throw new Error(`Buffer not found for stream: ${streamId}`)
    }

    buffer.addChunk({
      id: `${streamId}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      content: chunk,
      timestamp: new Date(),
      size: new Blob([chunk]).size,
    })
  }

  /**
   * Get optimized content for display
   */
  getDisplayContent(streamId: string): string {
    const buffer = this.activeBuffers.get(streamId)
    if (!buffer) return ''

    return buffer.getCombinedContent()
  }

  /**
   * Clean up buffer and free memory
   */
  destroyBuffer(streamId: string): void {
    const buffer = this.activeBuffers.get(streamId)
    if (buffer) {
      buffer.destroy()
      this.activeBuffers.delete(streamId)
    }
  }

  private async handleBufferFlush(buffer: ChunkBuffer): Promise<void> {
    if (this.config.persistOldChunks) {
      await this.persistChunksToIndexedDB(buffer.getOldChunks())
    }

    if (this.config.compressionEnabled && this.compressionWorker) {
      await this.compressOldChunks(buffer)
    }
  }

  private handleMemoryPressure(buffer: ChunkBuffer): void {
    console.warn('Memory pressure detected, forcing buffer cleanup')
    
    // Aggressive cleanup
    buffer.forceCleanup()
    
    // Trigger garbage collection if available
    if ('gc' in window && typeof window.gc === 'function') {
      window.gc()
    }
  }

  private initializeCompressionWorker(): void {
    if (typeof Worker !== 'undefined') {
      this.compressionWorker = new Worker(
        new URL('../workers/compressionWorker.ts', import.meta.url),
        { type: 'module' }
      )
    }
  }

  private async compressOldChunks(buffer: ChunkBuffer): Promise<void> {
    if (!this.compressionWorker) return

    const oldChunks = buffer.getOldChunks()
    if (oldChunks.length === 0) return

    return new Promise((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        reject(new Error('Compression timeout'))
      }, 5000)

      this.compressionWorker!.postMessage({
        type: 'compress',
        chunks: oldChunks,
      })

      this.compressionWorker!.onmessage = (event) => {
        clearTimeout(timeoutId)
        if (event.data.type === 'compressed') {
          buffer.replaceOldChunks(event.data.compressedContent)
          resolve()
        } else if (event.data.type === 'error') {
          reject(new Error(event.data.error))
        }
      }
    })
  }

  private async persistChunksToIndexedDB(chunks: StreamChunk[]): Promise<void> {
    // IndexedDB implementation for chunk persistence
    // This would store old chunks for later retrieval if needed
    try {
      const db = await this.openIndexedDB()
      const transaction = db.transaction(['chunks'], 'readwrite')
      const store = transaction.objectStore('chunks')

      for (const chunk of chunks) {
        await store.put(chunk)
      }
    } catch (error) {
      console.warn('Failed to persist chunks to IndexedDB:', error)
    }
  }

  private openIndexedDB(): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('StreamingChunks', 1)
      
      request.onerror = () => reject(request.error)
      request.onsuccess = () => resolve(request.result)
      
      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result
        if (!db.objectStoreNames.contains('chunks')) {
          const store = db.createObjectStore('chunks', { keyPath: 'id' })
          store.createIndex('timestamp', 'timestamp')
          store.createIndex('streamId', 'streamId')
        }
      }
    })
  }
}

interface StreamChunk {
  id: string
  content: string
  timestamp: Date
  size: number
  compressed?: boolean
}

class ChunkBuffer {
  private chunks: StreamChunk[] = []
  private combinedContent = ''
  private lastFlush = Date.now()
  private flushTimer?: number
  private config: BufferConfig
  private onFlush: (buffer: ChunkBuffer) => Promise<void>
  private onMemoryPressure: (buffer: ChunkBuffer) => void

  constructor(
    public streamId: string,
    config: {
      maxSize: number
      flushThreshold: number
      flushInterval: number
      onFlush: (buffer: ChunkBuffer) => Promise<void>
      onMemoryPressure: (buffer: ChunkBuffer) => void
    }
  ) {
    this.config = config as any
    this.onFlush = config.onFlush
    this.onMemoryPressure = config.onMemoryPressure

    this.startFlushTimer()
  }

  addChunk(chunk: StreamChunk): void {
    this.chunks.push(chunk)
    this.combinedContent += chunk.content

    // Check for flush conditions
    if (this.chunks.length >= this.config.flushThreshold) {
      this.flush()
    }

    // Monitor memory usage
    this.checkMemoryPressure()
  }

  getCombinedContent(): string {
    return this.combinedContent
  }

  getOldChunks(): StreamChunk[] {
    if (this.chunks.length <= this.config.maxSize) return []
    
    const oldChunks = this.chunks.slice(0, this.chunks.length - this.config.maxSize)
    return oldChunks
  }

  replaceOldChunks(compressedContent: string): void {
    const keepCount = this.config.maxSize
    const oldChunks = this.chunks.slice(0, this.chunks.length - keepCount)
    const recentChunks = this.chunks.slice(-keepCount)

    // Create a compressed chunk to replace old ones
    const compressedChunk: StreamChunk = {
      id: `${this.streamId}-compressed-${Date.now()}`,
      content: compressedContent,
      timestamp: oldChunks[0]?.timestamp || new Date(),
      size: new Blob([compressedContent]).size,
      compressed: true,
    }

    this.chunks = [compressedChunk, ...recentChunks]
    this.combinedContent = this.chunks.map(c => c.content).join('')
  }

  forceCleanup(): void {
    // Keep only the most recent chunks
    const keepCount = Math.floor(this.config.maxSize / 2)
    this.chunks = this.chunks.slice(-keepCount)
    this.combinedContent = this.chunks.map(c => c.content).join('')
  }

  destroy(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer)
    }
    this.chunks = []
    this.combinedContent = ''
  }

  private async flush(): Promise<void> {
    if (this.onFlush) {
      try {
        await this.onFlush(this)
      } catch (error) {
        console.error('Buffer flush error:', error)
      }
    }
    this.lastFlush = Date.now()
  }

  private startFlushTimer(): void {
    this.flushTimer = window.setInterval(() => {
      const timeSinceFlush = Date.now() - this.lastFlush
      if (timeSinceFlush >= this.config.flushInterval && this.chunks.length > 0) {
        this.flush()
      }
    }, this.config.flushInterval)
  }

  private checkMemoryPressure(): void {
    // Check if we're using too much memory
    const totalSize = this.chunks.reduce((sum, chunk) => sum + chunk.size, 0)
    const maxMemory = 50 * 1024 * 1024 // 50MB threshold

    if (totalSize > maxMemory) {
      this.onMemoryPressure(this)
    }
  }
}
```

### **Step 2: UI Update Throttling System**

```typescript
// src/services/uiUpdateThrottler.ts
interface ThrottleConfig {
  maxUpdatesPerSecond: number
  batchSize: number
  enableSmartThrottling: boolean
  priorityMode: 'latest' | 'batch' | 'smart'
}

export class UIUpdateThrottler {
  private config: ThrottleConfig
  private updateQueues = new Map<string, QueuedUpdate[]>()
  private processingTimers = new Map<string, number>()
  private lastUpdateTimes = new Map<string, number>()
  private performanceMonitor: PerformanceMonitor

  constructor(config: Partial<ThrottleConfig> = {}) {
    this.config = {
      maxUpdatesPerSecond: 30, // 30 FPS
      batchSize: 10,
      enableSmartThrottling: true,
      priorityMode: 'smart',
      ...config
    }

    this.performanceMonitor = new PerformanceMonitor()
  }

  /**
   * Queue a UI update with throttling
   */
  queueUpdate(
    componentId: string,
    updateFunction: () => void,
    priority: 'high' | 'medium' | 'low' = 'medium'
  ): void {
    const update: QueuedUpdate = {
      id: `${componentId}-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`,
      componentId,
      updateFunction,
      priority,
      timestamp: Date.now(),
    }

    if (!this.updateQueues.has(componentId)) {
      this.updateQueues.set(componentId, [])
    }

    const queue = this.updateQueues.get(componentId)!
    
    if (this.config.priorityMode === 'latest') {
      // Replace queue with only the latest update
      queue.length = 0
      queue.push(update)
    } else {
      queue.push(update)
    }

    this.scheduleProcessing(componentId)
  }

  /**
   * Process queued updates with smart batching
   */
  private scheduleProcessing(componentId: string): void {
    if (this.processingTimers.has(componentId)) {
      return // Already scheduled
    }

    const updateInterval = 1000 / this.config.maxUpdatesPerSecond
    const lastUpdate = this.lastUpdateTimes.get(componentId) || 0
    const timeSinceLastUpdate = Date.now() - lastUpdate
    
    let delay = Math.max(0, updateInterval - timeSinceLastUpdate)

    // Smart throttling based on performance
    if (this.config.enableSmartThrottling) {
      const performanceScore = this.performanceMonitor.getCurrentScore()
      if (performanceScore < 0.7) {
        // Poor performance, increase delay
        delay *= 2
      } else if (performanceScore > 0.9) {
        // Good performance, allow faster updates
        delay *= 0.5
      }
    }

    const timerId = window.setTimeout(() => {
      this.processUpdates(componentId)
    }, delay)

    this.processingTimers.set(componentId, timerId)
  }

  private processUpdates(componentId: string): void {
    const queue = this.updateQueues.get(componentId)
    if (!queue || queue.length === 0) {
      this.processingTimers.delete(componentId)
      return
    }

    const startTime = performance.now()

    try {
      let processed = 0
      const maxBatch = this.config.batchSize

      while (queue.length > 0 && processed < maxBatch) {
        const update = this.selectNextUpdate(queue)
        if (!update) break

        // Execute the update
        this.executeUpdate(update)
        processed++

        // Check if we're taking too long
        const elapsed = performance.now() - startTime
        if (elapsed > 16) { // 16ms = 60fps budget
          break
        }
      }

      this.lastUpdateTimes.set(componentId, Date.now())
      this.performanceMonitor.recordUpdatePerformance(componentId, performance.now() - startTime, processed)

    } catch (error) {
      console.error('Update processing error:', error)
    } finally {
      this.processingTimers.delete(componentId)
      
      // Schedule next batch if there are remaining updates
      if (queue.length > 0) {
        this.scheduleProcessing(componentId)
      }
    }
  }

  private selectNextUpdate(queue: QueuedUpdate[]): QueuedUpdate | null {
    if (queue.length === 0) return null

    switch (this.config.priorityMode) {
      case 'latest':
        return queue.pop() || null
      
      case 'batch':
        return queue.shift() || null
      
      case 'smart':
        // Prioritize high-priority updates, but don't starve others
        const highPriority = queue.find(u => u.priority === 'high')
        if (highPriority) {
          const index = queue.indexOf(highPriority)
          return queue.splice(index, 1)[0]
        }
        return queue.shift() || null
      
      default:
        return queue.shift() || null
    }
  }

  private executeUpdate(update: QueuedUpdate): void {
    try {
      update.updateFunction()
    } catch (error) {
      console.error(`Update execution failed for ${update.componentId}:`, error)
    }
  }

  /**
   * Clear all queued updates for a component
   */
  clearUpdates(componentId: string): void {
    this.updateQueues.delete(componentId)
    
    const timerId = this.processingTimers.get(componentId)
    if (timerId) {
      clearTimeout(timerId)
      this.processingTimers.delete(componentId)
    }
  }

  /**
   * Get throttling statistics
   */
  getStats(): ThrottleStats {
    let totalQueued = 0
    let totalComponents = 0

    for (const queue of this.updateQueues.values()) {
      totalQueued += queue.length
      totalComponents++
    }

    return {
      totalQueued,
      totalComponents,
      avgPerformanceScore: this.performanceMonitor.getAverageScore(),
      processingComponents: this.processingTimers.size,
    }
  }
}

interface QueuedUpdate {
  id: string
  componentId: string
  updateFunction: () => void
  priority: 'high' | 'medium' | 'low'
  timestamp: number
}

interface ThrottleStats {
  totalQueued: number
  totalComponents: number
  avgPerformanceScore: number
  processingComponents: number
}

class PerformanceMonitor {
  private scores: number[] = []
  private componentPerformance = new Map<string, number[]>()

  getCurrentScore(): number {
    // Simple performance score based on frame timing
    if ('memory' in performance) {
      const memory = (performance as any).memory
      const memoryUsage = memory.usedJSHeapSize / memory.jsHeapSizeLimit
      return Math.max(0, 1 - memoryUsage)
    }
    
    // Fallback to frame timing
    return this.scores.length > 0 ? this.scores[this.scores.length - 1] : 1
  }

  recordUpdatePerformance(componentId: string, duration: number, updatesProcessed: number): void {
    const score = Math.max(0, 1 - (duration / 16)) // 16ms budget for 60fps
    
    this.scores.push(score)
    if (this.scores.length > 100) {
      this.scores.shift()
    }

    if (!this.componentPerformance.has(componentId)) {
      this.componentPerformance.set(componentId, [])
    }

    const componentScores = this.componentPerformance.get(componentId)!
    componentScores.push(score)
    if (componentScores.length > 50) {
      componentScores.shift()
    }
  }

  getAverageScore(): number {
    if (this.scores.length === 0) return 1
    return this.scores.reduce((sum, score) => sum + score, 0) / this.scores.length
  }
}

export const uiUpdateThrottler = new UIUpdateThrottler()
```

### **Step 3: Optimized Streaming Hook**

```typescript
// src/hooks/useOptimizedStreaming.ts
import { useRef, useState, useCallback, useEffect } from 'react'
import { StreamingBufferManager } from '../services/streamingBufferManager'
import { uiUpdateThrottler } from '../services/uiUpdateThrottler'

interface OptimizedStreamingConfig {
  enableBuffering: boolean
  enableThrottling: boolean
  maxConcurrentStreams: number
  memoryLimitMB: number
}

export const useOptimizedStreaming = (config: Partial<OptimizedStreamingConfig> = {}) => {
  const finalConfig: OptimizedStreamingConfig = {
    enableBuffering: true,
    enableThrottling: true,
    maxConcurrentStreams: 3,
    memoryLimitMB: 100,
    ...config
  }

  const [displayContent, setDisplayContent] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const streamIdRef = useRef<string>()
  const bufferManagerRef = useRef<StreamingBufferManager>()
  const componentIdRef = useRef(`streaming-${Math.random().toString(36).substr(2, 9)}`)

  // Initialize buffer manager
  useEffect(() => {
    if (finalConfig.enableBuffering) {
      bufferManagerRef.current = new StreamingBufferManager({
        maxBufferSize: finalConfig.memoryLimitMB * 10, // Rough estimate
        compressionEnabled: true,
        persistOldChunks: false,
      })
    }

    return () => {
      if (bufferManagerRef.current && streamIdRef.current) {
        bufferManagerRef.current.destroyBuffer(streamIdRef.current)
      }
    }
  }, [finalConfig.enableBuffering, finalConfig.memoryLimitMB])

  const updateDisplay = useCallback((content: string) => {
    if (finalConfig.enableThrottling) {
      uiUpdateThrottler.queueUpdate(
        componentIdRef.current,
        () => setDisplayContent(content),
        'medium'
      )
    } else {
      setDisplayContent(content)
    }
  }, [finalConfig.enableThrottling])

  const startOptimizedStream = useCallback(async (
    query: string,
    streamFunction: (query: string, callbacks: any) => Promise<any>
  ) => {
    // Clean up previous stream
    if (streamIdRef.current && bufferManagerRef.current) {
      bufferManagerRef.current.destroyBuffer(streamIdRef.current)
    }

    streamIdRef.current = `stream-${Date.now()}`
    setIsStreaming(true)
    setError(null)
    setDisplayContent('')

    // Create new buffer if buffering is enabled
    let buffer: any = null
    if (finalConfig.enableBuffering && bufferManagerRef.current) {
      buffer = bufferManagerRef.current.createBuffer(streamIdRef.current)
    }

    let accumulatedContent = ''

    try {
      await streamFunction(query, {
        onData: (chunk: string) => {
          if (buffer) {
            // Use buffer for optimized memory management
            bufferManagerRef.current!.addChunk(streamIdRef.current!, chunk)
            const content = bufferManagerRef.current!.getDisplayContent(streamIdRef.current!)
            updateDisplay(content)
          } else {
            // Direct accumulation
            accumulatedContent += chunk
            updateDisplay(accumulatedContent)
          }
        },

        onComplete: (response: any) => {
          setIsStreaming(false)
        },

        onError: (error: Error) => {
          setError(error)
          setIsStreaming(false)
        }
      })
    } catch (error) {
      setError(error as Error)
      setIsStreaming(false)
    }
  }, [finalConfig, updateDisplay])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (streamIdRef.current && bufferManagerRef.current) {
        bufferManagerRef.current.destroyBuffer(streamIdRef.current)
      }
      uiUpdateThrottler.clearUpdates(componentIdRef.current)
    }
  }, [])

  return {
    displayContent,
    isStreaming,
    error,
    startOptimizedStream,
    getPerformanceStats: () => uiUpdateThrottler.getStats(),
  }
}
```

### **Step 4: Memory-Efficient Display Component**

```typescript
// src/components/OptimizedStreamingDisplay.tsx
import React, { memo, useMemo, useRef, useEffect } from 'react'
import { FixedSizeList as VirtualList } from 'react-window'

interface OptimizedStreamingDisplayProps {
  content: string
  isStreaming: boolean
  maxVisibleLines?: number
  enableVirtualization?: boolean
  className?: string
}

// Memoized component to prevent unnecessary re-renders
export const OptimizedStreamingDisplay = memo<OptimizedStreamingDisplayProps>(({
  content,
  isStreaming,
  maxVisibleLines = 1000,
  enableVirtualization = true,
  className = '',
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const shouldAutoScroll = useRef(true)

  // Split content into lines for efficient rendering
  const lines = useMemo(() => {
    const allLines = content.split('\n')
    
    // Limit lines to prevent memory issues
    if (allLines.length > maxVisibleLines) {
      return allLines.slice(-maxVisibleLines)
    }
    
    return allLines
  }, [content, maxVisibleLines])

  // Auto-scroll logic with performance optimization
  useEffect(() => {
    if (shouldAutoScroll.current && containerRef.current && isStreaming) {
      // Use requestAnimationFrame for smooth scrolling
      requestAnimationFrame(() => {
        if (containerRef.current) {
          containerRef.current.scrollTop = containerRef.current.scrollHeight
        }
      })
    }
  }, [content, isStreaming])

  // Check if user has scrolled up (disable auto-scroll)
  const handleScroll = () => {
    if (containerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = containerRef.current
      shouldAutoScroll.current = scrollTop + clientHeight >= scrollHeight - 10
    }
  }

  if (enableVirtualization && lines.length > 100) {
    return (
      <VirtualizedStreamingDisplay
        lines={lines}
        isStreaming={isStreaming}
        className={className}
      />
    )
  }

  return (
    <div
      ref={containerRef}
      className={`optimized-streaming-display overflow-auto h-64 ${className}`}
      onScroll={handleScroll}
    >
      <pre className="whitespace-pre-wrap font-mono text-sm">
        {content}
        {isStreaming && (
          <span className="inline-block w-2 h-4 bg-blue-500 animate-pulse ml-1" />
        )}
      </pre>
    </div>
  )
})

// Virtualized version for very large content
const VirtualizedStreamingDisplay: React.FC<{
  lines: string[]
  isStreaming: boolean
  className?: string
}> = memo(({ lines, isStreaming, className }) => {
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => (
    <div style={style} className="font-mono text-sm px-2">
      {lines[index]}
      {index === lines.length - 1 && isStreaming && (
        <span className="inline-block w-2 h-4 bg-blue-500 animate-pulse ml-1" />
      )}
    </div>
  )

  return (
    <div className={`virtualized-streaming-display ${className}`}>
      <VirtualList
        height={256} // 16rem
        itemCount={lines.length}
        itemSize={20}
        width="100%"
      >
        {Row}
      </VirtualList>
    </div>
  )
})
```

### **Step 5: Performance Monitoring Dashboard**

```typescript
// src/components/StreamingPerformanceMonitor.tsx
import React, { useState, useEffect } from 'react'
import { Activity, Zap, Database, Clock } from 'lucide-react'
import { uiUpdateThrottler } from '../services/uiUpdateThrottler'

export const StreamingPerformanceMonitor: React.FC<{ 
  show: boolean 
  className?: string 
}> = ({ show, className = '' }) => {
  const [stats, setStats] = useState<any>({})
  const [memoryInfo, setMemoryInfo] = useState<any>({})

  useEffect(() => {
    if (!show) return

    const interval = setInterval(() => {
      // Get throttling stats
      const throttleStats = uiUpdateThrottler.getStats()
      setStats(throttleStats)

      // Get memory info if available
      if ('memory' in performance) {
        const memory = (performance as any).memory
        setMemoryInfo({
          used: Math.round(memory.usedJSHeapSize / 1024 / 1024),
          total: Math.round(memory.totalJSHeapSize / 1024 / 1024),
          limit: Math.round(memory.jsHeapSizeLimit / 1024 / 1024),
        })
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [show])

  if (!show) return null

  return (
    <div className={`performance-monitor bg-gray-900 text-white p-3 rounded-lg text-xs ${className}`}>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-green-400" />
          <div>
            <div className="font-medium">Performance</div>
            <div>{Math.round((stats.avgPerformanceScore || 1) * 100)}%</div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-yellow-400" />
          <div>
            <div className="font-medium">Queue</div>
            <div>{stats.totalQueued || 0} updates</div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-blue-400" />
          <div>
            <div className="font-medium">Memory</div>
            <div>{memoryInfo.used || 0}MB</div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-purple-400" />
          <div>
            <div className="font-medium">Active</div>
            <div>{stats.processingComponents || 0} streams</div>
          </div>
        </div>
      </div>

      {memoryInfo.used && (
        <div className="mt-2">
          <div className="flex justify-between text-xs text-gray-400 mb-1">
            <span>Memory Usage</span>
            <span>{memoryInfo.used}MB / {memoryInfo.limit}MB</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-1.5">
            <div 
              className="bg-blue-500 h-1.5 rounded-full"
              style={{ width: `${(memoryInfo.used / memoryInfo.limit) * 100}%` }}
            />
          </div>
        </div>
      )}
    </div>
  )
}
```

## 🎯 **Usage Examples**

### **High-Performance Chat**
```typescript
const StreamingChatWithOptimizations: React.FC = () => {
  const { displayContent, isStreaming, startOptimizedStream, getPerformanceStats } = useOptimizedStreaming({
    enableBuffering: true,
    enableThrottling: true,
    memoryLimitMB: 50,
  })

  const [showMonitor, setShowMonitor] = useState(false)

  return (
    <div className="streaming-chat">
      <StreamingPerformanceMonitor show={showMonitor} />
      
      <OptimizedStreamingDisplay
        content={displayContent}
        isStreaming={isStreaming}
        enableVirtualization={true}
        maxVisibleLines={500}
      />
    </div>
  )
}
```

## 🎯 **Key Takeaways**

1. **Buffer management prevents memory leaks** - Clean up old content proactively
2. **UI throttling maintains smooth performance** - Don't update faster than 60fps
3. **Virtual scrolling handles large content** - Only render visible portions
4. **Memory monitoring is essential** - Track and optimize memory usage
5. **Web Workers for heavy processing** - Offload compression and parsing
6. **Smart batching improves efficiency** - Group updates intelligently
7. **Performance monitoring guides optimization** - Measure to improve

---

**Next**: [Advanced Features: Production-Ready Patterns](../advanced-features/01-retry-mechanisms.md)

**Previous**: [06-error-recovery-mechanisms.md](./06-error-recovery-mechanisms.md)