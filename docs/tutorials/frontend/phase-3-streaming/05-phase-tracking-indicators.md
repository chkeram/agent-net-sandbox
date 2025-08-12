# Phase 3.5: Phase Tracking Indicators - Advanced Loading States

## 🎯 **Learning Objectives**

By the end of this tutorial, you will:
- Build sophisticated loading states that show multi-step processing phases
- Implement phase tracking for orchestrator routing and agent processing
- Create visual progress indicators that enhance user understanding
- Handle phase transitions smoothly with animations and state management
- Build timeout handling and error states for each processing phase

## 📊 **The Multi-Phase Processing Challenge**

Modern agent orchestration involves multiple processing phases:
- **Discovery**: Finding the right agent for the task
- **Routing**: Sending the request to the selected agent
- **Processing**: Agent working on the response
- **Streaming**: Content being delivered back to user
- **Completion**: Final response assembled and displayed

**Our goal**: Create **transparent, informative loading states** that show users exactly what's happening at each step.

## 🎨 **Phase Tracking Architecture**

### **Step 1: Phase State Management**

```typescript
// src/types/phaseTracking.ts
export enum ProcessingPhase {
  IDLE = 'idle',
  DISCOVERY = 'discovery',
  ROUTING = 'routing', 
  PROCESSING = 'processing',
  STREAMING = 'streaming',
  COMPLETING = 'completing',
  COMPLETED = 'completed',
  ERROR = 'error',
  TIMEOUT = 'timeout'
}

export interface PhaseInfo {
  phase: ProcessingPhase
  startTime: Date
  duration?: number
  progress?: number // 0-100
  description: string
  details?: string
  agentInfo?: {
    id: string
    name: string
    protocol: string
  }
}

export interface PhaseTrackingState {
  currentPhase: ProcessingPhase
  phases: Map<ProcessingPhase, PhaseInfo>
  totalStartTime: Date
  totalDuration?: number
  estimatedCompletion?: Date
  confidence: number
  hasError: boolean
  errorDetails?: string
}
```

### **Step 2: Phase Tracking Service**

