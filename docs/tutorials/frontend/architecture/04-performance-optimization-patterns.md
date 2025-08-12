# Architecture 4: Performance Optimization Patterns - Advanced Performance Strategies

## 🎯 **Learning Objectives**

By the end of this tutorial, you will understand:
- Advanced React performance optimization techniques for chat applications
- Memory management strategies for long-running streaming applications
- Virtualization and windowing patterns for large message lists
- Code splitting and lazy loading patterns for optimal bundle sizes
- Performance monitoring and measurement strategies
- Browser-specific optimizations and compatibility patterns

## ⚡ **The Performance Challenge**

Chat applications face unique performance challenges:
- **Large Data Sets**: Thousands of messages with rich content
- **High-Frequency Updates**: Real-time streaming chunk updates
- **Memory Growth**: Accumulating message history over time
- **Scroll Performance**: Smooth scrolling through large message lists
- **Bundle Size**: Keeping initial load times fast
- **Mobile Performance**: Resource constraints on mobile devices

**Our goal**: Build **high-performance chat experiences** that remain responsive under any load.

## 🏗️ **Performance Architecture Overview**

### **Performance Monitoring Foundation**

```typescript
// src/services/performanceMonitoring.ts
interface PerformanceMetrics {
  renderTime: number
  memoryUsage: number
  bundleSize: number
  initialLoadTime: number
  timeToInteractive: number
  firstContentfulPaint: number
  largestContentfulPaint: number
  cumulativeLayoutShift: number
  
  // Custom metrics
  messageRenderTime: number
  streamingLatency: number
  scrollPerformance: number
  componentRerenders: number
}

interface PerformanceObservation {
  timestamp: Date
  metrics: Partial<PerformanceMetrics>
  context: {
    page: string
    component?: string
    action?: string
    messageCount?: number
    sessionDuration: number
  }
}

class PerformanceMonitoringService {
  private observations: PerformanceObservation[] = []
  private performanceObserver?: PerformanceObserver
  private memoryMonitorInterval?: NodeJS.Timer
  
  constructor() {
    this.setupWebVitalsMonitoring()
    this.setupMemoryMonitoring()
    this.setupCustomMetrics()
  }
  
  private setupWebVitalsMonitoring(): void {
    // First Contentful Paint
    this.observePerformanceEntry('paint', (entries) => {
      const fcp = entries.find(entry => entry.name === 'first-contentful-paint')
      if (fcp) {
        this.recordMetric({ firstContentfulPaint: fcp.startTime })
      }
    })
    
    // Largest Contentful Paint
    this.observePerformanceEntry('largest-contentful-paint', (entries) => {
      const lcp = entries[entries.length - 1]
      if (lcp) {
        this.recordMetric({ largestContentfulPaint: lcp.startTime })
      }
    })
    
    // Cumulative Layout Shift
    this.observePerformanceEntry('layout-shift', (entries) => {
      let cls = 0
      entries.forEach(entry => {
        if (!(entry as any).hadRecentInput) {
          cls += (entry as any).value
        }
      })
      if (cls > 0) {
        this.recordMetric({ cumulativeLayoutShift: cls })
      }
    })
    
    // Long Tasks (Performance issues)
    this.observePerformanceEntry('longtask', (entries) => {
      entries.forEach(entry => {
        console.warn(`Long task detected: ${entry.duration}ms`, entry)
      })
    })
  }
  
  private setupMemoryMonitoring(): void {
    if ('memory' in performance) {
      this.memoryMonitorInterval = setInterval(() => {
        const memory = (performance as any).memory
        this.recordMetric({
          memoryUsage: memory.usedJSHeapSize / 1024 / 1024 // MB
        })
      }, 10000) // Every 10 seconds
    }
  }
  
  private setupCustomMetrics(): void {
    // Monitor component render times
    if ('measure' in performance) {
      const originalSetState = React.Component.prototype.setState
      React.Component.prototype.setState = function(updater, callback) {
        const startTime = performance.now()
        return originalSetState.call(this, updater, () => {
          const endTime = performance.now()
          performanceMonitoring.recordMetric({
            componentRerenders: 1,
            renderTime: endTime - startTime
          }, {
            component: this.constructor.name
          })
          callback?.()
        })
      }
    }
  }
  
  private observePerformanceEntry(
    type: string, 
    callback: (entries: PerformanceEntry[]) => void
  ): void {
    try {
      const observer = new PerformanceObserver((list) => {
        callback(list.getEntries())
      })
      observer.observe({ entryTypes: [type] })
    } catch (error) {
      console.warn(`Performance observer not supported for ${type}:`, error)
    }
  }
  
  recordMetric(
    metrics: Partial<PerformanceMetrics>, 
    context: Partial<PerformanceObservation['context']> = {}
  ): void {
    const observation: PerformanceObservation = {
      timestamp: new Date(),
      metrics,
      context: {
        page: window.location.pathname,
        sessionDuration: Date.now() - this.getSessionStartTime(),
        ...context
      }
    }
    
    this.observations.push(observation)
    
    // Keep only last 1000 observations
    if (this.observations.length > 1000) {
      this.observations.shift()
    }
    
    // Report critical performance issues
    this.checkPerformanceThresholds(observation)
  }
  
  private checkPerformanceThresholds(observation: PerformanceObservation): void {
    const { metrics } = observation
    
    // Memory usage warning
    if (metrics.memoryUsage && metrics.memoryUsage > 100) {
      console.warn(`High memory usage: ${metrics.memoryUsage.toFixed(2)}MB`)
    }
    
    // Render time warning
    if (metrics.renderTime && metrics.renderTime > 16) {
      console.warn(`Slow render: ${metrics.renderTime.toFixed(2)}ms`, observation.context)
    }
    
    // Cumulative Layout Shift warning
    if (metrics.cumulativeLayoutShift && metrics.cumulativeLayoutShift > 0.1) {
      console.warn(`High CLS: ${metrics.cumulativeLayoutShift.toFixed(3)}`)
    }
  }
  
  getMetricsSummary(): {
    averages: Partial<PerformanceMetrics>
    counts: Record<string, number>
    trends: Record<string, 'improving' | 'stable' | 'degrading'>
  } {
    const allMetrics = this.observations.map(obs => obs.metrics)
    
    const averages: Partial<PerformanceMetrics> = {}
    const counts: Record<string, number> = {}
    
    // Calculate averages
    Object.keys(allMetrics[0] || {}).forEach(key => {
      const values = allMetrics
        .map(m => m[key as keyof PerformanceMetrics])
        .filter(v => v !== undefined) as number[]
      
      if (values.length > 0) {
        averages[key as keyof PerformanceMetrics] = 
          values.reduce((sum, val) => sum + val, 0) / values.length
        counts[key] = values.length
      }
    })
    
    // Calculate trends (simplified)
    const trends: Record<string, 'improving' | 'stable' | 'degrading'> = {}
    Object.keys(averages).forEach(key => {
      const recentValues = this.observations
        .slice(-10)
        .map(obs => obs.metrics[key as keyof PerformanceMetrics])
        .filter(v => v !== undefined) as number[]
        
      if (recentValues.length >= 5) {
        const firstHalf = recentValues.slice(0, Math.floor(recentValues.length / 2))
        const secondHalf = recentValues.slice(Math.floor(recentValues.length / 2))
        
        const firstAvg = firstHalf.reduce((sum, val) => sum + val, 0) / firstHalf.length
        const secondAvg = secondHalf.reduce((sum, val) => sum + val, 0) / secondHalf.length
        
        const change = (secondAvg - firstAvg) / firstAvg
        
        if (change > 0.1) trends[key] = 'degrading'
        else if (change < -0.1) trends[key] = 'improving'
        else trends[key] = 'stable'
      }
    })
    
    return { averages, counts, trends }
  }
  
  private getSessionStartTime(): number {
    let startTime = sessionStorage.getItem('session-start-time')
    if (!startTime) {
      startTime = Date.now().toString()
      sessionStorage.setItem('session-start-time', startTime)
    }
    return parseInt(startTime, 10)
  }
}

export const performanceMonitoring = new PerformanceMonitoringService()
```

