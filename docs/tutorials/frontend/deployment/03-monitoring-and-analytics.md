# Production Monitoring & Analytics: Complete Observability Setup

## 🎯 **What You'll Learn**

This comprehensive monitoring guide covers:
- Production error tracking and alerting with Sentry
- User analytics and behavior tracking 
- Performance monitoring and Core Web Vitals
- Real-time system health monitoring
- Custom metrics and business intelligence
- Log aggregation and analysis strategies

## 🔍 **Monitoring Architecture Overview**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React App     │───▶│   Sentry         │───▶│   Alerts        │
│                 │    │   Error Tracking │    │   Notifications │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Analytics     │───▶│   Data Warehouse │───▶│   Dashboards    │
│   Collection    │    │   (BigQuery)     │    │   (Grafana)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Performance   │───▶│   Time Series DB │───▶│   Alerts &      │
│   Metrics       │    │   (Prometheus)   │    │   Visualization │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚨 **Error Tracking with Sentry**

### **Step 1: Advanced Sentry Configuration**

```typescript
// src/utils/errorTracking.ts
import * as Sentry from '@sentry/react'
import { BrowserTracing } from '@sentry/tracing'
import { ENV } from '../config/environment'

// Custom error types for better categorization
export interface ApplicationError extends Error {
  category: 'network' | 'validation' | 'protocol' | 'ui' | 'performance'
  severity: 'low' | 'medium' | 'high' | 'critical'
  context?: Record<string, any>
  userId?: string
  sessionId?: string
}

class ErrorTrackingService {
  private initialized = false
  private sessionId = this.generateSessionId()
  
  init() {
    if (this.initialized || ENV.environment !== 'production') {
      return
    }
    
    Sentry.init({
      dsn: ENV.sentryDsn,
      environment: ENV.environment,
      release: ENV.version,
      
      integrations: [
        new BrowserTracing({
          // Automatic instrumentation
          routingInstrumentation: Sentry.reactRouterV6Instrumentation(
            React.useEffect,
            useLocation,
            useNavigationType,
            createRoutesFromChildren,
            matchRoutes
          ),
          
          // Track specific interactions
          tracingOrigins: [
            'localhost',
            ENV.apiUrl,
            /^\//  // Same-origin requests
          ],
        }),
        
        // Custom integration for React components
        new Sentry.Replay({
          maskAllText: true,
          maskAllInputs: true,
          blockAllMedia: true,
        }),
      ],
      
      // Performance monitoring
      tracesSampleRate: ENV.environment === 'production' ? 0.1 : 1.0,
      
      // Session replay sampling
      replaysSessionSampleRate: 0.1,
      replaysOnErrorSampleRate: 1.0,
      
      // Error filtering and sampling
      beforeSend(event, hint) {
        return this.filterError(event, hint)
      },
      
      // Performance event filtering
      beforeSendTransaction(event) {
        return this.filterTransaction(event)
      },
      
      // Initial context
      initialScope: {
        tags: {
          version: ENV.version,
          buildDate: ENV.buildDate,
          sessionId: this.sessionId,
        },
        level: 'info',
      },
      
      // Transport options for reliability
      transport: Sentry.makeBrowserOfflineTransport(Sentry.makeFetchTransport),
      transportOptions: {
        maxQueueLength: 100,
      },
    })
    
    // Set up global error handlers
    this.setupGlobalHandlers()
    this.initialized = true
  }
  
  private filterError(event: Sentry.Event, hint: Sentry.EventHint): Sentry.Event | null {
    const error = hint.originalException
    
    // Skip network errors we can't control
    if (error instanceof Error) {
      if (error.message.includes('NetworkError') || 
          error.message.includes('ERR_INTERNET_DISCONNECTED') ||
          error.message.includes('ERR_NETWORK')) {
        return null
      }
      
      // Skip browser extension errors
      if (error.stack?.includes('extension://') || 
          error.stack?.includes('moz-extension://')) {
        return null
      }
      
      // Skip known third-party script errors
      if (error.stack?.includes('googletagmanager') ||
          error.stack?.includes('facebook.net') ||
          error.stack?.includes('google-analytics')) {
        return null
      }
    }
    
    // Add custom fingerprinting for better grouping
    if (event.exception?.values?.[0]) {
      const exception = event.exception.values[0]
      if (exception.type === 'ChunkLoadError') {
        event.fingerprint = ['chunk-load-error']
      } else if (exception.value?.includes('Loading CSS chunk')) {
        event.fingerprint = ['css-chunk-error']
      }
    }
    
    return event
  }
  
  private filterTransaction(event: Sentry.Transaction): Sentry.Transaction | null {
    // Skip very short transactions
    if (event.spans && event.spans.length === 0 && (event.timestamp - event.start_timestamp) < 0.1) {
      return null
    }
    
    // Skip health check requests
    if (event.transaction?.includes('/health')) {
      return null
    }
    
    return event
  }
  
  private setupGlobalHandlers() {
    // Unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.captureError(new Error(`Unhandled Promise Rejection: ${event.reason}`), {
        category: 'network',
        severity: 'medium',
        context: { reason: event.reason }
      })
    })
    
    // Resource loading errors
    window.addEventListener('error', (event) => {
      if (event.target !== window) {
        this.captureError(new Error(`Resource loading error: ${event.target?.src || 'unknown'}`), {
          category: 'ui',
          severity: 'low',
          context: { 
            source: event.target?.src,
            type: event.target?.tagName 
          }
        })
      }
    }, true)
  }
  
  captureError(error: Error | ApplicationError, additionalContext?: Record<string, any>) {
    if (!this.initialized) return
    
    const isAppError = 'category' in error
    const category = isAppError ? error.category : 'unknown'
    const severity = isAppError ? error.severity : 'medium'
    
    Sentry.withScope((scope) => {
      scope.setTag('error.category', category)
      scope.setLevel(this.mapSeverityToLevel(severity))
      scope.setContext('error_details', {
        category,
        severity,
        sessionId: this.sessionId,
        timestamp: new Date().toISOString(),
        ...additionalContext,
        ...(isAppError ? error.context : {})
      })
      
      if (isAppError && error.userId) {
        scope.setUser({ id: error.userId })
      }
      
      Sentry.captureException(error)
    })
  }
  
  captureMessage(message: string, level: 'info' | 'warning' | 'error' = 'info', context?: Record<string, any>) {
    if (!this.initialized) return
    
    Sentry.withScope((scope) => {
      if (context) {
        scope.setContext('message_context', context)
      }
      scope.setTag('sessionId', this.sessionId)
      
      Sentry.captureMessage(message, level)
    })
  }
  
  setUserContext(userId: string, email?: string, username?: string) {
    if (!this.initialized) return
    
    Sentry.setUser({
      id: userId,
      email,
      username,
    })
  }
  
  addBreadcrumb(message: string, category: string, data?: Record<string, any>) {
    if (!this.initialized) return
    
    Sentry.addBreadcrumb({
      message,
      category,
      level: 'info',
      data,
      timestamp: Date.now() / 1000,
    })
  }
  
  private mapSeverityToLevel(severity: string): Sentry.SeverityLevel {
    switch (severity) {
      case 'low': return 'info'
      case 'medium': return 'warning'
      case 'high': return 'error'
      case 'critical': return 'fatal'
      default: return 'error'
    }
  }
  
  private generateSessionId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }
}

export const errorTracker = new ErrorTrackingService()
```

