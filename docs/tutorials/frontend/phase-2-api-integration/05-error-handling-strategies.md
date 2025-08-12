# Phase 2.5: Error Handling Strategies - Building Resilient Applications

## 🎯 **Learning Objectives**

By the end of this tutorial, you will:
- Implement comprehensive error handling strategies for API integration
- Build user-friendly error messages and recovery mechanisms
- Create graceful degradation patterns for network failures
- Handle edge cases like timeout, retry limits, and malformed responses
- Design error boundaries that prevent application crashes

## 🚨 **The Error Handling Challenge**

In production, things go wrong constantly:
- Network failures and timeouts
- Server errors and maintenance
- Invalid API responses
- Rate limiting and authentication issues
- Protocol parsing failures
- Client-side JavaScript errors

**Our goal**: Build an application that **fails gracefully** and provides **clear user feedback**.

## 🛡️ **Error Classification System**

### **Step 1: Error Type Definitions**

```typescript
// src/types/errors.ts
export enum ErrorCategory {
  NETWORK = 'network',
  SERVER = 'server', 
  CLIENT = 'client',
  PROTOCOL = 'protocol',
  VALIDATION = 'validation',
  AUTHENTICATION = 'authentication',
  RATE_LIMIT = 'rate_limit',
  TIMEOUT = 'timeout',
  UNKNOWN = 'unknown'
}

export enum ErrorSeverity {
  LOW = 'low',           // Non-blocking, can continue
  MEDIUM = 'medium',     // Affects functionality but recoverable
  HIGH = 'high',         // Blocks main functionality 
  CRITICAL = 'critical'  // Application unusable
}

export interface ApplicationError extends Error {
  category: ErrorCategory
  severity: ErrorSeverity
  code: string
  context?: Record<string, any>
  originalError?: Error
  retryable: boolean
  userMessage: string
  technicalMessage: string
  timestamp: Date
}

export class ErrorFactory {
  static createNetworkError(originalError: Error, context?: any): ApplicationError {
    return {
      name: 'NetworkError',
      message: 'Network request failed',
      category: ErrorCategory.NETWORK,
      severity: ErrorSeverity.MEDIUM,
      code: 'NET_001',
      context,
      originalError,
      retryable: true,
      userMessage: 'Connection problem. Please check your internet connection and try again.',
      technicalMessage: `Network failure: ${originalError.message}`,
      timestamp: new Date(),
    }
  }

  static createTimeoutError(timeoutMs: number, context?: any): ApplicationError {
    return {
      name: 'TimeoutError',
      message: `Request timed out after ${timeoutMs}ms`,
      category: ErrorCategory.TIMEOUT,
      severity: ErrorSeverity.MEDIUM,
      code: 'TIMEOUT_001',
      context,
      originalError: undefined,
      retryable: true,
      userMessage: `Request took too long (${timeoutMs/1000}s). The server might be busy, please try again.`,
      technicalMessage: `Request timeout after ${timeoutMs}ms`,
      timestamp: new Date(),
    }
  }

  static createProtocolError(protocol: string, parseError: Error, context?: any): ApplicationError {
    return {
      name: 'ProtocolError',
      message: `Failed to parse ${protocol} response`,
      category: ErrorCategory.PROTOCOL,
      severity: ErrorSeverity.LOW,
      code: 'PROTO_001',
      context,
      originalError: parseError,
      retryable: false,
      userMessage: 'The agent response format was unexpected, but the content is still available.',
      technicalMessage: `${protocol} parsing failed: ${parseError.message}`,
      timestamp: new Date(),
    }
  }

  static createServerError(statusCode: number, statusText: string, context?: any): ApplicationError {
    const isRetryable = statusCode >= 500 // 5xx errors are typically retryable
    const severity = statusCode >= 500 ? ErrorSeverity.MEDIUM : ErrorSeverity.HIGH

    return {
      name: 'ServerError',
      message: `Server error: ${statusCode} ${statusText}`,
      category: ErrorCategory.SERVER,
      severity,
      code: `HTTP_${statusCode}`,
      context,
      originalError: undefined,
      retryable: isRetryable,
      userMessage: isRetryable 
        ? 'Server is temporarily unavailable. Please try again in a moment.'
        : 'Server rejected the request. Please check your input and try again.',
      technicalMessage: `HTTP ${statusCode}: ${statusText}`,
      timestamp: new Date(),
    }
  }

  static createValidationError(field: string, value: any, rule: string): ApplicationError {
    return {
      name: 'ValidationError',
      message: `Validation failed for ${field}`,
      category: ErrorCategory.VALIDATION,
      severity: ErrorSeverity.LOW,
      code: 'VALID_001',
      context: { field, value, rule },
      originalError: undefined,
      retryable: false,
      userMessage: `Please check your ${field} and try again.`,
      technicalMessage: `Field '${field}' failed validation rule '${rule}' with value '${value}'`,
      timestamp: new Date(),
    }
  }
}
```