```typescript
// src/services/phaseTracker.ts
interface PhaseTrackerConfig {
  phaseTimeouts: Record<ProcessingPhase, number>
  enableProgressEstimation: boolean
  enablePerformanceTracking: boolean
}

export class PhaseTrackerService {
  private config: PhaseTrackerConfig
  private trackingState: PhaseTrackingState
  private subscribers = new Set<(state: PhaseTrackingState) => void>()
  private phaseTimeouts = new Map<ProcessingPhase, number>()
  private performanceHistory = new Map<ProcessingPhase, number[]>()

  constructor(config: Partial<PhaseTrackerConfig> = {}) {
    this.config = {
      phaseTimeouts: {
        [ProcessingPhase.IDLE]: 0,
        [ProcessingPhase.DISCOVERY]: 5000,      // 5 seconds
        [ProcessingPhase.ROUTING]: 3000,       // 3 seconds  
        [ProcessingPhase.PROCESSING]: 30000,   // 30 seconds
        [ProcessingPhase.STREAMING]: 60000,    // 60 seconds
        [ProcessingPhase.COMPLETING]: 5000,    // 5 seconds
        [ProcessingPhase.COMPLETED]: 0,
        [ProcessingPhase.ERROR]: 0,
        [ProcessingPhase.TIMEOUT]: 0,
      },
      enableProgressEstimation: true,
      enablePerformanceTracking: true,
      ...config,
    }

    this.trackingState = this.createInitialState()
  }

  /**
   * Start tracking a new request
   */
  startTracking(requestId?: string): void {
    this.trackingState = this.createInitialState()
    this.trackingState.totalStartTime = new Date()
    
    // Start with discovery phase
    this.setPhase(ProcessingPhase.DISCOVERY, {
      description: 'Finding the right agent for your request...',
      details: 'Analyzing query and matching capabilities'
    })

    console.log('🔄 Phase tracking started for request:', requestId)
  }

  /**
   * Set current processing phase
   */
  setPhase(
    phase: ProcessingPhase, 
    options: {
      description?: string
      details?: string
      progress?: number
      agentInfo?: { id: string; name: string; protocol: string }
    } = {}
  ): void {
    const now = new Date()
    
    // Complete previous phase
    if (this.trackingState.currentPhase !== ProcessingPhase.IDLE) {
      this.completeCurrentPhase()
    }

    // Set new phase
    const phaseInfo: PhaseInfo = {
      phase,
      startTime: now,
      progress: options.progress,
      description: options.description || this.getDefaultDescription(phase),
      details: options.details,
      agentInfo: options.agentInfo,
    }

    this.trackingState.currentPhase = phase
    this.trackingState.phases.set(phase, phaseInfo)

    // Set up timeout if applicable
    this.setupPhaseTimeout(phase)

    // Update confidence and estimation
    this.updateProgressEstimation()

    // Notify subscribers
    this.notifySubscribers()

    console.log(`📍 Phase changed to ${phase}:`, phaseInfo.description)
  }

  /**
   * Update current phase progress
   */
  updatePhaseProgress(progress: number, details?: string): void {
    const currentPhaseInfo = this.trackingState.phases.get(this.trackingState.currentPhase)
    if (currentPhaseInfo) {
      currentPhaseInfo.progress = Math.max(0, Math.min(100, progress))
      if (details) {
        currentPhaseInfo.details = details
      }

      this.updateProgressEstimation()
      this.notifySubscribers()
    }
  }

  /**
   * Mark processing as completed successfully
   */
  complete(): void {
    this.completeCurrentPhase()
    
    const now = new Date()
    this.trackingState.currentPhase = ProcessingPhase.COMPLETED
    this.trackingState.totalDuration = now.getTime() - this.trackingState.totalStartTime.getTime()
    
    this.trackingState.phases.set(ProcessingPhase.COMPLETED, {
      phase: ProcessingPhase.COMPLETED,
      startTime: now,
      duration: 0,
      progress: 100,
      description: 'Response completed successfully',
      details: `Total time: ${(this.trackingState.totalDuration / 1000).toFixed(1)}s`,
    })

    // Update performance history
    if (this.config.enablePerformanceTracking) {
      this.updatePerformanceHistory()
    }

    this.clearTimeouts()
    this.notifySubscribers()

    console.log('✅ Phase tracking completed:', {
      totalDuration: this.trackingState.totalDuration,
      phases: Array.from(this.trackingState.phases.keys())
    })
  }

  /**
   * Mark processing as failed
   */
  error(errorMessage: string, phase?: ProcessingPhase): void {
    this.completeCurrentPhase()
    
    const failedPhase = phase || this.trackingState.currentPhase
    const now = new Date()

    this.trackingState.currentPhase = ProcessingPhase.ERROR
    this.trackingState.hasError = true
    this.trackingState.errorDetails = errorMessage
    this.trackingState.totalDuration = now.getTime() - this.trackingState.totalStartTime.getTime()

    this.trackingState.phases.set(ProcessingPhase.ERROR, {
      phase: ProcessingPhase.ERROR,
      startTime: now,
      duration: 0,
      progress: 0,
      description: `Error during ${failedPhase} phase`,
      details: errorMessage,
    })

    this.clearTimeouts()
    this.notifySubscribers()

    console.error('❌ Phase tracking error:', { phase: failedPhase, error: errorMessage })
  }

  /**
   * Subscribe to phase tracking updates
   */
  subscribe(callback: (state: PhaseTrackingState) => void): () => void {
    this.subscribers.add(callback)
    return () => this.subscribers.delete(callback)
  }

  /**
   * Get current tracking state
   */
  getState(): PhaseTrackingState {
    return { ...this.trackingState }
  }

  private createInitialState(): PhaseTrackingState {
    return {
      currentPhase: ProcessingPhase.IDLE,
      phases: new Map(),
      totalStartTime: new Date(),
      confidence: 1.0,
      hasError: false,
    }
  }

  private completeCurrentPhase(): void {
    const currentPhaseInfo = this.trackingState.phases.get(this.trackingState.currentPhase)
    if (currentPhaseInfo && !currentPhaseInfo.duration) {
      const now = new Date()
      currentPhaseInfo.duration = now.getTime() - currentPhaseInfo.startTime.getTime()
      currentPhaseInfo.progress = 100
    }
  }

  private setupPhaseTimeout(phase: ProcessingPhase): void {
    const timeoutMs = this.config.phaseTimeouts[phase]
    if (timeoutMs > 0) {
      const timeoutId = window.setTimeout(() => {
        if (this.trackingState.currentPhase === phase) {
          this.handlePhaseTimeout(phase)
        }
      }, timeoutMs)
      
      this.phaseTimeouts.set(phase, timeoutId)
    }
  }

  private handlePhaseTimeout(phase: ProcessingPhase): void {
    const phaseInfo = this.trackingState.phases.get(phase)
    if (phaseInfo) {
      this.error(`${phase} phase timed out after ${this.config.phaseTimeouts[phase]/1000}s`, phase)
    }
  }

  private clearTimeouts(): void {
    this.phaseTimeouts.forEach(timeoutId => clearTimeout(timeoutId))
    this.phaseTimeouts.clear()
  }

  private getDefaultDescription(phase: ProcessingPhase): string {
    switch (phase) {
      case ProcessingPhase.DISCOVERY:
        return 'Finding the right agent for your request...'
      case ProcessingPhase.ROUTING:
        return 'Routing your request to the selected agent...'
      case ProcessingPhase.PROCESSING:
        return 'Agent is processing your request...'
      case ProcessingPhase.STREAMING:
        return 'Receiving response from agent...'
      case ProcessingPhase.COMPLETING:
        return 'Finalizing response...'
      case ProcessingPhase.COMPLETED:
        return 'Response completed successfully'
      case ProcessingPhase.ERROR:
        return 'An error occurred during processing'
      case ProcessingPhase.TIMEOUT:
        return 'Request timed out'
      default:
        return 'Processing...'
    }
  }

  private updateProgressEstimation(): void {
    if (!this.config.enableProgressEstimation) return

    // Estimate completion based on current phase and historical data
    const phaseWeights = {
      [ProcessingPhase.DISCOVERY]: 0.1,
      [ProcessingPhase.ROUTING]: 0.1,
      [ProcessingPhase.PROCESSING]: 0.6,
      [ProcessingPhase.STREAMING]: 0.2,
      [ProcessingPhase.COMPLETING]: 0.0,
    }

    let totalProgress = 0
    let completedWeight = 0

    for (const [phase, info] of this.trackingState.phases) {
      const weight = phaseWeights[phase] || 0
      if (info.duration !== undefined) {
        // Phase completed
        completedWeight += weight
      } else if (phase === this.trackingState.currentPhase && info.progress) {
        // Current phase with progress
        completedWeight += weight * (info.progress / 100)
      }
    }

    totalProgress = completedWeight * 100

    // Estimate completion time based on historical data
    if (this.config.enablePerformanceTracking) {
      const avgDuration = this.getAverageProcessingTime()
      if (avgDuration > 0) {
        const elapsed = new Date().getTime() - this.trackingState.totalStartTime.getTime()
        const estimatedTotal = avgDuration
        const estimatedCompletion = new Date(this.trackingState.totalStartTime.getTime() + estimatedTotal)
        
        this.trackingState.estimatedCompletion = estimatedCompletion
        this.trackingState.confidence = Math.max(0.3, Math.min(1.0, 1 - (elapsed / estimatedTotal)))
      }
    }
  }

  private getAverageProcessingTime(): number {
    const allDurations: number[] = []
    this.performanceHistory.forEach(durations => allDurations.push(...durations))
    
    if (allDurations.length === 0) return 0
    
    return allDurations.reduce((sum, duration) => sum + duration, 0) / allDurations.length
  }

  private updatePerformanceHistory(): void {
    // Record performance for each completed phase
    this.trackingState.phases.forEach((info, phase) => {
      if (info.duration && phase !== ProcessingPhase.COMPLETED) {
        const history = this.performanceHistory.get(phase) || []
        history.push(info.duration)
        
        // Keep only last 20 measurements
        if (history.length > 20) {
          history.shift()
        }
        
        this.performanceHistory.set(phase, history)
      }
    })

    // Record total duration
    if (this.trackingState.totalDuration) {
      const totalHistory = this.performanceHistory.get(ProcessingPhase.COMPLETED) || []
      totalHistory.push(this.trackingState.totalDuration)
      
      if (totalHistory.length > 20) {
        totalHistory.shift()
      }
      
      this.performanceHistory.set(ProcessingPhase.COMPLETED, totalHistory)
    }
  }

  private notifySubscribers(): void {
    this.subscribers.forEach(callback => {
      try {
        callback(this.trackingState)
      } catch (error) {
        console.error('Phase tracker subscriber error:', error)
      }
    })
  }
}

export const phaseTracker = new PhaseTrackerService()
```

