# Production Performance Optimization: Frontend Tuning Guide

## 🎯 **What You'll Learn**

This advanced performance guide covers:
- React 18 performance optimization techniques for production
- Bundle analysis and size optimization strategies
- Runtime performance monitoring and optimization
- Memory management and leak prevention
- Core Web Vitals optimization for real user experiences
- Advanced caching strategies and CDN configuration

## 📊 **Performance Baseline Analysis**

### **Step 1: Current Performance Audit**

```bash
# Install analysis tools
npm install --save-dev webpack-bundle-analyzer
npm install --save-dev @vitejs/plugin-legacy
npm install --save-dev vite-plugin-pwa

# Run bundle analysis
npm run build:analyze
```

```javascript
// scripts/analyze-bundle.js
import { analyzeMetafile } from 'esbuild'
import fs from 'fs'

const metafile = JSON.parse(fs.readFileSync('dist/metafile.json'))
const analysis = await analyzeMetafile(metafile)
console.log(analysis)
```

```typescript
// src/utils/performanceMonitor.ts
export class PerformanceMonitor {
  private static measurements: Map<string, number> = new Map()
  
  static startMeasurement(name: string): void {
    this.measurements.set(name, performance.now())
  }
  
  static endMeasurement(name: string): number {
    const start = this.measurements.get(name)
    if (!start) {
      console.warn(`No start time found for measurement: ${name}`)
      return 0
    }
    
    const duration = performance.now() - start
    this.measurements.delete(name)
    
    // Log in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`⏱️ ${name}: ${duration.toFixed(2)}ms`)
    }
    
    // Report to analytics in production
    if (process.env.NODE_ENV === 'production' && window.gtag) {
      window.gtag('event', 'timing_complete', {
        name: name,
        value: Math.round(duration)
      })
    }
    
    return duration
  }
  
  static measureAsync<T>(name: string, fn: () => Promise<T>): Promise<T> {
    return new Promise(async (resolve, reject) => {
      this.startMeasurement(name)
      try {
        const result = await fn()
        this.endMeasurement(name)
        resolve(result)
      } catch (error) {
        this.endMeasurement(name)
        reject(error)
      }
    })
  }
}
```

### **Step 2: Bundle Size Optimization**

