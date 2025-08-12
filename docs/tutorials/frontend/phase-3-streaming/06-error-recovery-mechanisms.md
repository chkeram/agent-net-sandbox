# Phase 3.6: Error Recovery Mechanisms - Robust Streaming Error Handling

## 🎯 **Learning Objectives**

By the end of this tutorial, you will:
- Build comprehensive error recovery systems for streaming failures
- Implement automatic retry logic with exponential backoff strategies
- Handle partial content recovery when streams are interrupted
- Create user-friendly error states with clear recovery options
- Build fallback mechanisms that maintain functionality during outages

## 🚨 **The Streaming Error Challenge**

Streaming introduces unique error scenarios:
- **Connection drops**: Network interruption mid-stream
- **Partial content**: Stream cuts off with incomplete response
- **Server errors**: Backend failures during streaming
- **Protocol errors**: Malformed streaming data
- **Timeout scenarios**: Long-running requests that hang
- **Rate limiting**: Too many concurrent streams

**Our goal**: Build **resilient streaming** that recovers gracefully from any failure.

## 🛡️ **Error Recovery Architecture**

### **Step 1: Streaming Error Types**

```typescript
// src/types/streamingErrors.ts
export enum StreamingErrorType {
  CONNECTION_LOST = 'connection_lost',
  STREAM_INTERRUPTED = 'stream_interrupted', 
  PARTIAL_CONTENT = 'partial_content',
  SERVER_ERROR = 'server_error',
  TIMEOUT = 'timeout',
  RATE_LIMITED = 'rate_limited',
  PROTOCOL_ERROR = 'protocol_error',
  UNKNOWN = 'unknown'
}

export interface StreamingError extends Error {
  type: StreamingErrorType
  recoverable: boolean
  partialContent?: string
  lastValidChunk?: string
  streamPosition?: number
  retryAfter?: number // seconds
  context?: {
    query: string
    requestId: string
    agentInfo?: {
      id: string
      name: string
      protocol: string
    }
    streamDuration: number
    chunksReceived: number
  }
}

export interface RecoveryStrategy {
  type: 'retry' | 'fallback' | 'partial_recovery' | 'user_action' | 'fail'
  retryDelay?: number
  maxRetries?: number
  fallbackContent?: string
  userMessage: string
  actionLabel?: string
}

export interface RecoveryAttempt {
  attemptNumber: number
  timestamp: Date
  strategy: RecoveryStrategy
  error: StreamingError
  success: boolean
  recoveredContent?: string
}
```

### **Step 2: Error Recovery Service**