### **Step 2: React Error Boundaries with Sentry**

```typescript
// src/components/ErrorBoundary.tsx
import React, { Component, ErrorInfo, ReactNode } from 'react'
import { errorTracker } from '../utils/errorTracking'
import { AlertTriangle, RefreshCw, Home } from 'lucide-react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  level?: 'page' | 'component' | 'critical'
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
  eventId: string | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      eventId: null,
    }
  }
  
  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
    }
  }
  
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error boundary caught error:', error, errorInfo)
    
    // Capture error with Sentry
    const eventId = errorTracker.captureError({
      ...error,
      category: 'ui',
      severity: this.props.level === 'critical' ? 'critical' : 'high',
      context: {
        errorInfo,
        boundaryLevel: this.props.level,
        componentStack: errorInfo.componentStack,
      }
    } as any, {
      react_error_boundary: true,
      error_boundary_level: this.props.level,
    })
    
    this.setState({
      errorInfo,
      eventId: eventId || null,
    })
  }
  
  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      eventId: null,
    })
    
    errorTracker.addBreadcrumb(
      'User clicked retry after error',
      'ui',
      { boundaryLevel: this.props.level }
    )
  }
  
  handleGoHome = () => {
    window.location.href = '/'
  }
  
  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }
      
      const isComponentLevel = this.props.level === 'component'
      
      return (
        <div className={`${isComponentLevel ? 'p-4' : 'min-h-screen flex items-center justify-center'} bg-red-50`}>
          <div className="text-center max-w-md mx-auto">
            <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" />
            
            <h2 className={`${isComponentLevel ? 'text-lg' : 'text-2xl'} font-bold text-red-800 mb-2`}>
              {isComponentLevel ? 'Component Error' : 'Something went wrong'}
            </h2>
            
            <p className="text-red-600 mb-6">
              {isComponentLevel 
                ? 'This component encountered an error and couldn\'t render properly.'
                : 'We apologize for the inconvenience. Our team has been notified.'
              }
            </p>
            
            {process.env.NODE_ENV === 'development' && (
              <details className="mb-6 text-left bg-gray-100 p-4 rounded">
                <summary className="cursor-pointer font-semibold">Error Details</summary>
                <pre className="mt-2 text-sm overflow-auto">
                  {this.state.error?.toString()}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </details>
            )}
            
            <div className="flex gap-3 justify-center">
              <button
                onClick={this.handleRetry}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
              >
                <RefreshCw className="w-4 h-4" />
                Try Again
              </button>
              
              {!isComponentLevel && (
                <button
                  onClick={this.handleGoHome}
                  className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                >
                  <Home className="w-4 h-4" />
                  Go Home
                </button>
              )}
            </div>
            
            {this.state.eventId && (
              <p className="mt-4 text-sm text-gray-500">
                Error ID: {this.state.eventId}
              </p>
            )}
          </div>
        </div>
      )
    }
    
    return this.props.children
  }
}
```