```typescript
// vite.config.ts - Advanced build optimization
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { visualizer } from 'rollup-plugin-visualizer'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react({
      // Enable React Fast Refresh optimizations
      fastRefresh: true,
      
      // Optimize JSX runtime
      jsxRuntime: 'automatic',
      
      // Remove PropTypes in production
      babel: {
        plugins: process.env.NODE_ENV === 'production' ? [
          ['babel-plugin-transform-remove-console', { exclude: ['error', 'warn'] }]
        ] : []
      }
    }),
    
    // Bundle analyzer
    visualizer({
      filename: 'dist/bundle-analysis.html',
      open: true,
      gzipSize: true,
    }),
    
    // PWA for caching
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\.yourdomain\.com\//,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 * 24 // 24 hours
              }
            }
          }
        ]
      }
    })
  ],
  
  build: {
    target: 'es2018', // Better browser support
    
    // Enable source maps for production debugging
    sourcemap: true,
    
    rollupOptions: {
      output: {
        // Advanced chunk splitting strategy
        manualChunks: {
          // Vendor libraries that rarely change
          'vendor-react': ['react', 'react-dom'],
          'vendor-routing': ['react-router-dom'],
          'vendor-ui': ['lucide-react'],
          'vendor-syntax': ['react-syntax-highlighter'],
          
          // Feature-based chunks
          'feature-streaming': ['../services/streamingApi'],
          'feature-orchestrator': ['../services/orchestratorApi'],
          'feature-protocols': [
            '../services/a2aParser',
            '../services/acpParser',
            '../services/protocolParser'
          ],
          
          // Utils that might be shared
          'utils': [
            '../utils/performance',
            '../utils/errorTracking',
            '../utils/webVitals'
          ]
        },
        
        // Optimize chunk names for caching
        chunkFileNames: (chunkInfo) => {
          const facadeModuleId = chunkInfo.facadeModuleId
          
          if (facadeModuleId) {
            // Route-based chunks
            if (facadeModuleId.includes('pages/')) {
              return 'pages/[name]-[hash].js'
            }
            
            // Component chunks
            if (facadeModuleId.includes('components/')) {
              return 'components/[name]-[hash].js'
            }
          }
          
          return 'chunks/[name]-[hash].js'
        },
        
        // Optimize asset names
        assetFileNames: (assetInfo) => {
          if (assetInfo.name?.endsWith('.css')) {
            return 'styles/[name]-[hash][extname]'
          }
          
          if (/\.(png|jpe?g|svg|gif|tiff|bmp|ico)$/.test(assetInfo.name || '')) {
            return 'images/[name]-[hash][extname]'
          }
          
          return 'assets/[name]-[hash][extname]'
        }
      }
    },
    
    // Compression settings
    minify: 'terser',
    terserOptions: {
      compress: {
        // Remove console statements in production
        drop_console: true,
        drop_debugger: true,
        
        // Remove unused code
        dead_code: true,
        
        // Optimize conditionals
        conditionals: true,
        
        // Remove unused variables
        unused: true,
      },
      mangle: {
        // Preserve class names for debugging
        keep_classnames: true,
        keep_fnames: true,
      },
      format: {
        // Remove comments
        comments: false,
      }
    },
    
    // Asset optimization
    assetsInlineLimit: 2048, // Inline small assets (2KB)
    
    // Chunk size warnings
    chunkSizeWarningLimit: 1000, // 1MB warning
    
    // Enable CSS code splitting
    cssCodeSplit: true,
  },
  
  // Dependency pre-bundling optimization
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'lucide-react',
    ],
    
    // Exclude large dependencies that should be loaded on demand
    exclude: [
      'react-syntax-highlighter/dist/esm/languages/hljs',
    ]
  }
})
```

### **Step 3: React Component Optimization**

```typescript
// src/components/OptimizedMessage.tsx
import React, { memo, useMemo, useCallback, useState } from 'react'
import { PerformanceMonitor } from '../utils/performanceMonitor'

interface OptimizedMessageProps {
  content: string
  agentName: string
  timestamp: string
  protocol: string
  onCopy?: (content: string) => void
  onRetry?: () => void
}

// Memoized sub-components to prevent unnecessary re-renders
const MessageHeader = memo<{
  agentName: string
  protocol: string
  timestamp: string
}>(({ agentName, protocol, timestamp }) => (
  <div className="flex items-center justify-between mb-2">
    <div className="flex items-center gap-2">
      <span className="font-semibold text-gray-800">{agentName}</span>
      <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
        {protocol.toUpperCase()}
      </span>
    </div>
    <span className="text-xs text-gray-500">{timestamp}</span>
  </div>
))

const MessageActions = memo<{
  onCopy: (content: string) => void
  onRetry: () => void
  content: string
}>(({ onCopy, onRetry, content }) => {
  const handleCopy = useCallback(() => {
    PerformanceMonitor.startMeasurement('message-copy')
    onCopy(content)
    PerformanceMonitor.endMeasurement('message-copy')
  }, [onCopy, content])

  return (
    <div className="flex gap-2 mt-2">
      <button 
        onClick={handleCopy}
        className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
      >
        Copy
      </button>
      <button 
        onClick={onRetry}
        className="px-3 py-1 text-xs bg-blue-100 hover:bg-blue-200 rounded"
      >
        Retry
      </button>
    </div>
  )
})

// Main component with extensive optimization
export const OptimizedMessage = memo<OptimizedMessageProps>(({
  content,
  agentName,
  timestamp,
  protocol,
  onCopy,
  onRetry
}) => {
  const [isExpanded, setIsExpanded] = useState(false)
  
  // Memoize expensive computations
  const processedContent = useMemo(() => {
    PerformanceMonitor.startMeasurement('content-processing')
    
    // Simulate content processing (syntax highlighting, etc.)
    const processed = content.length > 500 && !isExpanded 
      ? content.substring(0, 500) + '...'
      : content
    
    PerformanceMonitor.endMeasurement('content-processing')
    return processed
  }, [content, isExpanded])
  
  const formattedTimestamp = useMemo(() => {
    return new Date(timestamp).toLocaleString()
  }, [timestamp])
  
  // Memoized event handlers
  const handleCopy = useCallback(() => {
    if (onCopy) {
      onCopy(content)
    }
  }, [onCopy, content])
  
  const handleRetry = useCallback(() => {
    if (onRetry) {
      onRetry()
    }
  }, [onRetry])
  
  const toggleExpanded = useCallback(() => {
    setIsExpanded(prev => !prev)
  }, [])
  
  return (
    <div className="message-container p-4 border border-gray-200 rounded-lg">
      <MessageHeader 
        agentName={agentName}
        protocol={protocol}
        timestamp={formattedTimestamp}
      />
      
      <div className="message-content">
        <pre className="whitespace-pre-wrap text-sm">
          {processedContent}
        </pre>
        
        {content.length > 500 && (
          <button
            onClick={toggleExpanded}
            className="mt-2 text-blue-600 hover:text-blue-800 text-sm"
          >
            {isExpanded ? 'Show Less' : 'Show More'}
          </button>
        )}
      </div>
      
      {(onCopy || onRetry) && (
        <MessageActions 
          content={content}
          onCopy={handleCopy}
          onRetry={handleRetry}
        />
      )}
    </div>
  )
}, (prevProps, nextProps) => {
  // Custom comparison for memo
  return (
    prevProps.content === nextProps.content &&
    prevProps.agentName === nextProps.agentName &&
    prevProps.timestamp === nextProps.timestamp &&
    prevProps.protocol === nextProps.protocol
  )
})
```

