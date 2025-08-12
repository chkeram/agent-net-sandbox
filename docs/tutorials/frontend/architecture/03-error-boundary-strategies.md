# Architecture 3: Error Boundary Strategies - Comprehensive Error Handling Architecture

## 🎯 **Learning Objectives**

By the end of this tutorial, you will understand:
- Advanced error boundary patterns for React applications
- How to design resilient error handling that prevents application crashes
- Strategies for error recovery and graceful degradation
- Error reporting and monitoring architecture
- Context-aware error boundaries that provide meaningful user feedback
- Performance monitoring and error analytics integration

## 🛡️ **The Error Boundary Challenge**

Production React applications need bulletproof error handling:
- **Component Errors**: JavaScript errors in render methods, lifecycle, or hooks
- **Async Errors**: Promise rejections, network failures, streaming errors
- **Third-party Integration Errors**: External library failures
- **User Input Errors**: Invalid data causing component failures
- **Memory Pressure**: Out-of-memory errors in large applications
- **Browser Compatibility**: Different error patterns across browsers

**Our goal**: Build **comprehensive error boundaries** that maintain application stability while providing meaningful user feedback and developer insights.

## 🏗️ **Error Boundary Architecture**

### **Hierarchical Error Boundary Design**

```typescript
// src/types/errorBoundary.ts

export interface ErrorInfo {
  componentStack: string
  errorBoundary?: string
  errorBoundaryStack?: string
}

export interface AppError {
  id: string
  message: string
  stack?: string
  name: string
  timestamp: Date
  
  // Context information
  component?: string
  props?: Record<string, any>
  state?: Record<string, any>
  userAgent: string
  url: string
  
  // Error classification
  severity: 'low' | 'medium' | 'high' | 'critical'
  category: 'render' | 'async' | 'network' | 'user_input' | 'third_party' | 'unknown'
  recoverable: boolean
  
  // User context
  userId?: string
  sessionId: string
  
  // Additional context
  breadcrumbs: Breadcrumb[]
  tags: Record<string, string>
  extra: Record<string, any>
}

export interface Breadcrumb {
  timestamp: Date
  message: string
  category: string
  level: 'info' | 'warning' | 'error'
  data?: Record<string, any>
}

export interface ErrorBoundaryState {
  hasError: boolean
  error: AppError | null
  errorId: string | null
  retryCount: number
  canRetry: boolean
  fallbackComponent?: React.ComponentType<any>
}

export interface ErrorRecoveryStrategy {
  type: 'retry' | 'fallback' | 'redirect' | 'reload' | 'ignore'
  maxRetries?: number
  retryDelay?: number
  fallbackComponent?: React.ComponentType<any>
  redirectUrl?: string
  condition?: (error: AppError) => boolean
}
```

### **Base Error Boundary Implementation**