### **Memory Management Patterns**

```typescript
// src/hooks/useMemoryOptimization.ts
import { useEffect, useRef, useCallback, useState } from 'react'

interface MemoryOptimizationOptions {
  maxItems: number
  pruneThreshold: number
  enableCompression: boolean
  enableWeakReferences: boolean
  memoryThreshold: number // MB
}

interface MemoryStats {
  itemCount: number
  estimatedMemoryUsage: number
  compressionRatio: number
  pruneCount: number
  lastCleanup: Date
}

export const useMemoryOptimization = <T>(
  items: T[],
  options: Partial<MemoryOptimizationOptions> = {}
) => {
  const {
    maxItems = 1000,
    pruneThreshold = 1200,
    enableCompression = true,
    enableWeakReferences = true,
    memoryThreshold = 50,
  } = options
  
  const [memoryStats, setMemoryStats] = useState<MemoryStats>({
    itemCount: 0,
    estimatedMemoryUsage: 0,
    compressionRatio: 1,
    pruneCount: 0,
    lastCleanup: new Date(),
  })
  
  const compressedItemsRef = useRef<Map<string, string>>(new Map())
  const weakReferencesRef = useRef<WeakMap<object, T>>(new WeakMap())
  const memoryCheckIntervalRef = useRef<NodeJS.Timer>()
  
  // Estimate memory usage of an item
  const estimateItemSize = useCallback((item: T): number => {
    try {
      const serialized = JSON.stringify(item)
      return new Blob([serialized]).size
    } catch {
      return 1024 // Default estimate: 1KB
    }
  }, [])
  
  // Compress large items
  const compressItem = useCallback(async (item: T, key: string): Promise<string> => {
    if (!enableCompression) return JSON.stringify(item)
    
    try {
      const serialized = JSON.stringify(item)
      
      // Only compress if item is large enough
      if (serialized.length > 5000) {
        // Use CompressionStream if available
        if ('CompressionStream' in window) {
          const stream = new CompressionStream('gzip')
          const writer = stream.writable.getWriter()
          const reader = stream.readable.getReader()
          
          writer.write(new TextEncoder().encode(serialized))
          writer.close()
          
          const chunks: Uint8Array[] = []
          let done = false
          
          while (!done) {
            const { value, done: readerDone } = await reader.read()
            done = readerDone
            if (value) chunks.push(value)
          }
          
          const compressed = new Uint8Array(
            chunks.reduce((acc, chunk) => acc + chunk.length, 0)
          )
          
          let offset = 0
          chunks.forEach(chunk => {
            compressed.set(chunk, offset)
            offset += chunk.length
          })
          
          return btoa(String.fromCharCode(...compressed))
        }
        
        // Fallback compression using LZ-string if available
        if ('LZString' in window) {
          return (window as any).LZString.compress(serialized)
        }
      }
      
      return serialized
    } catch (error) {
      console.warn('Compression failed:', error)
      return JSON.stringify(item)
    }
  }, [enableCompression])
  
  // Decompress item
  const decompressItem = useCallback(async (compressed: string): Promise<T> => {
    try {
      // Try to parse as regular JSON first
      return JSON.parse(compressed)
    } catch {
      try {
        // Try gzip decompression
        if ('DecompressionStream' in window) {
          const compressed_data = Uint8Array.from(atob(compressed), c => c.charCodeAt(0))
          const stream = new DecompressionStream('gzip')
          const writer = stream.writable.getWriter()
          const reader = stream.readable.getReader()
          
          writer.write(compressed_data)
          writer.close()
          
          const chunks: Uint8Array[] = []
          let done = false
          
          while (!done) {
            const { value, done: readerDone } = await reader.read()
            done = readerDone
            if (value) chunks.push(value)
          }
          
          const decompressed = new Uint8Array(
            chunks.reduce((acc, chunk) => acc + chunk.length, 0)
          )
          
          let offset = 0
          chunks.forEach(chunk => {
            decompressed.set(chunk, offset)
            offset += chunk.length
          })
          
          const text = new TextDecoder().decode(decompressed)
          return JSON.parse(text)
        }
        
        // Try LZ-string decompression
        if ('LZString' in window) {
          const decompressed = (window as any).LZString.decompress(compressed)
          return JSON.parse(decompressed)
        }
        
        throw new Error('No decompression method available')
      } catch (error) {
        console.warn('Decompression failed:', error)
        throw error
      }
    }
  }, [])
  
  // Prune old items when threshold is exceeded
  const pruneItems = useCallback((currentItems: T[]): T[] => {
    if (currentItems.length <= maxItems) return currentItems
    
    // Keep the most recent items
    const prunedItems = currentItems.slice(-maxItems)
    const pruneCount = currentItems.length - prunedItems.length
    
    setMemoryStats(prev => ({
      ...prev,
      pruneCount: prev.pruneCount + pruneCount,
      lastCleanup: new Date(),
    }))
    
    console.log(`Pruned ${pruneCount} items from memory`)
    return prunedItems
    
  }, [maxItems])
  
  // Memory pressure detection and cleanup
  const handleMemoryPressure = useCallback((): void => {
    if ('memory' in performance) {
      const memory = (performance as any).memory
      const usedMB = memory.usedJSHeapSize / 1024 / 1024
      
      if (usedMB > memoryThreshold) {
        console.warn(`Memory pressure detected: ${usedMB.toFixed(2)}MB`)
        
        // Force garbage collection if available
        if ('gc' in window && typeof window.gc === 'function') {
          window.gc()
        }
        
        // Clear compressed cache
        compressedItemsRef.current.clear()
        
        // Trigger memory cleanup event
        window.dispatchEvent(new CustomEvent('memory-pressure', { 
          detail: { usedMemory: usedMB } 
        }))
      }
    }
  }, [memoryThreshold])
  
  // Periodic memory monitoring
  useEffect(() => {
    memoryCheckIntervalRef.current = setInterval(() => {
      handleMemoryPressure()
      
      // Update memory stats
      if ('memory' in performance) {
        const memory = (performance as any).memory
        setMemoryStats(prev => ({
          ...prev,
          itemCount: items.length,
          estimatedMemoryUsage: memory.usedJSHeapSize / 1024 / 1024,
        }))
      }
    }, 5000) // Check every 5 seconds
    
    return () => {
      if (memoryCheckIntervalRef.current) {
        clearInterval(memoryCheckIntervalRef.current)
      }
    }
  }, [handleMemoryPressure, items.length])
  
  // Process items with memory optimization
  const optimizedItems = useCallback((sourceItems: T[]): T[] => {
    let processedItems = sourceItems
    
    // Prune if necessary
    if (processedItems.length > pruneThreshold) {
      processedItems = pruneItems(processedItems)
    }
    
    return processedItems
  }, [pruneItems, pruneThreshold])
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      compressedItemsRef.current.clear()
      if (memoryCheckIntervalRef.current) {
        clearInterval(memoryCheckIntervalRef.current)
      }
    }
  }, [])
  
  return {
    optimizedItems: optimizedItems(items),
    memoryStats,
    compressItem,
    decompressItem,
    pruneItems,
    handleMemoryPressure,
  }
}
```