## 📊 **User Analytics Implementation**

### **Step 3: Custom Analytics Service**

```typescript
// src/utils/analytics.ts
interface AnalyticsEvent {
  name: string
  properties?: Record<string, any>
  userId?: string
  sessionId?: string
  timestamp?: number
}

interface UserProperties {
  userId?: string
  email?: string
  plan?: string
  signupDate?: string
  [key: string]: any
}

class AnalyticsService {
  private queue: AnalyticsEvent[] = []
  private userId: string | null = null
  private sessionId: string
  private isInitialized = false
  private flushTimer: number | null = null
  
  constructor() {
    this.sessionId = this.generateSessionId()
    this.setupBeforeUnloadHandler()
  }
  
  init() {
    if (this.isInitialized) return
    
    // Initialize Google Analytics 4
    if (ENV.enableAnalytics && ENV.gaTrackingId) {
      this.initializeGA4()
    }
    
    // Initialize custom analytics
    this.isInitialized = true
    this.startPeriodicFlush()
    
    // Track page view
    this.track('page_view', {
      page: window.location.pathname,
      referrer: document.referrer,
    })
  }
  
  private initializeGA4() {
    // Load GA4 script
    const script = document.createElement('script')
    script.async = true
    script.src = `https://www.googletagmanager.com/gtag/js?id=${ENV.gaTrackingId}`
    document.head.appendChild(script)
    
    // Configure GA4
    window.gtag = window.gtag || function() {
      (window.gtag.q = window.gtag.q || []).push(arguments)
    }
    window.gtag.l = Date.now()
    
    window.gtag('config', ENV.gaTrackingId, {
      send_page_view: false, // We'll send manually
      session_id: this.sessionId,
    })
  }
  
  identify(userId: string, properties?: UserProperties) {
    this.userId = userId
    
    // Set user properties in GA4
    if (window.gtag) {
      window.gtag('config', ENV.gaTrackingId, {
        user_id: userId,
        custom_map: { user_plan: 'plan' }
      })
      
      if (properties) {
        window.gtag('event', 'user_properties', properties)
      }
    }
    
    // Update Sentry user context
    errorTracker.setUserContext(userId, properties?.email, properties?.email)
  }
  
  track(eventName: string, properties?: Record<string, any>) {
    const event: AnalyticsEvent = {
      name: eventName,
      properties: {
        ...properties,
        session_id: this.sessionId,
        timestamp: Date.now(),
        page: window.location.pathname,
        user_agent: navigator.userAgent,
      },
      userId: this.userId || undefined,
      sessionId: this.sessionId,
      timestamp: Date.now(),
    }
    
    // Queue event for batch processing
    this.queue.push(event)
    
    // Send to GA4 immediately
    if (window.gtag) {
      window.gtag('event', eventName, {
        ...properties,
        session_id: this.sessionId,
        user_id: this.userId,
      })
    }
    
    // Add breadcrumb to Sentry
    errorTracker.addBreadcrumb(
      `User action: ${eventName}`,
      'user',
      properties
    )
    
    // Flush if queue is getting large
    if (this.queue.length >= 10) {
      this.flush()
    }
  }
  
  page(pageName: string, properties?: Record<string, any>) {
    this.track('page_view', {
      page_name: pageName,
      ...properties,
    })
    
    // Send page view to GA4
    if (window.gtag) {
      window.gtag('config', ENV.gaTrackingId, {
        page_title: document.title,
        page_location: window.location.href,
        ...properties,
      })
    }
  }
  
  // Business-specific tracking methods
  trackAgentInteraction(agentId: string, action: 'query' | 'retry' | 'copy', query?: string) {
    this.track('agent_interaction', {
      agent_id: agentId,
      action,
      query_length: query?.length,
      has_query: !!query,
    })
  }
  
  trackStreamingSession(data: {
    duration: number
    messageCount: number
    protocolsUsed: string[]
    errors: number
  }) {
    this.track('streaming_session', {
      session_duration: data.duration,
      message_count: data.messageCount,
      protocols_used: data.protocolsUsed.join(','),
      error_count: data.errors,
    })
  }
  
  trackPerformance(metric: string, value: number, context?: Record<string, any>) {
    this.track('performance_metric', {
      metric_name: metric,
      metric_value: value,
      ...context,
    })
  }
  
  private async flush() {
    if (this.queue.length === 0) return
    
    const events = [...this.queue]
    this.queue = []
    
    try {
      // Send to custom analytics endpoint
      if (ENV.analyticsEndpoint) {
        await fetch(ENV.analyticsEndpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            events,
            client_id: this.sessionId,
            timestamp: Date.now(),
          }),
        })
      }
      
      console.log(`📊 Flushed ${events.length} analytics events`)
    } catch (error) {
      console.warn('Failed to flush analytics events:', error)
      // Re-queue events for retry
      this.queue = [...events, ...this.queue]
    }
  }
  
  private startPeriodicFlush() {
    this.flushTimer = window.setInterval(() => {
      this.flush()
    }, 30000) // Flush every 30 seconds
  }
  
  private setupBeforeUnloadHandler() {
    window.addEventListener('beforeunload', () => {
      // Synchronous flush on page unload
      if (this.queue.length > 0) {
        navigator.sendBeacon(
          ENV.analyticsEndpoint || '/api/analytics',
          JSON.stringify({
            events: this.queue,
            client_id: this.sessionId,
            timestamp: Date.now(),
          })
        )
      }
    })
  }
  
  private generateSessionId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }
}