### **Step 4: Virtual Scrolling for Large Lists**

```typescript
// src/components/VirtualizedMessageList.tsx
import React, { useMemo, useCallback, useRef, useEffect } from 'react'
import { FixedSizeList as List } from 'react-window'
import { OptimizedMessage } from './OptimizedMessage'

interface VirtualizedMessageListProps {
  messages: Array<{
    id: string
    content: string
    agentName: string
    timestamp: string
    protocol: string
  }>
  onCopyMessage?: (content: string) => void
  onRetryMessage?: (messageId: string) => void
}

const ITEM_HEIGHT = 200 // Approximate height per message

export const VirtualizedMessageList: React.FC<VirtualizedMessageListProps> = ({
  messages,
  onCopyMessage,
  onRetryMessage
}) => {
  const listRef = useRef<List>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  
  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (listRef.current && messages.length > 0) {
      listRef.current.scrollToItem(messages.length - 1, 'end')
    }
  }, [messages.length])
  
  // Memoized item renderer to prevent unnecessary re-renders
  const renderItem = useCallback(({ index, style }: { 
    index: number
    style: React.CSSProperties 
  }) => {
    const message = messages[index]
    if (!message) return null
    
    return (
      <div style={style}>
        <div className="p-2">
          <OptimizedMessage
            content={message.content}
            agentName={message.agentName}
            timestamp={message.timestamp}
            protocol={message.protocol}
            onCopy={onCopyMessage}
            onRetry={() => onRetryMessage?.(message.id)}
          />
        </div>
      </div>
    )
  }, [messages, onCopyMessage, onRetryMessage])
  
  // Calculate container height dynamically
  const containerHeight = useMemo(() => {
    return Math.min(600, Math.max(300, messages.length * ITEM_HEIGHT))
  }, [messages.length])
  
  if (messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No messages yet. Start a conversation!
      </div>
    )
  }
  
  return (
    <div 
      ref={containerRef}
      className="virtualized-message-list border border-gray-200 rounded-lg"
    >
      <List
        ref={listRef}
        height={containerHeight}
        itemCount={messages.length}
        itemSize={ITEM_HEIGHT}
        width="100%"
        itemData={messages}
        overscanCount={5} // Render 5 extra items for smooth scrolling
      >
        {renderItem}
      </List>
    </div>
  )
}
```