### **Virtualization and Windowing**

```typescript
// src/components/VirtualizedMessageList.tsx
import React, { useMemo, useCallback, useRef, useState, useEffect } from 'react'

interface VirtualizedMessageListProps<T> {
  items: T[]
  itemHeight: number | ((item: T, index: number) => number)
  containerHeight: number
  renderItem: (item: T, index: number, style: React.CSSProperties) => React.ReactNode
  overscan?: number
  onScroll?: (scrollTop: number, scrollDirection: 'up' | 'down') => void
  maintainScrollPosition?: boolean
  className?: string
}

interface VirtualScrollState {
  scrollTop: number
  visibleStartIndex: number
  visibleEndIndex: number
  itemOffsets: number[]
  totalHeight: number
}

export const VirtualizedMessageList = <T,>({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  overscan = 5,
  onScroll,
  maintainScrollPosition = false,
  className = '',
}: VirtualizedMessageListProps<T>) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const [scrollState, setScrollState] = useState<VirtualScrollState>({
    scrollTop: 0,
    visibleStartIndex: 0,
    visibleEndIndex: 0,
    itemOffsets: [],
    totalHeight: 0,
  })
  
  const previousScrollTop = useRef(0)
  const isScrolling = useRef(false)
  const scrollingTimeout = useRef<NodeJS.Timeout>()
  
  // Calculate item heights and offsets
  const { itemOffsets, totalHeight } = useMemo(() => {
    const offsets: number[] = [0]
    let totalHeight = 0
    
    for (let i = 0; i < items.length; i++) {
      const height = typeof itemHeight === 'function' 
        ? itemHeight(items[i], i) 
        : itemHeight
      
      totalHeight += height
      offsets.push(totalHeight)
    }
    
    return { itemOffsets: offsets, totalHeight }
  }, [items, itemHeight])
  
  // Calculate visible range
  const visibleRange = useMemo(() => {
    const { scrollTop } = scrollState
    
    // Binary search for start index
    let startIndex = 0
    let endIndex = itemOffsets.length - 1
    
    while (startIndex < endIndex) {
      const mid = Math.floor((startIndex + endIndex) / 2)
      if (itemOffsets[mid] < scrollTop) {
        startIndex = mid + 1
      } else {
        endIndex = mid
      }
    }
    
    const visibleStartIndex = Math.max(0, startIndex - overscan)
    
    // Find end index
    let visibleEndIndex = visibleStartIndex
    let currentOffset = itemOffsets[visibleStartIndex]
    
    while (visibleEndIndex < items.length && currentOffset < scrollTop + containerHeight) {
      visibleEndIndex++
      if (visibleEndIndex < itemOffsets.length) {
        currentOffset = itemOffsets[visibleEndIndex]
      }
    }
    
    visibleEndIndex = Math.min(items.length - 1, visibleEndIndex + overscan)
    
    return { visibleStartIndex, visibleEndIndex }
  }, [scrollState.scrollTop, itemOffsets, containerHeight, overscan, items.length])
  
  // Handle scroll events with throttling
  const handleScroll = useCallback((event: React.UIEvent<HTMLDivElement>) => {
    const scrollTop = event.currentTarget.scrollTop
    const scrollDirection = scrollTop > previousScrollTop.current ? 'down' : 'up'
    
    previousScrollTop.current = scrollTop
    isScrolling.current = true
    
    // Clear previous timeout
    if (scrollingTimeout.current) {
      clearTimeout(scrollingTimeout.current)
    }
    
    // Update scroll state
    setScrollState(prev => ({
      ...prev,
      scrollTop,
      ...visibleRange,
    }))
    
    // Call external scroll handler
    onScroll?.(scrollTop, scrollDirection)
    
    // Set scrolling to false after a delay
    scrollingTimeout.current = setTimeout(() => {
      isScrolling.current = false
    }, 150)
    
    // Performance monitoring
    performanceMonitoring.recordMetric({
      scrollPerformance: performance.now()
    }, {
      component: 'VirtualizedMessageList',
      action: 'scroll',
      messageCount: items.length
    })
  }, [visibleRange, onScroll, items.length])
  
  // Maintain scroll position when items change
  useEffect(() => {
    if (maintainScrollPosition && containerRef.current) {
      const container = containerRef.current
      const { scrollTop } = scrollState
      
      // If we're at the bottom, stay at the bottom
      const isAtBottom = scrollTop + containerHeight >= totalHeight - 10
      
      if (isAtBottom) {
        container.scrollTop = totalHeight - containerHeight
      }
    }
  }, [items.length, totalHeight, maintainScrollPosition, scrollState, containerHeight])
  
  // Render visible items
  const visibleItems = useMemo(() => {
    const rendered = []
    
    for (let i = visibleRange.visibleStartIndex; i <= visibleRange.visibleEndIndex; i++) {
      if (i >= items.length) break
      
      const item = items[i]
      const top = itemOffsets[i]
      const height = itemOffsets[i + 1] - itemOffsets[i]
      
      const style: React.CSSProperties = {
        position: 'absolute',
        top: top,
        left: 0,
        right: 0,
        height: height,
      }
      
      rendered.push({
        key: i,
        item,
        index: i,
        style,
      })
    }
    
    return rendered
  }, [items, visibleRange, itemOffsets])
  
  // Performance monitoring for render time
  useEffect(() => {
    const startTime = performance.now()
    
    return () => {
      const endTime = performance.now()
      performanceMonitoring.recordMetric({
        messageRenderTime: endTime - startTime
      }, {
        component: 'VirtualizedMessageList',
        messageCount: visibleItems.length
      })
    }
  }, [visibleItems.length])
  
  return (
    <div
      ref={containerRef}
      className={`virtualized-message-list ${className}`}
      style={{
        height: containerHeight,
        overflow: 'auto',
        position: 'relative',
      }}
      onScroll={handleScroll}
    >
      {/* Virtual container with total height */}
      <div
        style={{
          height: totalHeight,
          position: 'relative',
        }}
      >
        {/* Render visible items */}
        {visibleItems.map(({ key, item, index, style }) =>
          <div key={key} style={style}>
            {renderItem(item, index, style)}
          </div>
        )}
      </div>
      
      {/* Scroll indicator for development */}
      {process.env.NODE_ENV === 'development' && (
        <div
          style={{
            position: 'fixed',
            top: 10,
            right: 10,
            background: 'rgba(0,0,0,0.7)',
            color: 'white',
            padding: '5px 10px',
            borderRadius: '3px',
            fontSize: '12px',
            pointerEvents: 'none',
            zIndex: 9999,
          }}
        >
          Items: {visibleRange.visibleStartIndex}-{visibleRange.visibleEndIndex} / {items.length}
          <br />
          Scroll: {Math.round(scrollState.scrollTop)}px
        </div>
      )}
    </div>
  )
}
```