export const analytics = new AnalyticsService()
```

### **Step 4: React Hooks for Analytics**

```typescript
// src/hooks/useAnalytics.ts
import { useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'
import { analytics } from '../utils/analytics'

export const usePageTracking = () => {
  const location = useLocation()
  const previousPath = useRef<string>()
  
  useEffect(() => {
    const currentPath = location.pathname + location.search
    
    // Don't track the first page view (handled by init)
    if (previousPath.current !== undefined) {
      analytics.page(currentPath, {
        previous_page: previousPath.current,
        search_params: Object.fromEntries(new URLSearchParams(location.search))
      })
    }
    
    previousPath.current = currentPath
  }, [location])
}

export const useInteractionTracking = () => {
  const trackClick = (elementName: string, properties?: Record<string, any>) => {
    analytics.track('click', {
      element: elementName,
      ...properties,
    })
  }
  
  const trackFormSubmit = (formName: string, success: boolean, properties?: Record<string, any>) => {
    analytics.track('form_submit', {
      form_name: formName,
      success,
      ...properties,
    })
  }
  
  const trackSearch = (query: string, results: number, category?: string) => {
    analytics.track('search', {
      query_length: query.length,
      results_count: results,
      category,
    })
  }
  
  return {
    trackClick,
    trackFormSubmit,
    trackSearch,
  }
}

export const usePerformanceTracking = () => {
  const trackTiming = (name: string, startTime: number, endTime?: number) => {
    const duration = (endTime || performance.now()) - startTime
    analytics.trackPerformance(name, duration)
  }
  
  const trackComponentMount = (componentName: string) => {
    const startTime = performance.now()
    
    return () => {
      const mountDuration = performance.now() - startTime
      analytics.trackPerformance('component_mount', mountDuration, {
        component_name: componentName,
      })
    }
  }
  
  return {
    trackTiming,
    trackComponentMount,
  }
}
```

## 📈 **Performance Monitoring**

### **Step 5: Real User Monitoring (RUM)**

```typescript
// src/utils/performanceMonitoring.ts
import { getCLS, getFID, getFCP, getLCP, getTTFB, Metric } from 'web-vitals'
import { analytics } from './analytics'

interface PerformanceConfig {
  sampleRate: number
  enableLongTasks: boolean
  enableResourceTiming: boolean
  enableNavigationTiming: boolean
}

class PerformanceMonitoringService {
  private config: PerformanceConfig
  private observer: PerformanceObserver | null = null
  private vitalsData: Map<string, Metric> = new Map()
  
  constructor(config: Partial<PerformanceConfig> = {}) {
    this.config = {
      sampleRate: 0.1, // 10% of users
      enableLongTasks: true,
      enableResourceTiming: true,
      enableNavigationTiming: true,
      ...config,
    }
  }
  
  init() {
    // Only monitor a sample of users to reduce data volume
    if (Math.random() > this.config.sampleRate) {
      return
    }
    
    this.setupWebVitals()
    this.setupLongTaskMonitoring()
    this.setupResourceTimingMonitoring()
    this.setupNavigationTimingMonitoring()
    this.setupMemoryMonitoring()
  }
  
  private setupWebVitals() {
    const handleVital = (metric: Metric) => {
      this.vitalsData.set(metric.name, metric)
      
      // Track in analytics
      analytics.trackPerformance(`web_vital_${metric.name.toLowerCase()}`, metric.value, {
        rating: this.getVitalRating(metric.name, metric.value),
        delta: metric.delta,
        id: metric.id,
      })
      
      // Track in Sentry as measurement
      if (window.Sentry) {
        window.Sentry.setMeasurement(metric.name, metric.value, 'millisecond')
      }
    }
    
    getCLS(handleVital)
    getFID(handleVital)
    getFCP(handleVital)
    getLCP(handleVital)
    getTTFB(handleVital)
  }
  
  private setupLongTaskMonitoring() {
    if (!this.config.enableLongTasks || !('PerformanceObserver' in window)) {
      return
    }
    
    try {
      this.observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === 'longtask') {
            const duration = entry.duration
            
            // Track long tasks that block the main thread
            if (duration > 50) { // Tasks longer than 50ms
              analytics.trackPerformance('long_task', duration, {
                entry_type: entry.entryType,
                start_time: entry.startTime,
              })
              
              // Report to Sentry as performance issue
              if (window.Sentry && duration > 100) {
                window.Sentry.captureMessage(
                  `Long task detected: ${duration}ms`,
                  'warning'
                )
              }
            }
          }
        }
      })
      
      this.observer.observe({ entryTypes: ['longtask'] })
    } catch (error) {
      console.warn('Long task monitoring not supported:', error)
    }
  }
  
  private setupResourceTimingMonitoring() {
    if (!this.config.enableResourceTiming || !('PerformanceObserver' in window)) {
      return
    }
    
    const resourceObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        const resource = entry as PerformanceResourceTiming
        
        // Track slow resources
        const duration = resource.responseEnd - resource.requestStart
        if (duration > 1000) { // Resources taking more than 1 second
          analytics.trackPerformance('slow_resource', duration, {
            resource_name: resource.name,
            resource_type: this.getResourceType(resource.name),
            transfer_size: resource.transferSize,
          })
        }
        
        // Track failed resources
        if (resource.transferSize === 0 && duration > 0) {
          analytics.track('resource_error', {
            resource_name: resource.name,
            resource_type: this.getResourceType(resource.name),
          })
        }
      }
    })
    
    resourceObserver.observe({ entryTypes: ['resource'] })
  }
  
  private setupNavigationTimingMonitoring() {
    if (!this.config.enableNavigationTiming) return
    
    window.addEventListener('load', () => {
      setTimeout(() => {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
        
        if (navigation) {
          const timings = {
            dns_lookup: navigation.domainLookupEnd - navigation.domainLookupStart,
            tcp_connect: navigation.connectEnd - navigation.connectStart,
            ssl_negotiate: navigation.secureConnectionStart ? navigation.connectEnd - navigation.secureConnectionStart : 0,
            request: navigation.responseStart - navigation.requestStart,
            response: navigation.responseEnd - navigation.responseStart,
            dom_processing: navigation.domContentLoadedEventStart - navigation.responseEnd,
            load_complete: navigation.loadEventEnd - navigation.loadEventStart,
            total_load: navigation.loadEventEnd - navigation.navigationStart,
          }
          
          Object.entries(timings).forEach(([name, value]) => {
            analytics.trackPerformance(`navigation_${name}`, value)
          })
        }
      }, 0)
    })
  }
  
  private setupMemoryMonitoring() {
    if (!('memory' in performance)) return
    
    setInterval(() => {
      const memory = (performance as any).memory
      const usedMB = memory.usedJSHeapSize / 1024 / 1024
      const totalMB = memory.totalJSHeapSize / 1024 / 1024
      
      analytics.trackPerformance('memory_usage', usedMB, {
        total_memory: totalMB,
        usage_percentage: (usedMB / totalMB) * 100,
      })
      
      // Alert on high memory usage
      if (usedMB > 100) { // More than 100MB
        analytics.track('high_memory_usage', {
          memory_used: usedMB,
          memory_total: totalMB,
        })
      }
    }, 60000) // Check every minute
  }
  
  private getVitalRating(name: string, value: number): 'good' | 'needs-improvement' | 'poor' {
    const thresholds: Record<string, { good: number; poor: number }> = {
      CLS: { good: 0.1, poor: 0.25 },
      FID: { good: 100, poor: 300 },
      FCP: { good: 1800, poor: 3000 },
      LCP: { good: 2500, poor: 4000 },
      TTFB: { good: 800, poor: 1800 },
    }
    
    const threshold = thresholds[name]
    if (!threshold) return 'good'
    
    if (value <= threshold.good) return 'good'
    if (value <= threshold.poor) return 'needs-improvement'
    return 'poor'
  }
  
  private getResourceType(url: string): string {
    if (url.match(/\.(js|jsx|ts|tsx)$/)) return 'script'
    if (url.match(/\.(css|scss|sass)$/)) return 'style'
    if (url.match(/\.(png|jpg|jpeg|gif|svg|webp)$/)) return 'image'
    if (url.match(/\.(woff|woff2|ttf|eot)$/)) return 'font'
    if (url.includes('/api/')) return 'api'
    return 'other'
  }
  
  getVitalsReport() {
    const report: Record<string, any> = {}
    this.vitalsData.forEach((metric, name) => {
      report[name] = {
        value: metric.value,
        rating: this.getVitalRating(name, metric.value),
        delta: metric.delta,
      }
    })
    return report
  }
}