### **Step 2: Error Handler Service**

```typescript
// src/services/errorHandler.ts
import { ApplicationError, ErrorCategory, ErrorSeverity } from '../types/errors'

interface ErrorHandlerConfig {
  enableLogging: boolean
  enableReporting: boolean
  maxRetries: number
  retryDelayMs: number
  reportingEndpoint?: string
}

export class ErrorHandlerService {
  private config: ErrorHandlerConfig
  private errorCounts = new Map<string, number>()

  constructor(config: Partial<ErrorHandlerConfig> = {}) {
    this.config = {
      enableLogging: true,
      enableReporting: process.env.NODE_ENV === 'production',
      maxRetries: 3,
      retryDelayMs: 1000,
      ...config,
    }
  }

  /**
   * Handle application error with appropriate response
   */
  async handleError(error: ApplicationError): Promise<ErrorHandlingResult> {
    // Log error
    if (this.config.enableLogging) {
      this.logError(error)
    }

    // Track error frequency
    this.trackErrorFrequency(error)

    // Report critical errors
    if (error.severity === ErrorSeverity.CRITICAL && this.config.enableReporting) {
      await this.reportError(error)
    }

    // Determine recovery strategy
    const strategy = this.determineRecoveryStrategy(error)

    return {
      error,
      strategy,
      userMessage: error.userMessage,
      canRetry: error.retryable && this.canRetry(error),
      suggestedAction: this.getSuggestedAction(error),
    }
  }

  private logError(error: ApplicationError): void {
    const logLevel = this.getLogLevel(error.severity)
    const logMessage = `[${error.category}] ${error.technicalMessage}`
    
    const context = {
      code: error.code,
      category: error.category,
      severity: error.severity,
      retryable: error.retryable,
      context: error.context,
      timestamp: error.timestamp.toISOString(),
    }

    console[logLevel](logMessage, context)

    // Also log original error if available
    if (error.originalError) {
      console[logLevel]('Original error:', error.originalError)
    }
  }

  private getLogLevel(severity: ErrorSeverity): 'debug' | 'info' | 'warn' | 'error' {
    switch (severity) {
      case ErrorSeverity.LOW: return 'info'
      case ErrorSeverity.MEDIUM: return 'warn'
      case ErrorSeverity.HIGH:
      case ErrorSeverity.CRITICAL: return 'error'
      default: return 'warn'
    }
  }

  private trackErrorFrequency(error: ApplicationError): void {
    const key = `${error.category}:${error.code}`
    const currentCount = this.errorCounts.get(key) || 0
    this.errorCounts.set(key, currentCount + 1)

    // Alert on high error frequency
    if (currentCount > 5) {
      console.warn(`High error frequency detected: ${key} (${currentCount} occurrences)`)
    }
  }

  private async reportError(error: ApplicationError): Promise<void> {
    if (!this.config.reportingEndpoint) return

    try {
      await fetch(this.config.reportingEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          error: {
            name: error.name,
            message: error.technicalMessage,
            category: error.category,
            severity: error.severity,
            code: error.code,
            context: error.context,
            timestamp: error.timestamp.toISOString(),
          },
          user_agent: navigator.userAgent,
          url: window.location.href,
          stack: error.originalError?.stack,
        }),
      })
    } catch (reportingError) {
      console.error('Failed to report error:', reportingError)
    }
  }

  private determineRecoveryStrategy(error: ApplicationError): RecoveryStrategy {
    switch (error.category) {
      case ErrorCategory.NETWORK:
      case ErrorCategory.TIMEOUT:
        return RecoveryStrategy.RETRY_WITH_BACKOFF
      
      case ErrorCategory.SERVER:
        return error.retryable 
          ? RecoveryStrategy.RETRY_WITH_BACKOFF 
          : RecoveryStrategy.SHOW_ERROR
      
      case ErrorCategory.PROTOCOL:
        return RecoveryStrategy.USE_FALLBACK
      
      case ErrorCategory.VALIDATION:
        return RecoveryStrategy.REQUEST_INPUT
      
      case ErrorCategory.AUTHENTICATION:
        return RecoveryStrategy.REQUEST_AUTH
      
      default:
        return RecoveryStrategy.SHOW_ERROR
    }
  }

  private canRetry(error: ApplicationError): boolean {
    if (!error.retryable) return false
    
    const key = `${error.category}:${error.code}`
    const errorCount = this.errorCounts.get(key) || 0
    
    return errorCount < this.config.maxRetries
  }

  private getSuggestedAction(error: ApplicationError): string {
    switch (error.category) {
      case ErrorCategory.NETWORK:
        return 'Check your internet connection and try again'
      
      case ErrorCategory.TIMEOUT:
        return 'The server is slow. Try again or wait a moment'
      
      case ErrorCategory.SERVER:
        return error.retryable 
          ? 'Server issue detected. Trying again automatically'
          : 'Please contact support if this continues'
      
      case ErrorCategory.VALIDATION:
        return 'Please check your input and try again'
      
      default:
        return 'Please try again or contact support'
    }
  }
}

export enum RecoveryStrategy {
  RETRY_WITH_BACKOFF = 'retry_with_backoff',
  USE_FALLBACK = 'use_fallback', 
  SHOW_ERROR = 'show_error',
  REQUEST_INPUT = 'request_input',
  REQUEST_AUTH = 'request_auth',
}

export interface ErrorHandlingResult {
  error: ApplicationError
  strategy: RecoveryStrategy
  userMessage: string
  canRetry: boolean
  suggestedAction: string
}
```