### **Code Splitting and Lazy Loading**

```typescript
// src/utils/lazyLoading.ts
import { lazy, ComponentType } from 'react'

interface LazyLoadOptions {
  delay?: number // Minimum delay before loading
  preload?: boolean // Preload on hover/focus
  retries?: number // Retry failed loads
  fallback?: ComponentType<any>
}

// Enhanced lazy loading with retry logic and preloading
export const createLazyComponent = <T extends ComponentType<any>>(
  importFunc: () => Promise<{ default: T }>,
  options: LazyLoadOptions = {}
): ComponentType<React.ComponentProps<T>> => {
  const {
    delay = 0,
    preload = true,
    retries = 3,
    fallback
  } = options
  
  let componentPromise: Promise<{ default: T }> | null = null
  let retryCount = 0
  
  const loadComponent = async (): Promise<{ default: T }> => {
    if (componentPromise) return componentPromise
    
    componentPromise = new Promise(async (resolve, reject) => {
      try {
        // Add artificial delay if specified
        if (delay > 0) {
          await new Promise(resolve => setTimeout(resolve, delay))
        }
        
        const startTime = performance.now()
        const component = await importFunc()
        const loadTime = performance.now() - startTime
        
        // Record performance metrics
        performanceMonitoring.recordMetric({
          bundleSize: loadTime // Approximation
        }, {
          component: component.default.name || 'LazyComponent',
          action: 'lazy_load'
        })
        
        resolve(component)
      } catch (error) {
        componentPromise = null // Reset for retry
        
        if (retryCount < retries) {
          retryCount++
          console.warn(`Lazy load failed, retrying (${retryCount}/${retries}):`, error)
          
          // Exponential backoff
          const retryDelay = Math.pow(2, retryCount - 1) * 1000
          await new Promise(resolve => setTimeout(resolve, retryDelay))
          
          resolve(await loadComponent())
        } else {
          reject(error)
        }
      }
    })
    
    return componentPromise
  }
  
  const LazyComponent = lazy(loadComponent)
  
  // Add preloading capabilities
  if (preload) {
    ;(LazyComponent as any).preload = loadComponent
  }
  
  return LazyComponent
}

// Route-based code splitting
export const createLazyRoute = (
  importFunc: () => Promise<{ default: ComponentType<any> }>,
  fallbackComponent?: ComponentType<any>
) => {
  return createLazyComponent(importFunc, {
    preload: true,
    retries: 2,
    fallback: fallbackComponent
  })
}

// Feature-based code splitting
const AdvancedSearchModal = createLazyComponent(
  () => import('../components/AdvancedSearch/AdvancedSearchModal'),
  { preload: false }
)

const MessageExportDialog = createLazyComponent(
  () => import('../components/Export/MessageExportDialog'),
  { preload: false }
)

const ConversationAnalytics = createLazyComponent(
  () => import('../components/Analytics/ConversationAnalytics'),
  { preload: false }
)

// Preloading utilities
export const preloadComponents = {
  search: () => (AdvancedSearchModal as any).preload?.(),
  export: () => (MessageExportDialog as any).preload?.(),
  analytics: () => (ConversationAnalytics as any).preload?.(),
}

// Bundle analysis helper
export const analyzeBundleSize = async (): Promise<{
  totalSize: number
  chunkSizes: Record<string, number>
  recommendations: string[]
}> => {
  const chunks = await Promise.all([
    import('./chunk1').catch(() => ({ size: 0 })),
    import('./chunk2').catch(() => ({ size: 0 })),
    // Add more chunks as needed
  ])
  
  const chunkSizes: Record<string, number> = {}
  let totalSize = 0
  
  chunks.forEach((chunk, index) => {
    const size = (chunk as any).size || 0
    chunkSizes[`chunk${index + 1}`] = size
    totalSize += size
  })
  
  const recommendations = []
  if (totalSize > 1024 * 1024) { // 1MB
    recommendations.push('Consider splitting large chunks further')
  }
  
  return {
    totalSize,
    chunkSizes,
    recommendations
  }
}
```