### **Step 3: Phase Tracking React Hook**

```typescript
// src/hooks/usePhaseTracking.ts
import { useState, useEffect, useCallback } from 'react'
import { phaseTracker } from '../services/phaseTracker'
import { PhaseTrackingState, ProcessingPhase } from '../types/phaseTracking'

export const usePhaseTracking = () => {
  const [state, setState] = useState<PhaseTrackingState>(() => phaseTracker.getState())

  useEffect(() => {
    const unsubscribe = phaseTracker.subscribe(setState)
    return unsubscribe
  }, [])

  const startTracking = useCallback((requestId?: string) => {
    phaseTracker.startTracking(requestId)
  }, [])

  const setPhase = useCallback((
    phase: ProcessingPhase,
    options?: {
      description?: string
      details?: string
      progress?: number
      agentInfo?: { id: string; name: string; protocol: string }
    }
  ) => {
    phaseTracker.setPhase(phase, options)
  }, [])

  const updateProgress = useCallback((progress: number, details?: string) => {
    phaseTracker.updatePhaseProgress(progress, details)
  }, [])

  const complete = useCallback(() => {
    phaseTracker.complete()
  }, [])

  const error = useCallback((errorMessage: string, phase?: ProcessingPhase) => {
    phaseTracker.error(errorMessage, phase)
  }, [])

  return {
    state,
    startTracking,
    setPhase,
    updateProgress,
    complete,
    error,
    isProcessing: state.currentPhase !== ProcessingPhase.IDLE && 
                  state.currentPhase !== ProcessingPhase.COMPLETED && 
                  state.currentPhase !== ProcessingPhase.ERROR,
    hasError: state.hasError,
    isCompleted: state.currentPhase === ProcessingPhase.COMPLETED,
  }
}
```