### **Step 3: Enhanced Orchestrator API with Error Handling**

```typescript
// src/services/orchestratorApi.ts - Enhanced with comprehensive error handling
import { ErrorFactory, ApplicationError } from '../types/errors'
import { ErrorHandlerService } from './errorHandler'

export class ResilientOrchestratorAPI extends OrchestratorAPI {
  private errorHandler: ErrorHandlerService
  private retryAttempts = new Map<string, number>()

  constructor() {
    super()
    this.errorHandler = new ErrorHandlerService()
  }

  /**
   * Enhanced processMessage with comprehensive error handling
   */
  async processMessage(query: string): Promise<ProcessResponse | null> {
    const requestId = this.generateRequestId()
    
    try {
      // Input validation
      this.validateQuery(query)

      // Make request with error handling
      const result = await this.makeRequestWithErrorHandling(
        '/process',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query }),
        },
        requestId
      )

      // Reset retry count on success
      this.retryAttempts.delete(requestId)
      
      return result

    } catch (error) {
      const appError = this.convertToApplicationError(error, { query, requestId })
      const handling = await this.errorHandler.handleError(appError)
      
      // Handle based on strategy
      switch (handling.strategy) {
        case RecoveryStrategy.RETRY_WITH_BACKOFF:
          return this.handleRetry(requestId, () => this.processMessage(query))
        
        case RecoveryStrategy.USE_FALLBACK:
          return this.getFallbackResponse(query)
        
        default:
          throw appError // Let component handle display
      }
    }
  }

  private validateQuery(query: string): void {
    if (!query || typeof query !== 'string') {
      throw ErrorFactory.createValidationError('query', query, 'must be non-empty string')
    }

    if (query.trim().length === 0) {
      throw ErrorFactory.createValidationError('query', query, 'cannot be empty or whitespace')
    }

    if (query.length > 10000) {
      throw ErrorFactory.createValidationError('query', query, 'exceeds maximum length of 10,000 characters')
    }
  }

  private async makeRequestWithErrorHandling<T>(
    endpoint: string, 
    options: RequestInit,
    requestId: string
  ): Promise<T> {
    const timeoutMs = 30000 // 30 seconds
    const startTime = Date.now()

    try {
      // Create timeout controller
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      // Check HTTP status
      if (!response.ok) {
        throw ErrorFactory.createServerError(
          response.status, 
          response.statusText, 
          { endpoint, requestId, duration: Date.now() - startTime }
        )
      }

      // Parse response
      const data = await response.json()
      return data

    } catch (error) {
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        throw ErrorFactory.createNetworkError(error, { endpoint, requestId })
      }

      if (error.name === 'AbortError') {
        throw ErrorFactory.createTimeoutError(timeoutMs, { endpoint, requestId })
      }

      // Re-throw ApplicationErrors as-is
      if ('category' in error) {
        throw error
      }

      // Convert unknown errors
      throw ErrorFactory.createNetworkError(error as Error, { endpoint, requestId })
    }
  }

  private convertToApplicationError(error: any, context: any): ApplicationError {
    // If already an ApplicationError, return as-is
    if (error && typeof error === 'object' && 'category' in error) {
      return error as ApplicationError
    }

    // Convert generic errors
    if (error instanceof Error) {
      return ErrorFactory.createNetworkError(error, context)
    }

    // Handle unknown error types
    return ErrorFactory.createNetworkError(new Error(String(error)), context)
  }

  private async handleRetry<T>(requestId: string, retryFunction: () => Promise<T>): Promise<T | null> {
    const currentAttempts = this.retryAttempts.get(requestId) || 0
    const maxAttempts = 3

    if (currentAttempts >= maxAttempts) {
      console.warn(`Max retry attempts (${maxAttempts}) exceeded for request ${requestId}`)
      return null
    }

    // Exponential backoff: 1s, 2s, 4s
    const delayMs = Math.pow(2, currentAttempts) * 1000
    console.log(`Retrying request ${requestId} in ${delayMs}ms (attempt ${currentAttempts + 1}/${maxAttempts})`)
    
    this.retryAttempts.set(requestId, currentAttempts + 1)
    
    await new Promise(resolve => setTimeout(resolve, delayMs))
    
    try {
      return await retryFunction()
    } catch (retryError) {
      // Let the outer error handling deal with it
      throw retryError
    }
  }

  private getFallbackResponse(query: string): ProcessResponse {
    return {
      request_id: `fallback-${Date.now()}`,
      agent_id: 'fallback',
      agent_name: 'Fallback Handler',
      protocol: 'fallback',
      content: `I received your message "${query}" but encountered a technical issue. Please try again or rephrase your question.`,
      confidence: 0.1,
      success: false,
      duration_ms: 0,
      timestamp: new Date().toISOString(),
    }
  }

  private generateRequestId(): string {
    return `req-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }
}
```

### **Step 4: Error-Aware React Hook**

```typescript
// src/hooks/useErrorHandling.ts
import { useState, useCallback } from 'react'
import { ApplicationError } from '../types/errors'
import { ErrorHandlerService } from '../services/errorHandler'