### **Performance Optimization Hooks**

```typescript
// src/hooks/usePerformanceOptimization.ts
import { useMemo, useCallback, useRef, useEffect } from 'react'

// Debounced values for high-frequency updates
export const useDebouncedValue = <T>(value: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = React.useState(value)
  const timeoutRef = useRef<NodeJS.Timeout>()
  
  useEffect(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    
    timeoutRef.current = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)
    
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [value, delay])
  
  return debouncedValue
}

// Throttled callbacks for scroll and resize events
export const useThrottledCallback = <T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T => {
  const lastCall = useRef<number>(0)
  const timeoutRef = useRef<NodeJS.Timeout>()
  
  return useCallback((...args: Parameters<T>) => {
    const now = Date.now()
    
    if (now - lastCall.current >= delay) {
      lastCall.current = now
      callback(...args)
    } else {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
      
      timeoutRef.current = setTimeout(() => {
        lastCall.current = Date.now()
        callback(...args)
      }, delay - (now - lastCall.current))
    }
  }, [callback, delay]) as T
}

// Memoized expensive computations with cache invalidation
export const useMemoWithInvalidation = <T>(
  factory: () => T,
  deps: React.DependencyList,
  invalidateOn?: string[]
): T => {
  const cacheRef = useRef<{
    deps: React.DependencyList
    value: T
    invalidation: string[]
  }>()
  
  const shouldInvalidate = invalidateOn && invalidateOn.some(key => {
    return cacheRef.current?.invalidation.includes(key)
  })
  
  return useMemo(() => {
    const result = factory()
    
    cacheRef.current = {
      deps,
      value: result,
      invalidation: invalidateOn || []
    }
    
    return result
  }, shouldInvalidate ? [...deps, ...invalidateOn] : deps)
}

// RAF-based animation hooks
export const useAnimationFrame = (callback: (time: number) => void) => {
  const requestRef = useRef<number>()
  const previousTimeRef = useRef<number>()
  
  const animate = useCallback((time: number) => {
    if (previousTimeRef.current !== undefined) {
      callback(time - previousTimeRef.current)
    }
    previousTimeRef.current = time
    requestRef.current = requestAnimationFrame(animate)
  }, [callback])
  
  useEffect(() => {
    requestRef.current = requestAnimationFrame(animate)
    return () => {
      if (requestRef.current) {
        cancelAnimationFrame(requestRef.current)
      }
    }
  }, [animate])
}

// Performance-aware rendering
export const useRenderPerformance = (componentName: string) => {
  const renderStartRef = useRef<number>()
  const renderCountRef = useRef(0)
  
  useEffect(() => {
    renderStartRef.current = performance.now()
    renderCountRef.current++
  })
  
  useEffect(() => {
    if (renderStartRef.current) {
      const renderTime = performance.now() - renderStartRef.current
      
      performanceMonitoring.recordMetric({
        renderTime,
        componentRerenders: 1
      }, {
        component: componentName
      })
      
      // Warn about slow renders
      if (renderTime > 16) {
        console.warn(`Slow render in ${componentName}: ${renderTime.toFixed(2)}ms`)
      }
    }
  })
  
  return {
    renderCount: renderCountRef.current,
    averageRenderTime: renderStartRef.current 
      ? (performance.now() - renderStartRef.current) / renderCountRef.current 
      : 0
  }
}
```