### **Step 5: Memory Management and Leak Prevention**

```typescript
// src/hooks/useMemoryOptimizedState.ts
import { useState, useCallback, useRef, useEffect } from 'react'

interface MemoryConfig {
  maxItems?: number
  maxAge?: number // in milliseconds
  cleanupInterval?: number // in milliseconds
}

export const useMemoryOptimizedState = <T>(
  config: MemoryConfig = {}
) => {
  const {
    maxItems = 1000,
    maxAge = 5 * 60 * 1000, // 5 minutes
    cleanupInterval = 60 * 1000, // 1 minute
  } = config
  
  const [items, setItems] = useState<Array<T & { _timestamp: number }>>([])
  const cleanupTimerRef = useRef<number>()
  
  // Cleanup old items periodically
  useEffect(() => {
    const cleanup = () => {
      const now = Date.now()
      setItems(current => 
        current.filter(item => now - item._timestamp < maxAge)
      )
    }
    
    cleanupTimerRef.current = window.setInterval(cleanup, cleanupInterval)
    
    return () => {
      if (cleanupTimerRef.current) {
        clearInterval(cleanupTimerRef.current)
      }
    }
  }, [maxAge, cleanupInterval])
  
  const addItem = useCallback((item: T) => {
    const timestampedItem = { ...item, _timestamp: Date.now() }
    
    setItems(current => {
      const updated = [...current, timestampedItem]
      
      // Trim to max items if needed
      if (updated.length > maxItems) {
        return updated.slice(-maxItems)
      }
      
      return updated
    })
  }, [maxItems])
  
  const clearItems = useCallback(() => {
    setItems([])
  }, [])
  
  const getMemoryUsage = useCallback(() => {
    if ('memory' in performance) {
      const memory = (performance as any).memory
      return {
        used: Math.round(memory.usedJSHeapSize / 1024 / 1024), // MB
        total: Math.round(memory.totalJSHeapSize / 1024 / 1024), // MB
        limit: Math.round(memory.jsHeapSizeLimit / 1024 / 1024), // MB
      }
    }
    return null
  }, [])
  
  return {
    items: items.map(({ _timestamp, ...item }) => item as T),
    addItem,
    clearItems,
    itemCount: items.length,
    getMemoryUsage,
  }
}
```

### **Step 6: Code Splitting and Lazy Loading**

```typescript
// src/routes/LazyRoutes.tsx
import React, { Suspense } from 'react'
import { Routes, Route } from 'react-router-dom'
import { ErrorBoundary } from '../components/ErrorBoundary'

// Lazy load route components
const Dashboard = React.lazy(() => import('../pages/Dashboard'))
const AgentChat = React.lazy(() => import('../pages/AgentChat'))
const Settings = React.lazy(() => import('../pages/Settings'))
const AgentDirectory = React.lazy(() => import('../pages/AgentDirectory'))
const SystemHealth = React.lazy(() => import('../pages/SystemHealth'))

// Loading component with skeleton
const RouteLoader: React.FC = () => (
  <div className="animate-pulse p-6">
    <div className="h-4 bg-gray-300 rounded w-3/4 mb-4"></div>
    <div className="h-4 bg-gray-300 rounded w-1/2 mb-4"></div>
    <div className="h-32 bg-gray-300 rounded mb-4"></div>
    <div className="h-4 bg-gray-300 rounded w-2/3"></div>
  </div>
)

export const LazyRoutes: React.FC = () => {
  return (
    <ErrorBoundary>
      <Suspense fallback={<RouteLoader />}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/chat" element={<AgentChat />} />
          <Route path="/agents" element={<AgentDirectory />} />
          <Route path="/health" element={<SystemHealth />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Suspense>
    </ErrorBoundary>
  )
}
```

### **Step 7: Service Worker and Caching Strategy**