```typescript
// src/services/streamingErrorRecovery.ts
interface RecoveryConfig {
  maxRetries: number
  baseRetryDelay: number // milliseconds
  maxRetryDelay: number
  enablePartialRecovery: boolean
  enableFallbackContent: boolean
  timeoutThreshold: number
}

export class StreamingErrorRecoveryService {
  private config: RecoveryConfig
  private recoveryHistory = new Map<string, RecoveryAttempt[]>()

  constructor(config: Partial<RecoveryConfig> = {}) {
    this.config = {
      maxRetries: 3,
      baseRetryDelay: 1000,
      maxRetryDelay: 10000,
      enablePartialRecovery: true,
      enableFallbackContent: true,
      timeoutThreshold: 30000,
      ...config
    }
  }

  /**
   * Analyze error and determine recovery strategy
   */
  analyzeError(error: StreamingError): RecoveryStrategy {
    const attemptHistory = this.recoveryHistory.get(error.context?.requestId || '') || []
    const retryCount = attemptHistory.length

    switch (error.type) {
      case StreamingErrorType.CONNECTION_LOST:
        return this.handleConnectionLost(error, retryCount)
      
      case StreamingErrorType.STREAM_INTERRUPTED:
        return this.handleStreamInterrupted(error, retryCount)
      
      case StreamingErrorType.PARTIAL_CONTENT:
        return this.handlePartialContent(error, retryCount)
      
      case StreamingErrorType.SERVER_ERROR:
        return this.handleServerError(error, retryCount)
      
      case StreamingErrorType.TIMEOUT:
        return this.handleTimeout(error, retryCount)
      
      case StreamingErrorType.RATE_LIMITED:
        return this.handleRateLimit(error, retryCount)
      
      case StreamingErrorType.PROTOCOL_ERROR:
        return this.handleProtocolError(error, retryCount)
      
      default:
        return this.handleUnknownError(error, retryCount)
    }
  }

  /**
   * Execute recovery strategy
   */
  async executeRecovery(
    strategy: RecoveryStrategy,
    error: StreamingError,
    retryFunction: () => Promise<any>
  ): Promise<{ success: boolean; content?: string; newError?: StreamingError }> {
    const requestId = error.context?.requestId || 'unknown'
    const attempt: RecoveryAttempt = {
      attemptNumber: (this.recoveryHistory.get(requestId)?.length || 0) + 1,
      timestamp: new Date(),
      strategy,
      error,
      success: false,
    }

    // Record attempt
    const history = this.recoveryHistory.get(requestId) || []
    history.push(attempt)
    this.recoveryHistory.set(requestId, history)

    try {
      switch (strategy.type) {
        case 'retry':
          return await this.executeRetry(strategy, error, retryFunction, attempt)
        
        case 'fallback':
          return await this.executeFallback(strategy, error, attempt)
        
        case 'partial_recovery':
          return await this.executePartialRecovery(strategy, error, attempt)
        
        case 'user_action':
          return { success: false } // User action required
        
        case 'fail':
        default:
          return { success: false, newError: error }
      }
    } catch (recoveryError) {
      attempt.success = false
      console.error('Recovery execution failed:', recoveryError)
      
      return {
        success: false,
        newError: this.createRecoveryError(recoveryError, error)
      }
    }
  }

  private handleConnectionLost(error: StreamingError, retryCount: number): RecoveryStrategy {
    if (retryCount >= this.config.maxRetries) {
      return {
        type: 'fail',
        userMessage: 'Connection lost and maximum retries exceeded. Please check your internet connection.',
      }
    }

    // Check if we have partial content to preserve
    if (error.partialContent && this.config.enablePartialRecovery) {
      return {
        type: 'partial_recovery',
        retryDelay: this.calculateRetryDelay(retryCount),
        userMessage: 'Connection lost. Attempting to recover where we left off...',
        actionLabel: 'Retry from last position'
      }
    }

    return {
      type: 'retry',
      retryDelay: this.calculateRetryDelay(retryCount),
      maxRetries: this.config.maxRetries - retryCount,
      userMessage: `Connection lost. Retrying in ${Math.ceil(this.calculateRetryDelay(retryCount) / 1000)} seconds...`,
      actionLabel: 'Retry now'
    }
  }

  private handleStreamInterrupted(error: StreamingError, retryCount: number): RecoveryStrategy {
    if (retryCount >= this.config.maxRetries) {
      if (error.partialContent && this.config.enableFallbackContent) {
        return {
          type: 'fallback',
          fallbackContent: error.partialContent,
          userMessage: 'Stream was interrupted, but here\'s the partial response we received.',
        }
      }
      
      return {
        type: 'fail',
        userMessage: 'Stream was interrupted and could not be recovered.',
      }
    }

    return {
      type: 'retry',
      retryDelay: this.calculateRetryDelay(retryCount),
      maxRetries: this.config.maxRetries - retryCount,
      userMessage: 'Stream was interrupted. Attempting to restart...',
      actionLabel: 'Retry'
    }
  }

  private handlePartialContent(error: StreamingError, retryCount: number): RecoveryStrategy {
    if (!this.config.enablePartialRecovery) {
      return this.handleStreamInterrupted(error, retryCount)
    }

    return {
      type: 'partial_recovery',
      retryDelay: this.calculateRetryDelay(retryCount),
      fallbackContent: error.partialContent,
      userMessage: 'Partial response received. You can view what we got so far or retry for the complete response.',
      actionLabel: 'Retry for complete response'
    }
  }

  private handleServerError(error: StreamingError, retryCount: number): RecoveryStrategy {
    // Server errors (5xx) are usually retryable
    if (error.message.includes('5') && retryCount < this.config.maxRetries) {
      return {
        type: 'retry',
        retryDelay: this.calculateRetryDelay(retryCount),
        maxRetries: this.config.maxRetries - retryCount,
        userMessage: 'Server is temporarily unavailable. Retrying...',
        actionLabel: 'Retry'
      }
    }

    // Client errors (4xx) usually aren't retryable
    return {
      type: 'user_action',
      userMessage: 'Server rejected the request. Please try rephrasing your query or try again later.',
      actionLabel: 'Try different query'
    }
  }

  private handleTimeout(error: StreamingError, retryCount: number): RecoveryStrategy {
    if (retryCount >= this.config.maxRetries) {
      return {
        type: 'fail',
        userMessage: 'Request timed out repeatedly. The server might be overloaded.',
      }
    }

    return {
      type: 'retry',
      retryDelay: this.calculateRetryDelay(retryCount),
      maxRetries: this.config.maxRetries - retryCount,
      userMessage: 'Request timed out. The server might be busy, retrying...',
      actionLabel: 'Retry'
    }
  }

  private handleRateLimit(error: StreamingError, retryCount: number): RecoveryStrategy {
    const retryAfter = (error.retryAfter || 60) * 1000 // Convert to milliseconds

    return {
      type: 'retry',
      retryDelay: retryAfter,
      maxRetries: 1, // Only retry once for rate limits
      userMessage: `Rate limited. Retrying in ${Math.ceil(retryAfter / 1000)} seconds...`,
      actionLabel: 'Wait and retry'
    }
  }

  private handleProtocolError(error: StreamingError, retryCount: number): RecoveryStrategy {
    // Protocol errors usually indicate data corruption, not network issues
    if (error.partialContent && this.config.enableFallbackContent) {
      return {
        type: 'fallback',
        fallbackContent: error.partialContent,
        userMessage: 'Response format was corrupted, but here\'s what we could extract.',
      }
    }

    return {
      type: 'fail',
      userMessage: 'Response format was corrupted and could not be recovered.',
    }
  }

  private handleUnknownError(error: StreamingError, retryCount: number): RecoveryStrategy {
    if (retryCount < 2) { // Try a couple times for unknown errors
      return {
        type: 'retry',
        retryDelay: this.calculateRetryDelay(retryCount),
        maxRetries: 2 - retryCount,
        userMessage: 'An unexpected error occurred. Retrying...',
        actionLabel: 'Retry'
      }
    }

    return {
      type: 'fail',
      userMessage: 'An unexpected error occurred and could not be recovered.',
    }
  }

  private async executeRetry(
    strategy: RecoveryStrategy,
    error: StreamingError,
    retryFunction: () => Promise<any>,
    attempt: RecoveryAttempt
  ): Promise<{ success: boolean; content?: string; newError?: StreamingError }> {
    // Wait for retry delay
    if (strategy.retryDelay) {
      await new Promise(resolve => setTimeout(resolve, strategy.retryDelay))
    }

    try {
      const result = await retryFunction()
      attempt.success = true
      attempt.recoveredContent = typeof result === 'string' ? result : JSON.stringify(result)
      
      return { success: true, content: attempt.recoveredContent }
    } catch (retryError) {
      attempt.success = false
      return { success: false, newError: this.createStreamingError(retryError, error.context) }
    }
  }

  private async executeFallback(
    strategy: RecoveryStrategy,
    error: StreamingError,
    attempt: RecoveryAttempt
  ): Promise<{ success: boolean; content?: string }> {
    const fallbackContent = strategy.fallbackContent || error.partialContent || 'Unable to complete the request.'
    
    attempt.success = true
    attempt.recoveredContent = fallbackContent
    
    return { success: true, content: fallbackContent }
  }

  private async executePartialRecovery(
    strategy: RecoveryStrategy,
    error: StreamingError,
    attempt: RecoveryAttempt
  ): Promise<{ success: boolean; content?: string }> {
    // For partial recovery, we present the partial content immediately
    // and optionally allow the user to retry for the complete response
    const partialContent = error.partialContent || 'Partial response was incomplete.'
    
    attempt.success = true
    attempt.recoveredContent = partialContent + '\n\n[Response was incomplete - you can retry for the full response]'
    
    return { success: true, content: attempt.recoveredContent }
  }

  private calculateRetryDelay(retryCount: number): number {
    // Exponential backoff with jitter
    const exponentialDelay = Math.min(
      this.config.baseRetryDelay * Math.pow(2, retryCount),
      this.config.maxRetryDelay
    )
    
    // Add random jitter (±25%)
    const jitter = exponentialDelay * 0.25 * (Math.random() - 0.5)
    
    return Math.round(exponentialDelay + jitter)
  }

  private createRecoveryError(recoveryError: any, originalError: StreamingError): StreamingError {
    return {
      name: 'RecoveryError',
      message: `Recovery failed: ${recoveryError.message}`,
      type: StreamingErrorType.UNKNOWN,
      recoverable: false,
      context: originalError.context,
    } as StreamingError
  }

  private createStreamingError(error: any, context?: any): StreamingError {
    return {
      name: 'StreamingError',
      message: error.message || 'Unknown streaming error',
      type: StreamingErrorType.UNKNOWN,
      recoverable: true,
      context,
    } as StreamingError
  }

  /**
   * Get recovery history for a request
   */
  getRecoveryHistory(requestId: string): RecoveryAttempt[] {
    return this.recoveryHistory.get(requestId) || []
  }

  /**
   * Clear recovery history for a request
   */
  clearRecoveryHistory(requestId: string): void {
    this.recoveryHistory.delete(requestId)
  }
}

export const errorRecovery = new StreamingErrorRecoveryService()
```