export const performanceMonitor = new PerformanceMonitoringService()
```

## 🏥 **Health Monitoring Dashboard**

### **Step 6: System Health Component**

```typescript
// src/components/SystemHealthDashboard.tsx
import React, { useState, useEffect } from 'react'
import { Activity, AlertTriangle, CheckCircle, Clock, Cpu, MemoryStick } from 'lucide-react'
import { performanceMonitor } from '../utils/performanceMonitoring'
import { useOrchestrator } from '../hooks/useOrchestrator'

interface HealthMetric {
  name: string
  value: number | string
  status: 'good' | 'warning' | 'error'
  threshold?: number
  unit?: string
}

export const SystemHealthDashboard: React.FC = () => {
  const [healthMetrics, setHealthMetrics] = useState<HealthMetric[]>([])
  const [webVitals, setWebVitals] = useState<Record<string, any>>({})
  const { isHealthy, agents, stats, getHealthSummary } = useOrchestrator()
  
  useEffect(() => {
    const updateMetrics = () => {
      const vitals = performanceMonitor.getVitalsReport()
      setWebVitals(vitals)
      
      const memory = ('memory' in performance) 
        ? (performance as any).memory 
        : null
      
      const metrics: HealthMetric[] = [
        {
          name: 'API Health',
          value: isHealthy ? 'Healthy' : 'Unhealthy',
          status: isHealthy ? 'good' : 'error',
        },
        {
          name: 'Active Agents',
          value: agents.filter(a => a.status === 'healthy').length,
          status: agents.length > 0 ? 'good' : 'warning',
        },
        {
          name: 'API Success Rate',
          value: stats.totalRequests > 0 
            ? ((stats.successfulRequests / stats.totalRequests) * 100).toFixed(1)
            : '100.0',
          status: (stats.successfulRequests / Math.max(stats.totalRequests, 1)) > 0.95 
            ? 'good' 
            : (stats.successfulRequests / Math.max(stats.totalRequests, 1)) > 0.8 
              ? 'warning' 
              : 'error',
          unit: '%',
        },
        {
          name: 'Avg Response Time',
          value: Math.round(stats.averageResponseTime),
          status: stats.averageResponseTime < 500 
            ? 'good' 
            : stats.averageResponseTime < 1000 
              ? 'warning' 
              : 'error',
          threshold: 500,
          unit: 'ms',
        },
      ]
      
      // Add memory metrics if available
      if (memory) {
        const usedMB = Math.round(memory.usedJSHeapSize / 1024 / 1024)
        metrics.push({
          name: 'Memory Usage',
          value: usedMB,
          status: usedMB < 50 ? 'good' : usedMB < 100 ? 'warning' : 'error',
          threshold: 50,
          unit: 'MB',
        })
      }
      
      // Add Web Vitals
      Object.entries(vitals).forEach(([name, data]) => {
        metrics.push({
          name: `${name} Score`,
          value: Math.round(data.value),
          status: data.rating === 'good' ? 'good' : 
                  data.rating === 'needs-improvement' ? 'warning' : 'error',
          unit: name === 'CLS' ? '' : 'ms',
        })
      })
      
      setHealthMetrics(metrics)
    }
    
    // Update immediately
    updateMetrics()
    
    // Update every 30 seconds
    const interval = setInterval(updateMetrics, 30000)
    return () => clearInterval(interval)
  }, [isHealthy, agents, stats])
  
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'good': return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'warning': return <AlertTriangle className="w-5 h-5 text-yellow-600" />
      case 'error': return <AlertTriangle className="w-5 h-5 text-red-600" />
      default: return <Activity className="w-5 h-5 text-gray-600" />
    }
  }
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good': return 'border-green-200 bg-green-50'
      case 'warning': return 'border-yellow-200 bg-yellow-50'
      case 'error': return 'border-red-200 bg-red-50'
      default: return 'border-gray-200 bg-gray-50'
    }
  }
  
  return (
    <div className="system-health-dashboard p-6">
      <div className="flex items-center gap-2 mb-6">
        <Activity className="w-6 h-6 text-blue-600" />
        <h2 className="text-2xl font-bold text-gray-900">System Health</h2>
      </div>
      
      {/* Health Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-8">
        {healthMetrics.map((metric, index) => (
          <div 
            key={index}
            className={`p-4 rounded-lg border-2 ${getStatusColor(metric.status)}`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">
                {metric.name}
              </span>
              {getStatusIcon(metric.status)}
            </div>
            
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold text-gray-900">
                {metric.value}
              </span>
              {metric.unit && (
                <span className="text-sm text-gray-500">{metric.unit}</span>
              )}
            </div>
            
            {metric.threshold && (
              <div className="mt-1 text-xs text-gray-500">
                Target: &lt; {metric.threshold}{metric.unit}
              </div>
            )}
          </div>
        ))}
      </div>
      
      {/* Agent Status */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">Agent Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <div key={agent.agent_id} className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg">
              <div className={`w-3 h-3 rounded-full ${
                agent.status === 'healthy' ? 'bg-green-400' :
                agent.status === 'degraded' ? 'bg-yellow-400' :
                'bg-red-400'
              }`} />
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 truncate">{agent.name}</p>
                <p className="text-sm text-gray-500">{agent.protocol.toUpperCase()}</p>
              </div>
              <span className={`px-2 py-1 text-xs rounded-full ${
                agent.status === 'healthy' ? 'bg-green-100 text-green-800' :
                agent.status === 'degraded' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }`}>
                {agent.status}
              </span>
            </div>
          ))}
        </div>
      </div>
      
      {/* Performance Chart Placeholder */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4">Performance Trends</h3>
        <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
          <div className="text-center text-gray-500">
            <Cpu className="w-12 h-12 mx-auto mb-2" />
            <p>Performance charts would be displayed here</p>
            <p className="text-sm">Integration with Grafana or similar tool recommended</p>
          </div>
        </div>
      </div>
    </div>
  )
}
```

## 🔍 **Log Aggregation Strategy**

### **Step 7: Structured Logging**

```typescript
// src/utils/logger.ts
export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
  FATAL = 4,
}