interface ErrorState {
  error: ApplicationError | null
  isRetrying: boolean
  retryCount: number
  lastRetry: Date | null
}

export const useErrorHandling = () => {
  const [errorState, setErrorState] = useState<ErrorState>({
    error: null,
    isRetrying: false,
    retryCount: 0,
    lastRetry: null,
  })

  const errorHandler = new ErrorHandlerService()

  const handleError = useCallback(async (error: ApplicationError) => {
    const result = await errorHandler.handleError(error)
    
    setErrorState(prev => ({
      ...prev,
      error,
      isRetrying: false,
    }))

    return result
  }, [errorHandler])

  const retry = useCallback(async (retryFunction: () => Promise<any>) => {
    setErrorState(prev => ({
      ...prev,
      isRetrying: true,
      retryCount: prev.retryCount + 1,
      lastRetry: new Date(),
    }))

    try {
      const result = await retryFunction()
      
      // Clear error on successful retry
      setErrorState({
        error: null,
        isRetrying: false,
        retryCount: 0,
        lastRetry: null,
      })

      return result
    } catch (retryError) {
      setErrorState(prev => ({
        ...prev,
        isRetrying: false,
        error: retryError as ApplicationError,
      }))
      
      throw retryError
    }
  }, [])

  const clearError = useCallback(() => {
    setErrorState({
      error: null,
      isRetrying: false,
      retryCount: 0,
      lastRetry: null,
    })
  }, [])

  return {
    error: errorState.error,
    isRetrying: errorState.isRetrying,
    retryCount: errorState.retryCount,
    lastRetry: errorState.lastRetry,
    handleError,
    retry,
    clearError,
    hasError: !!errorState.error,
  }
}
```

### **Step 5: Error Display Components**

```typescript
// src/components/ErrorDisplay.tsx
import React from 'react'
import { AlertTriangle, RefreshCw, X, Info, AlertCircle } from 'lucide-react'
import { ApplicationError, ErrorSeverity } from '../types/errors'