### **Step 4: Phase Indicator Components**

```typescript
// src/components/PhaseTrackingIndicator.tsx
import React from 'react'
import { Search, ArrowRight, Cpu, Download, CheckCircle, AlertCircle, Clock } from 'lucide-react'
import { PhaseTrackingState, ProcessingPhase } from '../types/phaseTracking'

interface PhaseTrackingIndicatorProps {
  state: PhaseTrackingState
  compact?: boolean
  showDetails?: boolean
  className?: string
}

export const PhaseTrackingIndicator: React.FC<PhaseTrackingIndicatorProps> = ({
  state,
  compact = false,
  showDetails = true,
  className = '',
}) => {
  const getPhaseIcon = (phase: ProcessingPhase) => {
    switch (phase) {
      case ProcessingPhase.DISCOVERY:
        return <Search className="w-4 h-4" />
      case ProcessingPhase.ROUTING:
        return <ArrowRight className="w-4 h-4" />
      case ProcessingPhase.PROCESSING:
        return <Cpu className="w-4 h-4" />
      case ProcessingPhase.STREAMING:
        return <Download className="w-4 h-4" />
      case ProcessingPhase.COMPLETING:
      case ProcessingPhase.COMPLETED:
        return <CheckCircle className="w-4 h-4" />
      case ProcessingPhase.ERROR:
      case ProcessingPhase.TIMEOUT:
        return <AlertCircle className="w-4 h-4" />
      default:
        return <Clock className="w-4 h-4" />
    }
  }

  const getPhaseStatus = (phase: ProcessingPhase): 'pending' | 'active' | 'completed' | 'error' => {
    if (state.hasError && (phase === ProcessingPhase.ERROR || phase === ProcessingPhase.TIMEOUT)) {
      return 'error'
    }
    
    if (state.phases.has(phase)) {
      const phaseInfo = state.phases.get(phase)!
      if (phaseInfo.duration !== undefined || phase === ProcessingPhase.COMPLETED) {
        return 'completed'
      }
      if (phase === state.currentPhase) {
        return 'active'
      }
    }
    
    return 'pending'
  }

  const renderPhaseItem = (phase: ProcessingPhase, label: string) => {
    const status = getPhaseStatus(phase)
    const phaseInfo = state.phases.get(phase)
    
    const statusStyles = {
      pending: 'text-gray-400 bg-gray-100',
      active: 'text-blue-600 bg-blue-100 animate-pulse',
      completed: 'text-green-600 bg-green-100',
      error: 'text-red-600 bg-red-100',
    }

    return (
      <div key={phase} className={`flex items-center gap-3 ${compact ? 'py-1' : 'py-2'}`}>
        <div className={`flex items-center justify-center w-8 h-8 rounded-full ${statusStyles[status]}`}>
          {getPhaseIcon(phase)}
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={`font-medium text-sm ${
              status === 'active' ? 'text-blue-800' :
              status === 'completed' ? 'text-green-800' :
              status === 'error' ? 'text-red-800' :
              'text-gray-600'
            }`}>
              {label}
            </span>
            
            {status === 'active' && phaseInfo?.progress !== undefined && (
              <span className="text-xs text-blue-600 font-medium">
                {Math.round(phaseInfo.progress)}%
              </span>
            )}
            
            {status === 'completed' && phaseInfo?.duration && (
              <span className="text-xs text-green-600">
                {(phaseInfo.duration / 1000).toFixed(1)}s
              </span>
            )}
          </div>
          
          {showDetails && phaseInfo && (
            <div className="text-xs text-gray-500 mt-1">
              {status === 'active' && phaseInfo.details ? phaseInfo.details : phaseInfo.description}
            </div>
          )}
          
          {/* Progress bar for active phase */}
          {status === 'active' && phaseInfo?.progress !== undefined && !compact && (
            <div className="mt-2 w-full bg-gray-200 rounded-full h-1.5">
              <div 
                className="bg-blue-500 h-1.5 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${phaseInfo.progress}%` }}
              />
            </div>
          )}
        </div>
      </div>
    )
  }

  if (compact) {
    // Compact view - show only current phase
    const currentPhaseInfo = state.phases.get(state.currentPhase)
    
    return (
      <div className={`phase-tracking-compact flex items-center gap-2 ${className}`}>
        <div className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-600">
          {getPhaseIcon(state.currentPhase)}
        </div>
        <span className="text-sm text-gray-600">
          {currentPhaseInfo?.description || 'Processing...'}
        </span>
        {currentPhaseInfo?.progress !== undefined && (
          <span className="text-xs text-blue-600 font-medium">
            {Math.round(currentPhaseInfo.progress)}%
          </span>
        )}
      </div>
    )
  }

  const phases = [
    { phase: ProcessingPhase.DISCOVERY, label: 'Agent Discovery' },
    { phase: ProcessingPhase.ROUTING, label: 'Request Routing' },
    { phase: ProcessingPhase.PROCESSING, label: 'Processing' },
    { phase: ProcessingPhase.STREAMING, label: 'Streaming Response' },
    { phase: ProcessingPhase.COMPLETING, label: 'Completing' },
  ]

  return (
    <div className={`phase-tracking-indicator bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-800">Processing Status</h3>
        {state.estimatedCompletion && !state.hasError && (
          <div className="text-xs text-gray-500">
            ETA: {state.estimatedCompletion.toLocaleTimeString()}
          </div>
        )}
      </div>

      <div className="space-y-1">
        {phases.map(({ phase, label }) => renderPhaseItem(phase, label))}
        
        {state.hasError && renderPhaseItem(ProcessingPhase.ERROR, 'Error')}
        {!state.hasError && state.currentPhase === ProcessingPhase.COMPLETED && 
         renderPhaseItem(ProcessingPhase.COMPLETED, 'Completed')}
      </div>

      {/* Overall progress bar */}
      {!state.hasError && state.currentPhase !== ProcessingPhase.COMPLETED && (
        <div className="mt-4 pt-3 border-t border-gray-100">
          <div className="flex items-center justify-between text-xs text-gray-500 mb-2">
            <span>Overall Progress</span>
            <span>
              {state.confidence && `${Math.round(state.confidence * 100)}% confident`}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full transition-all duration-1000 ease-out"
              style={{ width: `${calculateOverallProgress(state)}%` }}
            />
          </div>
        </div>
      )}

      {/* Agent info if available */}
      {state.phases.get(state.currentPhase)?.agentInfo && (
        <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-600">
          <div className="flex items-center gap-2">
            <span>Agent:</span>
            <span className="font-medium">
              {state.phases.get(state.currentPhase)?.agentInfo?.name}
            </span>
            <span className="px-2 py-1 bg-gray-100 rounded text-xs">
              {state.phases.get(state.currentPhase)?.agentInfo?.protocol?.toUpperCase()}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

function calculateOverallProgress(state: PhaseTrackingState): number {
  const phaseWeights = {
    [ProcessingPhase.DISCOVERY]: 10,
    [ProcessingPhase.ROUTING]: 10,
    [ProcessingPhase.PROCESSING]: 60,
    [ProcessingPhase.STREAMING]: 20,
  }

  let totalProgress = 0
  
  for (const [phase, info] of state.phases) {
    const weight = phaseWeights[phase] || 0
    if (info.duration !== undefined) {
      // Phase completed
      totalProgress += weight
    } else if (phase === state.currentPhase && info.progress !== undefined) {
      // Current phase with progress
      totalProgress += weight * (info.progress / 100)
    }
  }

  return Math.min(95, totalProgress) // Cap at 95% until actually completed
}
```

### **Step 5: Integration with Streaming Hook**

```typescript
// src/hooks/useStreamingOrchestrator.ts - Enhanced with phase tracking
import { usePhaseTracking } from './usePhaseTracking'

export const useStreamingOrchestrator = () => {
  const phaseTracking = usePhaseTracking()
  
  // ... existing hook logic ...

  const streamMessage = async (
    query: string,
    callbacks: StreamingCallbacks = {}
  ): Promise<ProcessResponse | null> => {
    if (isStreaming.current) {
      console.warn('Already streaming, ignoring new request')
      return null
    }

    // Start phase tracking
    phaseTracking.startTracking()

    try {
      setIsLoading(true)
      setError(null)
      isStreaming.current = true

      // Phase: Discovery (simulated - orchestrator handles this)
      phaseTracking.setPhase(ProcessingPhase.DISCOVERY, {
        description: 'Analyzing your request and finding the best agent...',
        details: 'Matching capabilities and protocols',
        progress: 20
      })

      // Start the stream
      await streamingApi.processMessage(query, {
        onStart: () => {
          // Phase: Routing
          phaseTracking.setPhase(ProcessingPhase.ROUTING, {
            description: 'Routing your request to the selected agent...',
            progress: 0
          })
          callbacks.onStart?.()
        },

        onData: (chunk) => {
          // Phase: Streaming (first chunk transitions from processing)
          if (phaseTracking.state.currentPhase !== ProcessingPhase.STREAMING) {
            phaseTracking.setPhase(ProcessingPhase.STREAMING, {
              description: 'Receiving response from agent...',
              progress: 10
            })
          }

          // Update progress based on content length (rough estimate)
          const currentContent = streamContent.current + chunk
          const estimatedProgress = Math.min(90, (currentContent.length / 500) * 100)
          phaseTracking.updateProgress(estimatedProgress, `Received ${currentContent.length} characters`)

          streamContent.current += chunk
          callbacks.onData?.(chunk)
        },

        onAgentInfo: (agentInfo) => {
          // Update routing phase with agent info
          phaseTracking.setPhase(ProcessingPhase.PROCESSING, {
            description: `${agentInfo.name} is processing your request...`,
            details: `Using ${agentInfo.protocol.toUpperCase()} protocol`,
            agentInfo: {
              id: agentInfo.id,
              name: agentInfo.name,
              protocol: agentInfo.protocol
            },
            progress: 0
          })
          callbacks.onAgentInfo?.(agentInfo)
        },

        onComplete: (response) => {
          // Phase: Completing
          phaseTracking.setPhase(ProcessingPhase.COMPLETING, {
            description: 'Finalizing response...',
            progress: 90
          })

          setTimeout(() => {
            phaseTracking.complete()
          }, 500) // Small delay for visual feedback

          setResponse(response)
          setIsLoading(false)
          isStreaming.current = false
          callbacks.onComplete?.(response)
        },

        onError: (error) => {
          phaseTracking.error(error.message)
          setError(error)
          setIsLoading(false)  
          isStreaming.current = false
          callbacks.onError?.(error)
        }
      })

      return response
      
    } catch (error) {
      phaseTracking.error((error as Error).message)
      setError(error as Error)
      setIsLoading(false)
      isStreaming.current = false
      throw error
    }
  }

  return {
    // ... existing returns ...
    phaseTracking: phaseTracking.state,
    isProcessing: phaseTracking.isProcessing,
  }
}
```

## 🎯 **Usage Examples**

### **In Chat Components**
```typescript
// Usage in StreamingChatContainer
const { streamMessage, phaseTracking } = useStreamingOrchestrator()

return (
  <div className="streaming-chat-container">
    {phaseTracking.currentPhase !== ProcessingPhase.IDLE && 
     phaseTracking.currentPhase !== ProcessingPhase.COMPLETED && (
      <PhaseTrackingIndicator 
        state={phaseTracking}
        showDetails={true}
        className="mb-4"
      />
    )}
    
    {/* Chat messages */}
    {messages.map(message => (
      <MessageComponent key={message.id} message={message} />
    ))}
  </div>
)
```

### **Compact Mode for Mobile**
```typescript
// Mobile-friendly compact indicator
<PhaseTrackingIndicator 
  state={phaseTracking}
  compact={true}
  showDetails={false}
  className="fixed bottom-20 left-4 right-4 bg-white shadow-lg rounded-lg px-3 py-2"
/>
```

## 🎯 **Key Takeaways**

1. **Transparency builds trust** - Users appreciate knowing what's happening
2. **Phase estimation improves UX** - Show progress and estimated completion times
3. **Timeout handling is crucial** - Don't leave users hanging indefinitely
4. **Visual feedback matters** - Smooth transitions and animations enhance perception
5. **Mobile considerations** - Compact modes for smaller screens
6. **Performance tracking helps** - Historical data improves future estimations
7. **Error context is valuable** - Show which phase failed and why

---

**Next**: [06-error-recovery-mechanisms.md](./06-error-recovery-mechanisms.md) - Robust Error Handling

**Previous**: [04-real-time-chunk-rendering.md](./04-real-time-chunk-rendering.md)