## 🎯 **Usage Examples**

### **Optimized Chat Container**
```typescript
// Highly optimized chat container with all performance patterns
export const OptimizedChatContainer: React.FC = () => {
  const { optimizedItems, memoryStats } = useMemoryOptimization(messages, {
    maxItems: 1000,
    enableCompression: true
  })
  
  const debouncedQuery = useDebouncedValue(searchQuery, 300)
  const { renderCount } = useRenderPerformance('OptimizedChatContainer')
  
  const handleScroll = useThrottledCallback((scrollTop: number) => {
    // Handle scroll events
    onScroll?.(scrollTop)
  }, 100)
  
  const renderMessage = useCallback((message: Message, index: number, style: React.CSSProperties) => (
    <div key={message.id} style={style}>
      <MessageComponent message={message} />
    </div>
  ), [])
  
  return (
    <div className="optimized-chat-container">
      <VirtualizedMessageList
        items={optimizedItems}
        itemHeight={120}
        containerHeight={600}
        renderItem={renderMessage}
        onScroll={handleScroll}
        maintainScrollPosition={true}
      />
      
      {process.env.NODE_ENV === 'development' && (
        <div className="performance-stats">
          <div>Renders: {renderCount}</div>
          <div>Memory: {memoryStats.estimatedMemoryUsage.toFixed(1)}MB</div>
          <div>Items: {optimizedItems.length}</div>
        </div>
      )}
    </div>
  )
}
```

## 🎯 **Key Takeaways**

1. **Measure before optimizing** - Use performance monitoring to identify bottlenecks
2. **Virtualize large lists** - Only render visible items in long message histories
3. **Manage memory proactively** - Prune old data and compress large items
4. **Code split strategically** - Load features on demand to reduce initial bundle size
5. **Debounce high-frequency updates** - Prevent UI blocking during rapid state changes
6. **Monitor real-world performance** - Track Web Vitals and custom metrics
7. **Optimize for mobile** - Consider resource constraints and battery usage

---

**Next**: [05-testing-strategies.md](./05-testing-strategies.md) - Comprehensive Testing Architecture

**Previous**: [03-error-boundary-strategies.md](./03-error-boundary-strategies.md)