interface LogEntry {
  timestamp: string
  level: LogLevel
  message: string
  context?: Record<string, any>
  userId?: string
  sessionId?: string
  requestId?: string
  component?: string
  action?: string
  error?: {
    name: string
    message: string
    stack?: string
  }
}

class StructuredLogger {
  private sessionId: string
  private userId?: string
  private logQueue: LogEntry[] = []
  private readonly maxQueueSize = 100
  
  constructor() {
    this.sessionId = this.generateSessionId()
    this.setupConsoleInterception()
  }
  
  setUserId(userId: string) {
    this.userId = userId
  }
  
  debug(message: string, context?: Record<string, any>) {
    this.log(LogLevel.DEBUG, message, context)
  }
  
  info(message: string, context?: Record<string, any>) {
    this.log(LogLevel.INFO, message, context)
  }
  
  warn(message: string, context?: Record<string, any>) {
    this.log(LogLevel.WARN, message, context)
  }
  
  error(message: string, error?: Error, context?: Record<string, any>) {
    this.log(LogLevel.ERROR, message, {
      ...context,
      error: error ? {
        name: error.name,
        message: error.message,
        stack: error.stack,
      } : undefined,
    })
  }
  
  fatal(message: string, error?: Error, context?: Record<string, any>) {
    this.log(LogLevel.FATAL, message, {
      ...context,
      error: error ? {
        name: error.name,
        message: error.message,
        stack: error.stack,
      } : undefined,
    })
  }
  