### **Step 3: Enhanced Streaming Hook with Recovery**

```typescript
// src/hooks/useStreamingWithRecovery.ts
import { useRef, useState, useCallback } from 'react'
import { errorRecovery } from '../services/streamingErrorRecovery'
import { StreamingError, RecoveryStrategy } from '../types/streamingErrors'

interface StreamingRecoveryState {
  isRecovering: boolean
  recoveryStrategy?: RecoveryStrategy
  recoveryAttempts: number
  partialContent?: string
  lastError?: StreamingError
}

export const useStreamingWithRecovery = () => {
  const [recoveryState, setRecoveryState] = useState<StreamingRecoveryState>({
    isRecovering: false,
    recoveryAttempts: 0,
  })

  const currentRequestId = useRef<string>()
  const streamContent = useRef<string>('')

  const handleStreamingError = useCallback(async (
    error: StreamingError,
    originalRetryFunction: () => Promise<any>
  ): Promise<{ recovered: boolean; content?: string }> => {
    console.log('🚨 Handling streaming error:', error)

    // Analyze error and get recovery strategy
    const strategy = errorRecovery.analyzeError(error)
    
    setRecoveryState(prev => ({
      ...prev,
      isRecovering: true,
      recoveryStrategy: strategy,
      recoveryAttempts: prev.recoveryAttempts + 1,
      partialContent: error.partialContent,
      lastError: error,
    }))

    try {
      // Execute recovery
      const result = await errorRecovery.executeRecovery(
        strategy,
        error,
        originalRetryFunction
      )

      if (result.success) {
        setRecoveryState(prev => ({
          ...prev,
          isRecovering: false,
          recoveryStrategy: undefined,
          partialContent: result.content,
        }))

        return { recovered: true, content: result.content }
      } else {
        // Recovery failed
        setRecoveryState(prev => ({
          ...prev,
          isRecovering: false,
          lastError: result.newError || error,
        }))

        return { recovered: false }
      }
    } catch (recoveryError) {
      console.error('Recovery execution failed:', recoveryError)
      
      setRecoveryState(prev => ({
        ...prev,
        isRecovering: false,
        lastError: error,
      }))

      return { recovered: false }
    }
  }, [])

  const clearRecoveryState = useCallback(() => {
    setRecoveryState({
      isRecovering: false,
      recoveryAttempts: 0,
    })
    
    if (currentRequestId.current) {
      errorRecovery.clearRecoveryHistory(currentRequestId.current)
    }
  }, [])

  const retryWithRecovery = useCallback(async (
    retryFunction: () => Promise<any>
  ): Promise<any> => {
    if (!recoveryState.lastError) {
      throw new Error('No error to retry from')
    }

    return handleStreamingError(recoveryState.lastError, retryFunction)
  }, [recoveryState.lastError, handleStreamingError])

  return {
    recoveryState,
    handleStreamingError,
    clearRecoveryState,
    retryWithRecovery,
  }
}
```