```typescript
// src/components/ErrorBoundary/BaseErrorBoundary.tsx
import React, { ErrorInfo, ReactNode } from 'react'
import { errorReporting } from '../../services/errorReporting'
import { ErrorLogger } from '../../services/errorLogger'

interface BaseErrorBoundaryProps {
  children: ReactNode
  fallback?: React.ComponentType<ErrorFallbackProps>
  onError?: (error: AppError) => void
  level: 'app' | 'page' | 'section' | 'component'
  context?: Record<string, any>
  recoveryStrategies?: ErrorRecoveryStrategy[]
  enableRetry?: boolean
  maxRetries?: number
  resetOnPropsChange?: boolean
}

interface ErrorFallbackProps {
  error: AppError
  retry: () => void
  canRetry: boolean
  retryCount: number
  level: string
}

export class BaseErrorBoundary extends React.Component<
  BaseErrorBoundaryProps,
  ErrorBoundaryState
> {
  private errorLogger: ErrorLogger
  private retryTimeout?: NodeJS.Timeout
  private breadcrumbs: Breadcrumb[] = []
  
  constructor(props: BaseErrorBoundaryProps) {
    super(props)
    
    this.state = {
      hasError: false,
      error: null,
      errorId: null,
      retryCount: 0,
      canRetry: props.enableRetry !== false,
      fallbackComponent: props.fallback,
    }
    
    this.errorLogger = new ErrorLogger({
      level: props.level,
      context: props.context,
    })
  }
  
  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      errorId: `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    }
  }
  
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const appError = this.createAppError(error, errorInfo)
    
    this.setState({ error: appError })
    
    // Log error
    this.errorLogger.logError(appError)
    
    // Report to external service
    errorReporting.reportError(appError)
    
    // Call custom error handler
    this.props.onError?.(appError)
    
    // Add to breadcrumbs for future errors
    this.addBreadcrumb({
      message: `Error boundary caught: ${error.message}`,
      category: 'error',
      level: 'error',
      data: { component: errorInfo.componentStack?.split('\n')[1]?.trim() },
    })
  }
  
  componentDidUpdate(prevProps: BaseErrorBoundaryProps) {
    const { resetOnPropsChange } = this.props
    const { hasError } = this.state
    
    // Reset error boundary if props change and resetOnPropsChange is enabled
    if (hasError && resetOnPropsChange && prevProps.children !== this.props.children) {
      this.resetErrorBoundary()
    }
  }
  
  componentWillUnmount() {
    if (this.retryTimeout) {
      clearTimeout(this.retryTimeout)
    }
  }
  
  private createAppError(error: Error, errorInfo: ErrorInfo): AppError {
    return {
      id: this.state.errorId || 'unknown',
      message: error.message,
      stack: error.stack,
      name: error.name,
      timestamp: new Date(),
      
      // Context
      component: errorInfo.componentStack?.split('\n')[1]?.trim(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      
      // Classification
      severity: this.classifyErrorSeverity(error),
      category: this.classifyErrorCategory(error),
      recoverable: this.isRecoverable(error),
      
      // Session info
      sessionId: this.getSessionId(),
      
      // Breadcrumbs and context
      breadcrumbs: [...this.breadcrumbs],
      tags: {
        level: this.props.level,
        boundary: this.constructor.name,
      },
      extra: {
        ...this.props.context,
        errorInfo,
        retryCount: this.state.retryCount,
      },
    }
  }
  
  private classifyErrorSeverity(error: Error): AppError['severity'] {
    // Network errors are usually medium severity
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      return 'medium'
    }
    
    // Chunk load errors (code splitting failures) are high severity
    if (error.message.includes('Loading chunk') || error.message.includes('ChunkLoadError')) {
      return 'high'
    }
    
    // Memory errors are critical
    if (error.message.includes('Maximum call stack') || error.message.includes('out of memory')) {
      return 'critical'
    }
    
    // Third-party errors are low to medium
    if (this.isThirdPartyError(error)) {
      return 'low'
    }
    
    // Default to medium for render errors
    return 'medium'
  }
  
  private classifyErrorCategory(error: Error): AppError['category'] {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      return 'network'
    }
    
    if (error.message.includes('Loading chunk')) {
      return 'async'
    }
    
    if (this.isThirdPartyError(error)) {
      return 'third_party'
    }
    
    return 'render'
  }
  
  private isRecoverable(error: Error): boolean {
    // Network errors are usually recoverable
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      return true
    }
    
    // Chunk load errors are recoverable with retry
    if (error.message.includes('Loading chunk')) {
      return true
    }
    
    // Memory errors are usually not recoverable
    if (error.message.includes('Maximum call stack') || error.message.includes('out of memory')) {
      return false
    }
    
    // Most render errors are recoverable with retry
    return true
  }
  
  private isThirdPartyError(error: Error): boolean {
    if (!error.stack) return false
    
    const thirdPartyIndicators = [
      'node_modules',
      'googleapis',
      'firebase',
      'sentry',
      'analytics',
      'gtag',
    ]
    
    return thirdPartyIndicators.some(indicator => 
      error.stack!.includes(indicator)
    )
  }
  
  private getSessionId(): string {
    let sessionId = sessionStorage.getItem('session-id')
    if (!sessionId) {
      sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      sessionStorage.setItem('session-id', sessionId)
    }
    return sessionId
  }
  
  private addBreadcrumb(breadcrumb: Omit<Breadcrumb, 'timestamp'>) {
    this.breadcrumbs.push({
      ...breadcrumb,
      timestamp: new Date(),
    })
    
    // Keep only last 10 breadcrumbs
    if (this.breadcrumbs.length > 10) {
      this.breadcrumbs.shift()
    }
  }
  
  private resetErrorBoundary = () => {
    this.setState({
      hasError: false,
      error: null,
      errorId: null,
      retryCount: 0,
    })
    
    this.addBreadcrumb({
      message: 'Error boundary reset',
      category: 'info',
      level: 'info',
    })
  }
  
  private handleRetry = () => {
    const { maxRetries = 3 } = this.props
    const { retryCount, error } = this.state
    
    if (retryCount >= maxRetries) {
      this.addBreadcrumb({
        message: `Max retries (${maxRetries}) exceeded`,
        category: 'error',
        level: 'error',
      })
      return
    }
    
    // Check if error is recoverable
    if (error && !error.recoverable) {
      this.addBreadcrumb({
        message: 'Error marked as non-recoverable',
        category: 'error',
        level: 'error',
      })
      return
    }
    
    // Apply recovery strategies
    const strategy = this.selectRecoveryStrategy(error)
    if (strategy) {
      this.applyRecoveryStrategy(strategy)
    } else {
      // Default retry
      this.setState(prevState => ({
        hasError: false,
        error: null,
        retryCount: prevState.retryCount + 1,
      }))
    }
    
    this.addBreadcrumb({
      message: `Retry attempt ${retryCount + 1}/${maxRetries}`,
      category: 'info',
      level: 'info',
    })
  }
  
  private selectRecoveryStrategy(error: AppError | null): ErrorRecoveryStrategy | null {
    if (!error || !this.props.recoveryStrategies) return null
    
    return this.props.recoveryStrategies.find(strategy => 
      !strategy.condition || strategy.condition(error)
    ) || null
  }
  
  private applyRecoveryStrategy(strategy: ErrorRecoveryStrategy) {
    switch (strategy.type) {
      case 'retry':
        const delay = strategy.retryDelay || 1000
        this.retryTimeout = setTimeout(() => {
          this.resetErrorBoundary()
        }, delay)
        break
        
      case 'fallback':
        this.setState({
          fallbackComponent: strategy.fallbackComponent,
        })
        break
        
      case 'redirect':
        if (strategy.redirectUrl) {
          window.location.href = strategy.redirectUrl
        }
        break
        
      case 'reload':
        window.location.reload()
        break
        
      case 'ignore':
        this.resetErrorBoundary()
        break
    }
  }
  
  render() {
    const { hasError, error, retryCount, canRetry, fallbackComponent } = this.state
    const { children, level } = this.props
    
    if (hasError && error) {
      const FallbackComponent = fallbackComponent || DefaultErrorFallback
      
      return (
        <FallbackComponent
          error={error}
          retry={this.handleRetry}
          canRetry={canRetry}
          retryCount={retryCount}
          level={level}
        />
      )
    }
    
    return children
  }
}