```typescript
// public/sw.js - Service Worker for advanced caching
const CACHE_NAME = 'agent-sandbox-v1'
const STATIC_ASSETS = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json'
]

// API cache with expiration
const API_CACHE_NAME = 'api-cache-v1'
const API_CACHE_DURATION = 5 * 60 * 1000 // 5 minutes

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(STATIC_ASSETS))
  )
})

self.addEventListener('fetch', (event) => {
  if (event.request.url.includes('/api/')) {
    // API requests - network first with cache fallback
    event.respondWith(
      caches.open(API_CACHE_NAME).then(async (cache) => {
        try {
          const response = await fetch(event.request)
          
          if (response.ok) {
            // Cache successful responses
            const responseClone = response.clone()
            await cache.put(event.request, responseClone)
          }
          
          return response
        } catch (error) {
          // Network failed, try cache
          const cachedResponse = await cache.match(event.request)
          
          if (cachedResponse) {
            // Check if cached response is still valid
            const cacheDate = cachedResponse.headers.get('sw-cache-date')
            if (cacheDate && Date.now() - parseInt(cacheDate) < API_CACHE_DURATION) {
              return cachedResponse
            }
          }
          
          throw error
        }
      })
    )
  } else {
    // Static assets - cache first
    event.respondWith(
      caches.match(event.request)
        .then(response => response || fetch(event.request))
    )
  }
})
```

### **Step 8: Web Vitals Optimization**

```typescript
// src/utils/webVitalsOptimizer.ts
import { getCLS, getFID, getFCP, getLCP, getTTFB, Metric } from 'web-vitals'

interface VitalThresholds {
  good: number
  needsImprovement: number
}

const THRESHOLDS: Record<string, VitalThresholds> = {
  CLS: { good: 0.1, needsImprovement: 0.25 },
  FID: { good: 100, needsImprovement: 300 },
  FCP: { good: 1800, needsImprovement: 3000 },
  LCP: { good: 2500, needsImprovement: 4000 },
  TTFB: { good: 800, needsImprovement: 1800 },
}

class WebVitalsOptimizer {
  private vitals: Map<string, Metric> = new Map()
  
  init() {
    // Collect all Core Web Vitals
    getCLS(this.handleVital.bind(this))
    getFID(this.handleVital.bind(this))
    getFCP(this.handleVital.bind(this))
    getLCP(this.handleVital.bind(this))
    getTTFB(this.handleVital.bind(this))
  }
  
  private handleVital(metric: Metric) {
    this.vitals.set(metric.name, metric)
    
    const threshold = THRESHOLDS[metric.name]
    if (threshold) {
      const rating = this.getRating(metric.value, threshold)
      
      // Log performance issues
      if (rating !== 'good') {
        console.warn(`⚠️ Poor ${metric.name}: ${metric.value} (${rating})`)
        this.suggestOptimizations(metric.name, rating)
      }
      
      // Send to analytics
      if (window.gtag) {
        window.gtag('event', 'web_vital', {
          event_category: 'Web Vitals',
          event_label: metric.name,
          value: Math.round(metric.value),
          custom_parameter_rating: rating
        })
      }
    }
  }
  
  private getRating(value: number, threshold: VitalThresholds): 'good' | 'needs-improvement' | 'poor' {
    if (value <= threshold.good) return 'good'
    if (value <= threshold.needsImprovement) return 'needs-improvement'
    return 'poor'
  }
  
  private suggestOptimizations(metric: string, rating: string) {
    const suggestions: Record<string, string[]> = {
      CLS: [
        'Add dimensions to images and videos',
        'Avoid inserting content above existing content',
        'Use font-display: swap for web fonts'
      ],
      FID: [
        'Reduce JavaScript execution time',
        'Remove unused JavaScript',
        'Use code splitting to reduce bundle size'
      ],
      LCP: [
        'Optimize images and videos',
        'Preload important resources',
        'Remove unused CSS and JavaScript'
      ],
      FCP: [
        'Eliminate render-blocking resources',
        'Minify CSS and JavaScript',
        'Remove unused code'
      ],
      TTFB: [
        'Use a fast web host',
        'Implement caching',
        'Use a CDN'
      ]
    }
    
    console.group(`💡 Optimization suggestions for ${metric}:`)
    suggestions[metric]?.forEach(suggestion => {
      console.log(`• ${suggestion}`)
    })
    console.groupEnd()
  }
  
  getReport(): Record<string, any> {
    const report: Record<string, any> = {}
    
    this.vitals.forEach((metric, name) => {
      const threshold = THRESHOLDS[name]
      report[name] = {
        value: metric.value,
        rating: threshold ? this.getRating(metric.value, threshold) : 'unknown',
        delta: metric.delta,
        id: metric.id
      }
    })
    
    return report
  }
}

export const webVitalsOptimizer = new WebVitalsOptimizer()

// Initialize on app start
if (typeof window !== 'undefined') {
  webVitalsOptimizer.init()
}
```