### **Step 4: Error Recovery UI Components**

```typescript
// src/components/StreamingErrorRecovery.tsx
import React from 'react'
import { RefreshCw, AlertTriangle, CheckCircle, Clock, X } from 'lucide-react'
import { RecoveryStrategy, StreamingError } from '../types/streamingErrors'

interface StreamingErrorRecoveryProps {
  error: StreamingError
  strategy?: RecoveryStrategy
  isRecovering: boolean
  recoveryAttempts: number
  partialContent?: string
  onRetry: () => void
  onAcceptPartial?: () => void
  onCancel: () => void
  className?: string
}

export const StreamingErrorRecovery: React.FC<StreamingErrorRecoveryProps> = ({
  error,
  strategy,
  isRecovering,
  recoveryAttempts,
  partialContent,
  onRetry,
  onAcceptPartial,
  onCancel,
  className = '',
}) => {
  const getErrorIcon = () => {
    switch (error.type) {
      case 'connection_lost':
      case 'stream_interrupted':
        return <AlertTriangle className="w-5 h-5 text-yellow-600" />
      case 'timeout':
        return <Clock className="w-5 h-5 text-orange-600" />
      case 'server_error':
      case 'protocol_error':
        return <X className="w-5 h-5 text-red-600" />
      default:
        return <AlertTriangle className="w-5 h-5 text-gray-600" />
    }
  }

  const getBackgroundColor = () => {
    if (strategy?.type === 'fallback' || strategy?.type === 'partial_recovery') {
      return 'bg-yellow-50 border-yellow-200'
    }
    if (strategy?.type === 'fail') {
      return 'bg-red-50 border-red-200'
    }
    return 'bg-blue-50 border-blue-200'
  }

  return (
    <div className={`streaming-error-recovery border-2 rounded-lg p-4 ${getBackgroundColor()} ${className}`}>
      <div className="flex items-start gap-3">
        {getErrorIcon()}
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <h3 className="font-semibold text-gray-800">
              {error.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </h3>
            {recoveryAttempts > 0 && (
              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                Attempt #{recoveryAttempts}
              </span>
            )}
          </div>

          <p className="text-gray-700 mb-3">
            {strategy?.userMessage || error.message}
          </p>

          {/* Show partial content if available */}
          {partialContent && strategy?.type === 'partial_recovery' && (
            <div className="mb-4 p-3 bg-white bg-opacity-50 rounded border-l-4 border-yellow-400">
              <div className="text-sm font-medium text-gray-800 mb-2">
                Partial Response Available:
              </div>
              <div className="text-sm text-gray-700 max-h-32 overflow-y-auto">
                {partialContent.length > 200 
                  ? `${partialContent.substring(0, 200)}...` 
                  : partialContent}
              </div>
            </div>
          )}

          {/* Recovery actions */}
          <div className="flex flex-wrap gap-2">
            {strategy?.type === 'retry' && (
              <button
                onClick={onRetry}
                disabled={isRecovering}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${isRecovering ? 'animate-spin' : ''}`} />
                {isRecovering ? 'Retrying...' : (strategy.actionLabel || 'Retry')}
              </button>
            )}

            {strategy?.type === 'partial_recovery' && (
              <>
                <button
                  onClick={onRetry}
                  disabled={isRecovering}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                >
                  <RefreshCw className={`w-4 h-4 ${isRecovering ? 'animate-spin' : ''}`} />
                  {isRecovering ? 'Retrying...' : 'Retry for Full Response'}
                </button>
                
                {onAcceptPartial && (
                  <button
                    onClick={onAcceptPartial}
                    className="flex items-center gap-2 px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700"
                  >
                    <CheckCircle className="w-4 h-4" />
                    Accept Partial Response
                  </button>
                )}
              </>
            )}

            {strategy?.type === 'fallback' && onAcceptPartial && (
              <button
                onClick={onAcceptPartial}
                className="flex items-center gap-2 px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700"
              >
                <CheckCircle className="w-4 h-4" />
                Accept Response
              </button>
            )}

            {strategy?.type === 'user_action' && (
              <button
                onClick={onCancel}
                className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
              >
                {strategy.actionLabel || 'Try Again'}
              </button>
            )}

            <button
              onClick={onCancel}
              className="px-3 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded"
            >
              Cancel
            </button>
          </div>

          {/* Recovery countdown */}
          {isRecovering && strategy?.retryDelay && (
            <div className="mt-3 text-sm text-gray-600">
              <CountdownTimer 
                duration={strategy.retryDelay}
                onComplete={() => {}}
                label="Retrying in"
              />
            </div>
          )}

          {/* Technical details for debugging */}
          {process.env.NODE_ENV === 'development' && (
            <details className="mt-4 text-xs">
              <summary className="cursor-pointer text-gray-500">
                Technical Details
              </summary>
              <div className="mt-2 bg-gray-100 p-2 rounded">
                <div><strong>Error Type:</strong> {error.type}</div>
                <div><strong>Recoverable:</strong> {error.recoverable ? 'Yes' : 'No'}</div>
                {error.context && (
                  <div><strong>Context:</strong> {JSON.stringify(error.context, null, 2)}</div>
                )}
                {strategy && (
                  <div><strong>Recovery Strategy:</strong> {strategy.type}</div>
                )}
              </div>
            </details>
          )}
        </div>
      </div>
    </div>
  )
}