// Default fallback component
const DefaultErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  retry,
  canRetry,
  retryCount,
  level,
}) => (
  <div className={`error-fallback error-fallback--${level} p-6 border border-red-200 bg-red-50 rounded-lg`}>
    <div className="flex items-start gap-4">
      <div className="flex-shrink-0">
        <svg className="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      
      <div className="flex-1">
        <h3 className="text-lg font-semibold text-red-800 mb-2">
          Something went wrong
        </h3>
        
        <p className="text-red-700 mb-4">
          {error.severity === 'critical' 
            ? 'A critical error has occurred. Please refresh the page.'
            : 'We encountered an unexpected error. You can try again or continue browsing.'
          }
        </p>
        
        {process.env.NODE_ENV === 'development' && (
          <details className="mb-4 text-sm">
            <summary className="cursor-pointer text-red-600 hover:text-red-800">
              Technical Details
            </summary>
            <div className="mt-2 p-3 bg-red-100 rounded border">
              <div className="font-mono text-xs">
                <div><strong>Error:</strong> {error.name}: {error.message}</div>
                <div><strong>Component:</strong> {error.component}</div>
                <div><strong>Category:</strong> {error.category}</div>
                <div><strong>Severity:</strong> {error.severity}</div>
                {error.stack && (
                  <div className="mt-2">
                    <strong>Stack:</strong>
                    <pre className="mt-1 whitespace-pre-wrap">{error.stack}</pre>
                  </div>
                )}
              </div>
            </div>
          </details>
        )}
        
        <div className="flex gap-3">
          {canRetry && (
            <button
              onClick={retry}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
            >
              Try Again {retryCount > 0 && `(${retryCount})`}
            </button>
          )}
          
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition-colors"
          >
            Refresh Page
          </button>
          
          {level !== 'app' && (
            <button
              onClick={() => window.history.back()}
              className="px-4 py-2 text-red-600 hover:text-red-800 transition-colors"
            >
              Go Back
            </button>
          )}
        </div>
      </div>
    </div>
  </div>
)
```

### **Specialized Error Boundaries**

```typescript
// src/components/ErrorBoundary/StreamingErrorBoundary.tsx
import React from 'react'
import { BaseErrorBoundary } from './BaseErrorBoundary'

const StreamingErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  retry,
  canRetry,
}) => (
  <div className="streaming-error-fallback bg-yellow-50 border border-yellow-200 rounded-lg p-4">
    <div className="flex items-center gap-3">
      <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
        <svg className="w-4 h-4 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      
      <div className="flex-1">
        <h4 className="font-semibold text-yellow-800">Streaming Interrupted</h4>
        <p className="text-yellow-700 text-sm mt-1">
          The message stream was interrupted due to an error. You can retry or view the partial content.
        </p>
        
        <div className="flex gap-2 mt-3">
          {canRetry && (
            <button
              onClick={retry}
              className="px-3 py-1 bg-yellow-600 text-white text-sm rounded hover:bg-yellow-700"
            >
              Retry Stream
            </button>
          )}
          <button className="px-3 py-1 text-yellow-600 text-sm hover:text-yellow-800">
            View Partial Content
          </button>
        </div>
      </div>
    </div>
  </div>
)

export const StreamingErrorBoundary: React.FC<{
  children: React.ReactNode
  onStreamingError?: (error: AppError) => void
}> = ({ children, onStreamingError }) => (
  <BaseErrorBoundary
    level="section"
    fallback={StreamingErrorFallback}
    onError={onStreamingError}
    enableRetry={true}
    maxRetries={2}
    recoveryStrategies={[
      {
        type: 'retry',
        retryDelay: 2000,
        condition: (error) => error.category === 'network' || error.category === 'async',
      },
      {
        type: 'fallback',
        condition: (error) => error.severity === 'critical',
        fallbackComponent: StreamingErrorFallback,
      },
    ]}
  >
    {children}
  </BaseErrorBoundary>
)

// src/components/ErrorBoundary/ChunkLoadErrorBoundary.tsx
const ChunkLoadErrorFallback: React.FC<ErrorFallbackProps> = ({ retry, canRetry }) => (
  <div className="chunk-load-error-fallback bg-blue-50 border border-blue-200 rounded-lg p-4">
    <div className="text-center">
      <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
        <svg className="w-8 h-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
        </svg>
      </div>
      
      <h3 className="text-lg font-semibold text-blue-800 mb-2">Loading Error</h3>
      <p className="text-blue-700 mb-4">
        Failed to load application resources. This might be due to a network issue or an app update.
      </p>
      
      {canRetry && (
        <button
          onClick={retry}
          className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          Retry
        </button>
      )}
    </div>
  </div>
)