### **Step 9: Advanced Image Optimization**

```typescript
// src/components/OptimizedImage.tsx
import React, { useState, useCallback, useRef } from 'react'

interface OptimizedImageProps {
  src: string
  alt: string
  width?: number
  height?: number
  className?: string
  loading?: 'lazy' | 'eager'
  priority?: boolean
}

export const OptimizedImage: React.FC<OptimizedImageProps> = ({
  src,
  alt,
  width,
  height,
  className = '',
  loading = 'lazy',
  priority = false
}) => {
  const [isLoaded, setIsLoaded] = useState(false)
  const [hasError, setHasError] = useState(false)
  const imgRef = useRef<HTMLImageElement>(null)
  
  // Generate responsive image URLs
  const generateSrcSet = useCallback((baseSrc: string) => {
    const sizes = [480, 768, 1024, 1280, 1920]
    return sizes
      .map(size => `${baseSrc}?w=${size}&q=80 ${size}w`)
      .join(', ')
  }, [])
  
  const handleLoad = useCallback(() => {
    setIsLoaded(true)
    
    // Measure LCP for above-the-fold images
    if (priority && 'PerformanceObserver' in window) {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries()
        entries.forEach((entry) => {
          if (entry.element === imgRef.current) {
            console.log(`🖼️ Image LCP: ${entry.startTime}ms`)
          }
        })
      })
      
      observer.observe({ entryTypes: ['largest-contentful-paint'] })
    }
  }, [priority])
  
  const handleError = useCallback(() => {
    setHasError(true)
  }, [])
  
  if (hasError) {
    return (
      <div className={`bg-gray-200 flex items-center justify-center ${className}`}>
        <span className="text-gray-500 text-sm">Failed to load image</span>
      </div>
    )
  }
  
  return (
    <div className={`relative ${className}`}>
      {/* Placeholder while loading */}
      {!isLoaded && (
        <div 
          className="absolute inset-0 bg-gray-200 animate-pulse"
          style={{ width, height }}
        />
      )}
      
      <img
        ref={imgRef}
        src={src}
        srcSet={generateSrcSet(src)}
        sizes="(max-width: 768px) 100vw, (max-width: 1024px) 50vw, 33vw"
        alt={alt}
        width={width}
        height={height}
        loading={loading}
        onLoad={handleLoad}
        onError={handleError}
        className={`transition-opacity duration-300 ${
          isLoaded ? 'opacity-100' : 'opacity-0'
        }`}
        decoding={priority ? 'sync' : 'async'}
      />
    </div>
  )
}
```

## 📊 **Performance Monitoring Dashboard**