  private log(level: LogLevel, message: string, context?: Record<string, any>) {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      context,
      userId: this.userId,
      sessionId: this.sessionId,
    }
    
    // Add to queue
    this.logQueue.push(entry)
    
    // Trim queue if too large
    if (this.logQueue.length > this.maxQueueSize) {
      this.logQueue.shift()
    }
    
    // Console output for development
    if (process.env.NODE_ENV === 'development') {
      const consoleMethod = this.getConsoleMethod(level)
      consoleMethod(`[${LogLevel[level]}] ${message}`, context)
    }
    
    // Send critical logs immediately
    if (level >= LogLevel.ERROR) {
      this.flush()
    }
  }
  
  private setupConsoleInterception() {
    // Intercept console errors for automatic logging
    const originalError = console.error
    console.error = (...args) => {
      this.error('Console error', new Error(args.join(' ')))
      originalError.apply(console, args)
    }
    
    // Intercept unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.error(
        'Unhandled promise rejection',
        event.reason instanceof Error ? event.reason : new Error(String(event.reason))
      )
    })
  }
  
  private getConsoleMethod(level: LogLevel) {
    switch (level) {
      case LogLevel.DEBUG: return console.debug
      case LogLevel.INFO: return console.info
      case LogLevel.WARN: return console.warn
      case LogLevel.ERROR:
      case LogLevel.FATAL:
        return console.error
      default: return console.log
    }
  }
  
  async flush() {
    if (this.logQueue.length === 0) return
    
    const logs = [...this.logQueue]
    this.logQueue = []
    
    try {
      if (ENV.logsEndpoint) {
        await fetch(ENV.logsEndpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            logs,
            client_info: {
              user_agent: navigator.userAgent,
              url: window.location.href,
              timestamp: new Date().toISOString(),
            },
          }),
        })
      }
    } catch (error) {
      console.warn('Failed to flush logs:', error)
      // Re-queue logs for retry
      this.logQueue = [...logs, ...this.logQueue]
    }
  }
  
  private generateSessionId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }
}

export const logger = new StructuredLogger()
```

## 🎯 **Key Takeaways**

1. **Error tracking is essential** - Catch and categorize all errors
2. **Analytics drive decisions** - Track user behavior and performance 
3. **Performance affects users** - Monitor Core Web Vitals religiously
4. **Structured logging helps debugging** - Consistent log format is crucial
5. **Dashboards provide visibility** - Real-time monitoring prevents issues
6. **Sampling reduces costs** - Monitor percentage of users, not all
7. **Context is everything** - Include relevant metadata with all events

---

**Next**: Complete deployment tutorial series

**Previous**: [02-performance-optimization.md](./02-performance-optimization.md)