export const ChunkLoadErrorBoundary: React.FC<{
  children: React.ReactNode
}> = ({ children }) => (
  <BaseErrorBoundary
    level="page"
    fallback={ChunkLoadErrorFallback}
    enableRetry={true}
    maxRetries={3}
    recoveryStrategies={[
      {
        type: 'reload',
        condition: (error) => error.message.includes('Loading chunk'),
      },
    ]}
  >
    {children}
  </BaseErrorBoundary>
)
```

### **Error Boundary Provider System**

```typescript
// src/providers/ErrorBoundaryProvider.tsx
import React, { createContext, useContext, useCallback, useState } from 'react'

interface ErrorBoundaryContextValue {
  reportError: (error: Error, context?: Record<string, any>) => void
  clearErrors: () => void
  globalErrors: AppError[]
  addBreadcrumb: (breadcrumb: Omit<Breadcrumb, 'timestamp'>) => void
  isErrorIgnored: (error: Error) => boolean
}

const ErrorBoundaryContext = createContext<ErrorBoundaryContextValue | null>(null)

interface ErrorBoundaryProviderProps {
  children: React.ReactNode
  config?: {
    enableGlobalErrorHandler?: boolean
    enableUnhandledRejectionHandler?: boolean
    ignoredErrors?: Array<string | RegExp>
    maxGlobalErrors?: number
  }
}