```typescript
// src/components/PerformanceDashboard.tsx
import React, { useEffect, useState } from 'react'
import { webVitalsOptimizer } from '../utils/webVitalsOptimizer'
import { PerformanceMonitor } from '../utils/performanceMonitor'

export const PerformanceDashboard: React.FC = () => {
  const [vitals, setVitals] = useState<Record<string, any>>({})
  const [memoryInfo, setMemoryInfo] = useState<any>(null)
  
  useEffect(() => {
    // Update vitals every 5 seconds
    const interval = setInterval(() => {
      setVitals(webVitalsOptimizer.getReport())
      
      // Get memory info if available
      if ('memory' in performance) {
        const memory = (performance as any).memory
        setMemoryInfo({
          used: Math.round(memory.usedJSHeapSize / 1024 / 1024),
          total: Math.round(memory.totalJSHeapSize / 1024 / 1024),
          limit: Math.round(memory.jsHeapSizeLimit / 1024 / 1024),
        })
      }
    }, 5000)
    
    return () => clearInterval(interval)
  }, [])
  
  const getRatingColor = (rating: string) => {
    switch (rating) {
      case 'good': return 'text-green-600 bg-green-100'
      case 'needs-improvement': return 'text-yellow-600 bg-yellow-100'
      case 'poor': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }
  
  if (process.env.NODE_ENV !== 'development') {
    return null // Only show in development
  }
  
  return (
    <div className="fixed bottom-4 right-4 bg-white border border-gray-300 rounded-lg shadow-lg p-4 max-w-sm">
      <h3 className="font-semibold mb-3">Performance Monitor</h3>
      
      <div className="space-y-2 mb-4">
        {Object.entries(vitals).map(([name, data]) => (
          <div key={name} className="flex justify-between items-center">
            <span className="text-sm font-medium">{name}:</span>
            <span className={`px-2 py-1 rounded text-xs font-semibold ${getRatingColor(data.rating)}`}>
              {Math.round(data.value)}
            </span>
          </div>
        ))}
      </div>
      
      {memoryInfo && (
        <div className="border-t pt-2">
          <div className="text-sm font-medium mb-1">Memory Usage</div>
          <div className="text-xs text-gray-600">
            {memoryInfo.used} MB / {memoryInfo.total} MB
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
            <div 
              className="bg-blue-600 h-2 rounded-full"
              style={{ width: `${(memoryInfo.used / memoryInfo.limit) * 100}%` }}
            />
          </div>
        </div>
      )}
    </div>
  )
}
```

## 🎯 **Performance Testing Strategy**

### **Automated Performance Testing**

```bash
# package.json scripts
{
  "scripts": {
    "perf:lighthouse": "lighthouse --chrome-flags=\"--headless\" --output html --output-path ./reports/lighthouse.html http://localhost:5173",
    "perf:bundle": "npm run build && bundlesize",
    "perf:load": "k6 run scripts/load-test.js",
    "perf:audit": "npm run perf:lighthouse && npm run perf:bundle"
  }
}
```

```javascript
// scripts/load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 10 }, // Ramp up
    { duration: '5m', target: 50 }, // Stay at 50 users
    { duration: '2m', target: 0 },  // Ramp down
  ],
};

export default function() {
  const response = http.get('http://localhost:5173');
  
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
  
  sleep(1);
}
```

## 🎯 **Key Performance Targets**

### **Core Web Vitals Goals**
- **LCP (Largest Contentful Paint)**: < 2.5 seconds
- **FID (First Input Delay)**: < 100 milliseconds  
- **CLS (Cumulative Layout Shift)**: < 0.1

### **Bundle Size Targets**
- **Initial Bundle**: < 200KB gzipped
- **Vendor Chunk**: < 150KB gzipped
- **Route Chunks**: < 50KB gzipped each

### **Runtime Performance**
- **Time to Interactive**: < 3 seconds
- **Memory Usage**: < 50MB for typical session
- **Frame Rate**: > 55 FPS during interactions

## 🎯 **Key Takeaways**

1. **Measure before optimizing** - Use real data to guide decisions
2. **Bundle analysis is crucial** - Understand what's in your bundles
3. **Code splitting pays off** - Load only what's needed when needed
4. **Memoization prevents waste** - Cache expensive computations
5. **Virtual scrolling scales** - Handle large datasets efficiently
6. **Memory management matters** - Prevent leaks in long-running apps
7. **Web Vitals affect SEO** - Google uses these metrics for ranking

---

**Next**: [03-monitoring-and-analytics.md](./03-monitoring-and-analytics.md) - Production Monitoring Setup

**Previous**: [01-production-setup.md](./01-production-setup.md)