interface ErrorDisplayProps {
  error: ApplicationError
  canRetry?: boolean
  isRetrying?: boolean
  onRetry?: () => void
  onDismiss?: () => void
  className?: string
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  canRetry = false,
  isRetrying = false,
  onRetry,
  onDismiss,
  className = '',
}) => {
  const getSeverityStyles = (severity: ErrorSeverity) => {
    switch (severity) {
      case ErrorSeverity.LOW:
        return 'bg-blue-50 border-blue-200 text-blue-800'
      case ErrorSeverity.MEDIUM:
        return 'bg-yellow-50 border-yellow-200 text-yellow-800'
      case ErrorSeverity.HIGH:
        return 'bg-orange-50 border-orange-200 text-orange-800'
      case ErrorSeverity.CRITICAL:
        return 'bg-red-50 border-red-200 text-red-800'
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800'
    }
  }

  const getSeverityIcon = (severity: ErrorSeverity) => {
    switch (severity) {
      case ErrorSeverity.LOW:
        return <Info className="w-5 h-5" />
      case ErrorSeverity.MEDIUM:
        return <AlertTriangle className="w-5 h-5" />
      case ErrorSeverity.HIGH:
      case ErrorSeverity.CRITICAL:
        return <AlertCircle className="w-5 h-5" />
      default:
        return <AlertTriangle className="w-5 h-5" />
    }
  }

  return (
    <div className={`error-display border-2 rounded-lg p-4 ${getSeverityStyles(error.severity)} ${className}`}>
      <div className="flex items-start gap-3">
        {getSeverityIcon(error.severity)}
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <h3 className="font-semibold">
              {error.category.charAt(0).toUpperCase() + error.category.slice(1)} Error
            </h3>
            <span className="text-xs font-mono bg-white bg-opacity-50 px-2 py-1 rounded">
              {error.code}
            </span>
          </div>
          
          <p className="mb-3">{error.userMessage}</p>
          
          {process.env.NODE_ENV === 'development' && (
            <details className="mb-3">
              <summary className="cursor-pointer text-sm opacity-75">
                Technical Details
              </summary>
              <div className="mt-2 text-xs bg-white bg-opacity-50 p-2 rounded">
                <p><strong>Message:</strong> {error.technicalMessage}</p>
                <p><strong>Retryable:</strong> {error.retryable ? 'Yes' : 'No'}</p>
                <p><strong>Time:</strong> {error.timestamp.toISOString()}</p>
                {error.context && (
                  <p><strong>Context:</strong> {JSON.stringify(error.context, null, 2)}</p>
                )}
              </div>
            </details>
          )}
          
          <div className="flex gap-2">
            {canRetry && (
              <button
                onClick={onRetry}
                disabled={isRetrying}
                className="flex items-center gap-1 px-3 py-1 bg-white bg-opacity-20 hover:bg-opacity-30 rounded text-sm disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${isRetrying ? 'animate-spin' : ''}`} />
                {isRetrying ? 'Retrying...' : 'Try Again'}
              </button>
            )}
            
            {onDismiss && (
              <button
                onClick={onDismiss}
                className="flex items-center gap-1 px-3 py-1 bg-white bg-opacity-20 hover:bg-opacity-30 rounded text-sm"
              >
                <X className="w-4 h-4" />
                Dismiss
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
```

## 🎯 **Integration Example**

### **Using Error Handling in Components**

```typescript
// src/components/ChatInterface.tsx - With comprehensive error handling
import React, { useState } from 'react'
import { useErrorHandling } from '../hooks/useErrorHandling'
import { ResilientOrchestratorAPI } from '../services/orchestratorApi'
import { ErrorDisplay } from './ErrorDisplay'

export const ChatInterface: React.FC = () => {
  const [query, setQuery] = useState('')
  const [response, setResponse] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const { error, isRetrying, handleError, retry, clearError, hasError } = useErrorHandling()
  
  const api = new ResilientOrchestratorAPI()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setIsLoading(true)
    clearError()

    try {
      const result = await api.processMessage(query)
      if (result) {
        setResponse(result.content)
      }
    } catch (err) {
      await handleError(err as any)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRetry = async () => {
    if (!query.trim()) return

    try {
      await retry(async () => {
        const result = await api.processMessage(query)
        if (result) {
          setResponse(result.content)
        }
        return result
      })
    } catch (retryError) {
      // Error is already handled by the hook
      console.log('Retry failed:', retryError)
    }
  }

  return (
    <div className="chat-interface max-w-2xl mx-auto p-4">
      <form onSubmit={handleSubmit} className="mb-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask the agents anything..."
            className="flex-1 p-2 border border-gray-300 rounded"
            disabled={isLoading || isRetrying}
          />
          <button
            type="submit"
            disabled={isLoading || isRetrying || !query.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
          >
            {isLoading || isRetrying ? 'Processing...' : 'Send'}
          </button>
        </div>
      </form>

      {hasError && (
        <ErrorDisplay
          error={error!}
          canRetry={error?.retryable}
          isRetrying={isRetrying}
          onRetry={handleRetry}
          onDismiss={clearError}
          className="mb-4"
        />
      )}

      {response && (
        <div className="response bg-gray-50 p-4 rounded">
          <pre className="whitespace-pre-wrap">{response}</pre>
        </div>
      )}
    </div>
  )
}
```

## 🎯 **Key Takeaways**

1. **Classify errors systematically** - Different error types need different handling
2. **Always provide user-friendly messages** - Technical errors confuse users
3. **Implement retry logic carefully** - Not all errors should be retried
4. **Log and monitor errors** - Track patterns to improve reliability
5. **Graceful degradation is key** - Provide fallback options when possible
6. **Test error scenarios** - Don't wait for production to find edge cases
7. **Recovery strategies matter** - Help users get back on track quickly

---

**Next**: [06-health-monitoring.md](./06-health-monitoring.md) - Agent Discovery and Health Checks

**Previous**: [04-protocol-aware-parsing.md](./04-protocol-aware-parsing.md)