export const ErrorBoundaryProvider: React.FC<ErrorBoundaryProviderProps> = ({
  children,
  config = {},
}) => {
  const {
    enableGlobalErrorHandler = true,
    enableUnhandledRejectionHandler = true,
    ignoredErrors = [],
    maxGlobalErrors = 50,
  } = config
  
  const [globalErrors, setGlobalErrors] = useState<AppError[]>([])
  const [breadcrumbs, setBreadcrumbs] = useState<Breadcrumb[]>([])
  
  const isErrorIgnored = useCallback((error: Error): boolean => {
    return ignoredErrors.some(pattern => {
      if (typeof pattern === 'string') {
        return error.message.includes(pattern) || error.name.includes(pattern)
      }
      return pattern.test(error.message) || pattern.test(error.name)
    })
  }, [ignoredErrors])
  
  const reportError = useCallback((error: Error, context?: Record<string, any>) => {
    if (isErrorIgnored(error)) return
    
    const appError: AppError = {
      id: `global-error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      message: error.message,
      stack: error.stack,
      name: error.name,
      timestamp: new Date(),
      
      userAgent: navigator.userAgent,
      url: window.location.href,
      
      severity: 'medium',
      category: 'unknown',
      recoverable: false,
      
      sessionId: sessionStorage.getItem('session-id') || 'unknown',
      
      breadcrumbs: [...breadcrumbs],
      tags: { source: 'global-handler' },
      extra: context || {},
    }
    
    setGlobalErrors(prev => {
      const newErrors = [appError, ...prev].slice(0, maxGlobalErrors)
      return newErrors
    })
    
    // Report to external service
    errorReporting.reportError(appError)
    
  }, [breadcrumbs, isErrorIgnored, maxGlobalErrors])
  
  const clearErrors = useCallback(() => {
    setGlobalErrors([])
  }, [])
  
  const addBreadcrumb = useCallback((breadcrumb: Omit<Breadcrumb, 'timestamp'>) => {
    setBreadcrumbs(prev => {
      const newBreadcrumbs = [...prev, { ...breadcrumb, timestamp: new Date() }]
      return newBreadcrumbs.slice(-20) // Keep last 20
    })
  }, [])
  
  // Global error handlers
  React.useEffect(() => {
    if (enableGlobalErrorHandler) {
      const handleGlobalError = (event: ErrorEvent) => {
        reportError(new Error(event.error?.message || event.message), {
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
        })
      }
      
      window.addEventListener('error', handleGlobalError)
      return () => window.removeEventListener('error', handleGlobalError)
    }
  }, [enableGlobalErrorHandler, reportError])
  
  React.useEffect(() => {
    if (enableUnhandledRejectionHandler) {
      const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
        const error = event.reason instanceof Error 
          ? event.reason 
          : new Error(String(event.reason))
        
        reportError(error, { type: 'unhandled-rejection' })
      }
      
      window.addEventListener('unhandledrejection', handleUnhandledRejection)
      return () => window.removeEventListener('unhandledrejection', handleUnhandledRejection)
    }
  }, [enableUnhandledRejectionHandler, reportError])
  
  const contextValue: ErrorBoundaryContextValue = {
    reportError,
    clearErrors,
    globalErrors,
    addBreadcrumb,
    isErrorIgnored,
  }
  
  return (
    <ErrorBoundaryContext.Provider value={contextValue}>
      {children}
    </ErrorBoundaryContext.Provider>
  )
}

export const useErrorBoundary = (): ErrorBoundaryContextValue => {
  const context = useContext(ErrorBoundaryContext)
  if (!context) {
    throw new Error('useErrorBoundary must be used within ErrorBoundaryProvider')
  }
  return context
}

// Hook for manual error reporting
export const useErrorReporting = () => {
  const { reportError, addBreadcrumb } = useErrorBoundary()
  
  const reportAsyncError = useCallback((error: Error, context?: Record<string, any>) => {
    reportError(error, { ...context, source: 'async-error' })
  }, [reportError])
  
  const reportUserAction = useCallback((action: string, data?: Record<string, any>) => {
    addBreadcrumb({
      message: `User action: ${action}`,
      category: 'user',
      level: 'info',
      data,
    })
  }, [addBreadcrumb])
  
  return {
    reportAsyncError,
    reportUserAction,
    addBreadcrumb,
  }
}
```

### **Error Monitoring and Analytics**

```typescript
// src/services/errorReporting.ts
interface ErrorReportingConfig {
  apiEndpoint?: string
  apiKey?: string
  enableConsoleLogging: boolean
  enableLocalStorage: boolean
  sampleRate: number // 0-1, percentage of errors to report
  beforeSend?: (error: AppError) => AppError | null
}

class ErrorReportingService {
  private config: ErrorReportingConfig
  private reportQueue: AppError[] = []
  private isOnline = navigator.onLine
  
  constructor(config: Partial<ErrorReportingConfig> = {}) {
    this.config = {
      enableConsoleLogging: process.env.NODE_ENV === 'development',
      enableLocalStorage: true,
      sampleRate: 1.0,
      ...config,
    }
    
    this.setupOnlineHandler()
    this.setupPeriodicFlush()
  }
  
  async reportError(error: AppError): Promise<void> {
    // Apply sampling
    if (Math.random() > this.config.sampleRate) {
      return
    }
    
    // Apply beforeSend filter
    const processedError = this.config.beforeSend ? this.config.beforeSend(error) : error
    if (!processedError) return
    
    // Console logging
    if (this.config.enableConsoleLogging) {
      console.group(`🚨 Error Report: ${processedError.id}`)
      console.error('Error:', processedError)
      console.groupEnd()
    }
    
    // Local storage for offline scenarios
    if (this.config.enableLocalStorage) {
      this.storeErrorLocally(processedError)
    }
    
    // Queue for remote reporting
    this.reportQueue.push(processedError)
    
    // Attempt to send if online
    if (this.isOnline && this.config.apiEndpoint) {
      await this.flushReports()
    }
  }
  
  private async flushReports(): Promise<void> {
    if (this.reportQueue.length === 0 || !this.config.apiEndpoint) return
    
    const errors = [...this.reportQueue]
    this.reportQueue = []
    
    try {
      const response = await fetch(this.config.apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` }),
        },
        body: JSON.stringify({ errors }),
      })
      
      if (!response.ok) {
        // Put errors back in queue
        this.reportQueue.unshift(...errors)
      }
    } catch (error) {
      // Put errors back in queue
      this.reportQueue.unshift(...errors)
      console.warn('Failed to report errors:', error)
    }
  }
  
  private storeErrorLocally(error: AppError): void {
    try {
      const stored = localStorage.getItem('error-reports') || '[]'
      const errors = JSON.parse(stored)
      
      errors.push(error)
      
      // Keep only last 100 errors
      const limitedErrors = errors.slice(-100)
      
      localStorage.setItem('error-reports', JSON.stringify(limitedErrors))
    } catch (error) {
      console.warn('Failed to store error locally:', error)
    }
  }
  
  private setupOnlineHandler(): void {
    window.addEventListener('online', () => {
      this.isOnline = true
      this.flushReports()
    })
    
    window.addEventListener('offline', () => {
      this.isOnline = false
    })
  }
  
  private setupPeriodicFlush(): void {
    setInterval(() => {
      if (this.isOnline) {
        this.flushReports()
      }
    }, 30000) // Flush every 30 seconds
  }
  
  getStoredErrors(): AppError[] {
    try {
      const stored = localStorage.getItem('error-reports') || '[]'
      return JSON.parse(stored)
    } catch {
      return []
    }
  }
  
  clearStoredErrors(): void {
    localStorage.removeItem('error-reports')
  }
}