// Countdown timer component
const CountdownTimer: React.FC<{
  duration: number
  onComplete: () => void
  label?: string
}> = ({ duration, onComplete, label = 'Time remaining' }) => {
  const [timeLeft, setTimeLeft] = React.useState(Math.ceil(duration / 1000))

  React.useEffect(() => {
    if (timeLeft <= 0) {
      onComplete()
      return
    }

    const timer = setTimeout(() => {
      setTimeLeft(prev => prev - 1)
    }, 1000)

    return () => clearTimeout(timer)
  }, [timeLeft, onComplete])

  return (
    <span>
      {label}: {timeLeft}s
    </span>
  )
}
```

### **Step 5: Integration with Streaming Chat**

```typescript
// Enhanced StreamingChatContainer with error recovery
export const StreamingChatContainer: React.FC = () => {
  const { streamMessage, isLoading, error } = useStreamingOrchestrator()
  const { recoveryState, handleStreamingError, clearRecoveryState, retryWithRecovery } = useStreamingWithRecovery()
  
  const handleSubmit = async (query: string) => {
    try {
      clearRecoveryState()
      await streamMessage(query)
    } catch (error) {
      // Convert to StreamingError and attempt recovery
      const streamingError: StreamingError = {
        name: 'StreamingError',
        message: error.message,
        type: 'unknown', // This would be determined by error analysis
        recoverable: true,
        context: { query, requestId: Date.now().toString() },
      }

      const recovery = await handleStreamingError(streamingError, () => streamMessage(query))
      
      if (!recovery.recovered) {
        // Show error recovery UI
        console.error('Failed to recover from streaming error')
      }
    }
  }

  return (
    <div className="streaming-chat-container">
      {/* Error recovery UI */}
      {recoveryState.lastError && (
        <StreamingErrorRecovery
          error={recoveryState.lastError}
          strategy={recoveryState.recoveryStrategy}
          isRecovering={recoveryState.isRecovering}
          recoveryAttempts={recoveryState.recoveryAttempts}
          partialContent={recoveryState.partialContent}
          onRetry={() => retryWithRecovery(() => streamMessage('previous query'))}
          onAcceptPartial={() => {
            // Accept partial content and clear error state
            if (recoveryState.partialContent) {
              // Add partial content to messages
              clearRecoveryState()
            }
          }}
          onCancel={clearRecoveryState}
          className="mb-4"
        />
      )}

      {/* Rest of chat interface */}
    </div>
  )
}
```

## 🎯 **Key Takeaways**

1. **Classify errors by recoverability** - Different errors need different recovery strategies
2. **Preserve partial content** - Don't lose what the user has already received
3. **Exponential backoff prevents spam** - Smart retry timing reduces server load
4. **User choice is important** - Let users decide between retry or accepting partial content
5. **Visual feedback during recovery** - Show progress and countdown timers
6. **Fallback mechanisms prevent total failure** - Always have a way to show something useful
7. **Recovery history helps debugging** - Track what recovery strategies work best

---

**Next**: [07-streaming-optimization-techniques.md](./07-streaming-optimization-techniques.md) - Performance Optimization

**Previous**: [05-phase-tracking-indicators.md](./05-phase-tracking-indicators.md)