export const errorReporting = new ErrorReportingService({
  apiEndpoint: process.env.REACT_APP_ERROR_REPORTING_ENDPOINT,
  apiKey: process.env.REACT_APP_ERROR_REPORTING_KEY,
})
```

## 🎯 **Usage Examples**

### **Application-Level Setup**
```typescript
// App.tsx
import { ErrorBoundaryProvider } from './providers/ErrorBoundaryProvider'
import { BaseErrorBoundary } from './components/ErrorBoundary/BaseErrorBoundary'

function App() {
  return (
    <ErrorBoundaryProvider>
      <BaseErrorBoundary level="app">
        <Router>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/chat" element={
              <ChunkLoadErrorBoundary>
                <ChatPage />
              </ChunkLoadErrorBoundary>
            } />
          </Routes>
        </Router>
      </BaseErrorBoundary>
    </ErrorBoundaryProvider>
  )
}
```

### **Component-Level Error Handling**
```typescript
// StreamingChatContainer with error boundary
export const StreamingChatContainer: React.FC = () => {
  const { reportAsyncError, reportUserAction } = useErrorReporting()
  
  const handleSendMessage = async (message: string) => {
    try {
      reportUserAction('send_message', { messageLength: message.length })
      await sendMessage(message)
    } catch (error) {
      reportAsyncError(error as Error, { 
        action: 'send_message',
        messageLength: message.length 
      })
    }
  }
  
  return (
    <StreamingErrorBoundary>
      {/* Chat interface */}
    </StreamingErrorBoundary>
  )
}
```

## 🎯 **Key Takeaways**

1. **Hierarchical error boundaries** - Different levels need different error handling strategies
2. **Context-aware error reporting** - Include relevant information to help debugging
3. **Recovery strategies** - Not all errors require a complete reset
4. **User-friendly fallbacks** - Show helpful error messages, not technical details
5. **Async error handling** - Catch Promise rejections and async errors
6. **Error analytics** - Track error patterns to improve application stability
7. **Performance impact** - Error boundaries should not slow down the application

---

**Next**: [04-performance-optimization-patterns.md](./04-performance-optimization-patterns.md) - Advanced Performance Strategies

**Previous**: [02-state-management-patterns.md](./02-state-management-patterns.md)