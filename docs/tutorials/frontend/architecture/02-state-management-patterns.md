# Architecture 2: State Management Patterns - Advanced React State Design

## 🎯 **Learning Objectives**

By the end of this tutorial, you will understand:
- Advanced React state management patterns used in the Agent Network Sandbox
- How to design scalable state architecture for complex streaming applications
- When to use local vs global state vs external storage
- Performance optimization techniques for state updates
- Error boundaries and state recovery patterns
- Testing strategies for complex state logic

## 🏗️ **State Management Architecture Overview**

Our Agent Network Sandbox uses a **layered state management approach**:

```
┌─────────────────────────────────────────────┐
│              UI Components                   │ ← Local UI state
├─────────────────────────────────────────────┤
│            Custom Hooks Layer               │ ← Business logic state
├─────────────────────────────────────────────┤
│           Service Layer                     │ ← External API state
├─────────────────────────────────────────────┤
│          Storage Layer                      │ ← Persistent state
└─────────────────────────────────────────────┘
```

## 🔄 **Core State Management Patterns**

### **Pattern 1: Streaming State with Refs**

**Problem**: High-frequency streaming updates can cause excessive re-renders and block the UI.

**Solution**: Use refs for streaming data, state for UI updates.

```typescript
// src/hooks/useStreamingOrchestrator.ts - State pattern analysis
export const useStreamingOrchestrator = () => {
  // ✅ UI STATE: Triggers re-renders only when UI needs updates
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [response, setResponse] = useState<ProcessResponse | null>(null)

  // ✅ REF STATE: High-frequency updates without re-renders
  const isStreaming = useRef(false)
  const streamContent = useRef('')
  const abortController = useRef<AbortController | null>(null)

  // ✅ HYBRID PATTERN: Combine both for optimal performance
  const streamMessage = async (query: string, callbacks: StreamingCallbacks = {}) => {
    // Reset UI state
    setIsLoading(true)
    setError(null)
    setResponse(null)

    // Reset streaming refs
    isStreaming.current = true
    streamContent.current = ''

    try {
      await streamingApi.processMessage(query, {
        onData: (chunk) => {
          // Update ref (no re-render)
          streamContent.current += chunk
          
          // Callback with current data (component decides when to re-render)
          callbacks.onData?.(chunk)
        },
        onComplete: (finalResponse) => {
          // Update UI state (triggers re-render)
          setResponse(finalResponse)
          setIsLoading(false)
          isStreaming.current = false
          
          callbacks.onComplete?.(finalResponse)
        }
      })
    } catch (err) {
      // Error handling with state
      setError(err as Error)
      setIsLoading(false)
      isStreaming.current = false
    }
  }

  return {
    // UI state for components
    isLoading,
    error,
    response,
    
    // Streaming utilities
    streamMessage,
    getCurrentContent: () => streamContent.current,
    isCurrentlyStreaming: () => isStreaming.current,
  }
}
```

**Key Insights**:
- **Refs for performance**: Don't re-render on every chunk
- **State for UI**: Only update when UI actually needs to change
- **Callbacks for flexibility**: Let components control their own re-render timing

### **Pattern 2: Compound State Reducers**

**Problem**: Complex state with multiple interdependent properties needs coordinated updates.

**Solution**: Use reducer pattern for complex state transitions.

```typescript
// src/hooks/useMessageActions.ts - Reducer pattern for complex state
interface MessageActionState {
  selectedMessages: Set<string>
  actionMode: 'none' | 'copy' | 'delete' | 'export' | 'regenerate'
  isProcessing: boolean
  processingProgress: number
  error: string | null
  history: Array<{
    action: string
    messageIds: string[]
    timestamp: Date
    undoData?: any
  }>
}

type MessageActionType =
  | { type: 'SELECT_MESSAGE'; messageId: string }
  | { type: 'DESELECT_MESSAGE'; messageId: string }
  | { type: 'SELECT_ALL'; messageIds: string[] }
  | { type: 'CLEAR_SELECTION' }
  | { type: 'SET_ACTION_MODE'; mode: MessageActionState['actionMode'] }
  | { type: 'START_PROCESSING'; action: string }
  | { type: 'UPDATE_PROGRESS'; progress: number }
  | { type: 'COMPLETE_ACTION'; action: string; messageIds: string[]; undoData?: any }
  | { type: 'SET_ERROR'; error: string }
  | { type: 'CLEAR_ERROR' }
  | { type: 'UNDO_LAST_ACTION' }

const messageActionReducer = (
  state: MessageActionState,
  action: MessageActionType
): MessageActionState => {
  switch (action.type) {
    case 'SELECT_MESSAGE':
      return {
        ...state,
        selectedMessages: new Set([...state.selectedMessages, action.messageId]),
        error: null,
      }

    case 'DESELECT_MESSAGE':
      const newSelection = new Set(state.selectedMessages)
      newSelection.delete(action.messageId)
      return {
        ...state,
        selectedMessages: newSelection,
      }

    case 'SELECT_ALL':
      return {
        ...state,
        selectedMessages: new Set(action.messageIds),
        error: null,
      }

    case 'CLEAR_SELECTION':
      return {
        ...state,
        selectedMessages: new Set(),
        actionMode: 'none',
        error: null,
      }

    case 'SET_ACTION_MODE':
      return {
        ...state,
        actionMode: action.mode,
        error: null,
      }

    case 'START_PROCESSING':
      return {
        ...state,
        isProcessing: true,
        processingProgress: 0,
        error: null,
      }

    case 'UPDATE_PROGRESS':
      return {
        ...state,
        processingProgress: Math.max(0, Math.min(100, action.progress)),
      }

    case 'COMPLETE_ACTION':
      return {
        ...state,
        isProcessing: false,
        processingProgress: 100,
        selectedMessages: new Set(), // Clear selection after action
        actionMode: 'none',
        history: [
          {
            action: action.action,
            messageIds: action.messageIds,
            timestamp: new Date(),
            undoData: action.undoData,
          },
          ...state.history.slice(0, 9), // Keep last 10 actions
        ],
      }

    case 'SET_ERROR':
      return {
        ...state,
        error: action.error,
        isProcessing: false,
        processingProgress: 0,
      }

    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      }

    case 'UNDO_LAST_ACTION':
      if (state.history.length === 0) return state
      
      const lastAction = state.history[0]
      return {
        ...state,
        history: state.history.slice(1), // Remove undone action
        error: null,
        // Note: Actual undo logic would be handled in the component
      }

    default:
      return state
  }
}

export const useMessageActions = () => {
  const [state, dispatch] = useReducer(messageActionReducer, {
    selectedMessages: new Set(),
    actionMode: 'none',
    isProcessing: false,
    processingProgress: 0,
    error: null,
    history: [],
  })

  // Memoized selectors
  const selectors = useMemo(() => ({
    getSelectedCount: () => state.selectedMessages.size,
    isMessageSelected: (messageId: string) => state.selectedMessages.has(messageId),
    canUndo: () => state.history.length > 0,
    getLastAction: () => state.history[0] || null,
  }), [state.selectedMessages, state.history])

  // Action creators
  const actions = useMemo(() => ({
    selectMessage: (messageId: string) => dispatch({ type: 'SELECT_MESSAGE', messageId }),
    deselectMessage: (messageId: string) => dispatch({ type: 'DESELECT_MESSAGE', messageId }),
    selectAll: (messageIds: string[]) => dispatch({ type: 'SELECT_ALL', messageIds }),
    clearSelection: () => dispatch({ type: 'CLEAR_SELECTION' }),
    setActionMode: (mode: MessageActionState['actionMode']) => 
      dispatch({ type: 'SET_ACTION_MODE', mode }),
    startProcessing: (action: string) => dispatch({ type: 'START_PROCESSING', action }),
    updateProgress: (progress: number) => dispatch({ type: 'UPDATE_PROGRESS', progress }),
    completeAction: (action: string, messageIds: string[], undoData?: any) =>
      dispatch({ type: 'COMPLETE_ACTION', action, messageIds, undoData }),
    setError: (error: string) => dispatch({ type: 'SET_ERROR', error }),
    clearError: () => dispatch({ type: 'CLEAR_ERROR' }),
    undoLastAction: () => dispatch({ type: 'UNDO_LAST_ACTION' }),
  }), [])

  return {
    state,
    ...selectors,
    ...actions,
  }
}
```

**Key Insights**:
- **Immutable updates**: Every state change creates a new object
- **Centralized logic**: All state transitions in one place
- **Predictable updates**: Each action type has one clear outcome
- **Memoized selectors**: Prevent unnecessary re-computations

### **Pattern 3: Service Layer State Synchronization**

**Problem**: Multiple components need access to the same external data, but shouldn't duplicate API calls.

**Solution**: Service layer with state synchronization and caching.

```typescript
// src/services/conversationStateManager.ts
interface ConversationCache {
  conversations: Map<string, StoredConversation>
  messages: Map<string, StoredMessage[]>
  lastFetched: Map<string, Date>
  subscribers: Map<string, Set<(data: any) => void>>
}

export class ConversationStateManager {
  private cache: ConversationCache = {
    conversations: new Map(),
    messages: new Map(),
    lastFetched: new Map(),
    subscribers: new Map(),
  }

  private readonly CACHE_TTL = 5 * 60 * 1000 // 5 minutes

  /**
   * Subscribe to conversation updates
   */
  subscribe(conversationId: string, callback: (messages: StoredMessage[]) => void): () => void {
    if (!this.cache.subscribers.has(conversationId)) {
      this.cache.subscribers.set(conversationId, new Set())
    }

    this.cache.subscribers.get(conversationId)!.add(callback)

    // Return unsubscribe function
    return () => {
      const subscribers = this.cache.subscribers.get(conversationId)
      if (subscribers) {
        subscribers.delete(callback)
        if (subscribers.size === 0) {
          this.cache.subscribers.delete(conversationId)
        }
      }
    }
  }

  /**
   * Get messages with intelligent caching
   */
  async getMessages(conversationId: string, forceRefresh = false): Promise<StoredMessage[]> {
    const lastFetched = this.cache.lastFetched.get(conversationId)
    const isStale = !lastFetched || (Date.now() - lastFetched.getTime()) > this.CACHE_TTL

    // Return cached data if fresh
    if (!forceRefresh && !isStale && this.cache.messages.has(conversationId)) {
      return this.cache.messages.get(conversationId)!
    }

    try {
      // Fetch fresh data
      const messages = await messageStorage.loadMessages(conversationId, { limit: 1000 })
      
      // Update cache
      this.cache.messages.set(conversationId, messages)
      this.cache.lastFetched.set(conversationId, new Date())

      // Notify subscribers
      this.notifySubscribers(conversationId, messages)

      return messages
    } catch (error) {
      console.error(`Failed to load messages for ${conversationId}:`, error)
      
      // Return stale data if available
      return this.cache.messages.get(conversationId) || []
    }
  }

  /**
   * Add message with optimistic updates
   */
  async addMessage(conversationId: string, message: StoredMessage): Promise<void> {
    try {
      // Optimistic update - add to cache immediately
      const currentMessages = this.cache.messages.get(conversationId) || []
      const updatedMessages = [...currentMessages, message]
      
      this.cache.messages.set(conversationId, updatedMessages)
      this.notifySubscribers(conversationId, updatedMessages)

      // Persist to storage
      await messageStorage.saveMessage(message)

    } catch (error) {
      console.error('Failed to save message:', error)
      
      // Rollback optimistic update
      const currentMessages = this.cache.messages.get(conversationId) || []
      const rolledBackMessages = currentMessages.filter(m => m.id !== message.id)
      
      this.cache.messages.set(conversationId, rolledBackMessages)
      this.notifySubscribers(conversationId, rolledBackMessages)
      
      throw error
    }
  }

  /**
   * Update message with optimistic updates
   */
  async updateMessage(
    conversationId: string, 
    messageId: string, 
    updates: Partial<StoredMessage>
  ): Promise<void> {
    const currentMessages = this.cache.messages.get(conversationId) || []
    const messageIndex = currentMessages.findIndex(m => m.id === messageId)
    
    if (messageIndex === -1) {
      throw new Error(`Message ${messageId} not found`)
    }

    const originalMessage = currentMessages[messageIndex]
    const updatedMessage = { ...originalMessage, ...updates }

    try {
      // Optimistic update
      const updatedMessages = [...currentMessages]
      updatedMessages[messageIndex] = updatedMessage
      
      this.cache.messages.set(conversationId, updatedMessages)
      this.notifySubscribers(conversationId, updatedMessages)

      // Persist to storage
      await messageStorage.saveMessage(updatedMessage)

    } catch (error) {
      console.error('Failed to update message:', error)
      
      // Rollback optimistic update
      this.cache.messages.set(conversationId, currentMessages)
      this.notifySubscribers(conversationId, currentMessages)
      
      throw error
    }
  }

  private notifySubscribers(conversationId: string, messages: StoredMessage[]): void {
    const subscribers = this.cache.subscribers.get(conversationId)
    if (subscribers) {
      subscribers.forEach(callback => {
        try {
          callback(messages)
        } catch (error) {
          console.error('Subscriber callback error:', error)
        }
      })
    }
  }

  /**
   * Clear cache for conversation
   */
  clearCache(conversationId?: string): void {
    if (conversationId) {
      this.cache.messages.delete(conversationId)
      this.cache.lastFetched.delete(conversationId)
    } else {
      this.cache.messages.clear()
      this.cache.lastFetched.clear()
    }
  }
}

export const conversationStateManager = new ConversationStateManager()

// Hook to consume the service
export const useConversationState = (conversationId: string) => {
  const [messages, setMessages] = useState<StoredMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    // Subscribe to updates
    const unsubscribe = conversationStateManager.subscribe(conversationId, setMessages)

    // Initial load
    const loadMessages = async () => {
      setIsLoading(true)
      setError(null)
      
      try {
        const initialMessages = await conversationStateManager.getMessages(conversationId)
        setMessages(initialMessages)
      } catch (err) {
        setError(err as Error)
      } finally {
        setIsLoading(false)
      }
    }

    loadMessages()

    return unsubscribe
  }, [conversationId])

  const addMessage = useCallback(async (message: StoredMessage) => {
    try {
      await conversationStateManager.addMessage(conversationId, message)
    } catch (err) {
      setError(err as Error)
      throw err
    }
  }, [conversationId])

  const updateMessage = useCallback(async (messageId: string, updates: Partial<StoredMessage>) => {
    try {
      await conversationStateManager.updateMessage(conversationId, messageId, updates)
    } catch (err) {
      setError(err as Error)
      throw err
    }
  }, [conversationId])

  return {
    messages,
    isLoading,
    error,
    addMessage,
    updateMessage,
    refresh: () => conversationStateManager.getMessages(conversationId, true),
  }
}
```

**Key Insights**:
- **Single source of truth**: Service layer manages all data
- **Optimistic updates**: UI responds immediately, syncs later
- **Automatic cache management**: TTL-based invalidation
- **Error recovery**: Rollback on failure

### **Pattern 4: Error Boundary State Recovery**

**Problem**: Component errors can crash the entire app and lose user data.

**Solution**: Error boundaries with state recovery and user data preservation.

```typescript
// src/components/ConversationErrorBoundary.tsx
interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorInfo: React.ErrorInfo | null
  conversationState: any // Preserved state
  recoveryAttempts: number
  lastErrorTime: Date | null
}

export class ConversationErrorBoundary extends React.Component<
  { children: React.ReactNode; conversationId: string },
  ErrorBoundaryState
> {
  private maxRecoveryAttempts = 3
  private recoveryTimeWindow = 60000 // 1 minute

  constructor(props: { children: React.ReactNode; conversationId: string }) {
    super(props)
    
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      conversationState: null,
      recoveryAttempts: 0,
      lastErrorTime: null,
    }
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
    }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    const now = new Date()
    
    // Check if we're in a recovery time window
    const withinTimeWindow = this.state.lastErrorTime && 
      (now.getTime() - this.state.lastErrorTime.getTime()) < this.recoveryTimeWindow

    const newAttempts = withinTimeWindow ? this.state.recoveryAttempts + 1 : 1

    this.setState({
      error,
      errorInfo,
      recoveryAttempts: newAttempts,
      lastErrorTime: now,
    })

    // Try to preserve conversation state
    this.preserveConversationState()

    // Log error with context
    console.error('ConversationErrorBoundary caught an error:', {
      error: error.toString(),
      errorInfo,
      conversationId: this.props.conversationId,
      recoveryAttempts: newAttempts,
      componentStack: errorInfo.componentStack,
    })

    // Report to error tracking service in production
    if (process.env.NODE_ENV === 'production') {
      this.reportError(error, errorInfo)
    }
  }

  private preserveConversationState = async () => {
    try {
      // Try to extract current conversation state
      const messages = await conversationStateManager.getMessages(this.props.conversationId)
      
      // Store in sessionStorage as backup
      const stateBackup = {
        conversationId: this.props.conversationId,
        messages: messages.slice(-10), // Last 10 messages
        timestamp: new Date().toISOString(),
        error: this.state.error?.toString(),
      }

      sessionStorage.setItem(
        `conversation-backup-${this.props.conversationId}`, 
        JSON.stringify(stateBackup)
      )

      this.setState({ conversationState: stateBackup })
    } catch (backupError) {
      console.error('Failed to preserve conversation state:', backupError)
    }
  }

  private reportError = (error: Error, errorInfo: React.ErrorInfo) => {
    // In production, send to error tracking service
    // Example: Sentry, LogRocket, etc.
  }

  private handleRecovery = () => {
    // Clear error state and attempt recovery
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    })

    // Clear any potentially corrupted cache
    conversationStateManager.clearCache(this.props.conversationId)
  }

  private handleReload = () => {
    // Preserve state and reload page
    if (this.state.conversationState) {
      localStorage.setItem('pre-reload-state', JSON.stringify({
        ...this.state.conversationState,
        shouldRestore: true,
      }))
    }
    
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      const canRetry = this.state.recoveryAttempts < this.maxRecoveryAttempts
      const hasBackup = Boolean(this.state.conversationState)

      return (
        <div className="conversation-error-boundary bg-red-50 border border-red-200 rounded-lg p-6 m-4">
          <div className="flex items-center gap-3 mb-4">
            <AlertTriangle className="w-6 h-6 text-red-600" />
            <h2 className="text-lg font-semibold text-red-800">
              Something went wrong with this conversation
            </h2>
          </div>

          <div className="text-sm text-red-700 mb-4">
            <p className="mb-2">
              We've encountered an unexpected error. Your conversation data has been preserved.
            </p>
            
            {hasBackup && (
              <div className="bg-red-100 p-3 rounded mb-3">
                <p className="font-medium mb-1">Protected Data:</p>
                <ul className="list-disc list-inside text-xs">
                  <li>Conversation ID: {this.props.conversationId}</li>
                  <li>Messages preserved: {this.state.conversationState?.messages?.length || 0}</li>
                  <li>Backup time: {this.state.conversationState?.timestamp}</li>
                </ul>
              </div>
            )}
          </div>

          <div className="flex gap-3 mb-4">
            {canRetry && (
              <button
                onClick={this.handleRecovery}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
              >
                Try Again ({this.maxRecoveryAttempts - this.state.recoveryAttempts} attempts left)
              </button>
            )}
            
            <button
              onClick={this.handleReload}
              className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
            >
              Reload Page
            </button>

            <button
              onClick={() => window.location.href = '/'}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Go to Home
            </button>
          </div>

          {/* Error details (development only) */}
          {process.env.NODE_ENV === 'development' && (
            <details className="text-xs">
              <summary className="cursor-pointer font-medium text-red-700 mb-2">
                Technical Details (Development)
              </summary>
              <div className="bg-red-100 p-3 rounded">
                <pre className="whitespace-pre-wrap overflow-auto">
                  {this.state.error?.toString()}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </div>
            </details>
          )}
        </div>
      )
    }

    return this.props.children
  }
}

// Usage in app
export const ConversationPage: React.FC<{ conversationId: string }> = ({ conversationId }) => (
  <ConversationErrorBoundary conversationId={conversationId}>
    <ConversationInterface conversationId={conversationId} />
  </ConversationErrorBoundary>
)
```

**Key Insights**:
- **Graceful degradation**: App continues working even with errors
- **State preservation**: Don't lose user data during crashes
- **Recovery mechanisms**: Multiple ways to recover from errors
- **Error reporting**: Track issues for improvement

## 🎯 **State Management Testing Patterns**

### **Testing Complex State Logic**

```typescript
// src/hooks/__tests__/useMessageActions.test.ts
import { renderHook, act } from '@testing-library/react-hooks'
import { useMessageActions } from '../useMessageActions'

describe('useMessageActions', () => {
  it('should handle message selection correctly', () => {
    const { result } = renderHook(() => useMessageActions())

    // Initial state
    expect(result.current.getSelectedCount()).toBe(0)
    expect(result.current.state.actionMode).toBe('none')

    // Select a message
    act(() => {
      result.current.selectMessage('msg-1')
    })

    expect(result.current.getSelectedCount()).toBe(1)
    expect(result.current.isMessageSelected('msg-1')).toBe(true)

    // Select multiple messages
    act(() => {
      result.current.selectMessage('msg-2')
      result.current.selectMessage('msg-3')
    })

    expect(result.current.getSelectedCount()).toBe(3)

    // Test action mode
    act(() => {
      result.current.setActionMode('copy')
    })

    expect(result.current.state.actionMode).toBe('copy')

    // Test complete action
    act(() => {
      result.current.completeAction('copy', ['msg-1', 'msg-2', 'msg-3'])
    })

    expect(result.current.getSelectedCount()).toBe(0) // Selection cleared
    expect(result.current.state.actionMode).toBe('none')
    expect(result.current.canUndo()).toBe(true)
  })

  it('should handle error states correctly', () => {
    const { result } = renderHook(() => useMessageActions())

    act(() => {
      result.current.setError('Something went wrong')
    })

    expect(result.current.state.error).toBe('Something went wrong')
    expect(result.current.state.isProcessing).toBe(false)

    act(() => {
      result.current.clearError()
    })

    expect(result.current.state.error).toBe(null)
  })

  it('should maintain action history correctly', () => {
    const { result } = renderHook(() => useMessageActions())

    // Perform multiple actions
    act(() => {
      result.current.selectMessage('msg-1')
      result.current.completeAction('copy', ['msg-1'])
    })

    act(() => {
      result.current.selectMessage('msg-2')
      result.current.completeAction('delete', ['msg-2'], { originalMessage: 'backup' })
    })

    expect(result.current.state.history).toHaveLength(2)
    expect(result.current.state.history[0].action).toBe('delete')
    expect(result.current.state.history[1].action).toBe('copy')

    // Test undo
    act(() => {
      result.current.undoLastAction()
    })

    expect(result.current.state.history).toHaveLength(1)
    expect(result.current.state.history[0].action).toBe('copy')
  })
})
```

## 🎯 **Performance Optimization Patterns**

### **Memoization Strategy**

```typescript
// Memoization patterns used throughout the app
export const OptimizedConversationList: React.FC<{
  conversations: StoredConversation[]
  onSelect: (id: string) => void
}> = ({ conversations, onSelect }) => {
  // ✅ Memoize expensive computations
  const sortedConversations = useMemo(() => {
    return conversations
      .filter(conv => !conv.archived)
      .sort((a, b) => b.lastActivity.getTime() - a.lastActivity.getTime())
  }, [conversations])

  // ✅ Memoize callback functions
  const handleSelect = useCallback((id: string) => {
    onSelect(id)
  }, [onSelect])

  // ✅ Memoize complex renders
  const conversationItems = useMemo(() => {
    return sortedConversations.map(conversation => (
      <ConversationItem
        key={conversation.id}
        conversation={conversation}
        onSelect={handleSelect}
      />
    ))
  }, [sortedConversations, handleSelect])

  return (
    <div className="conversation-list">
      {conversationItems}
    </div>
  )
}

// ✅ Memoized child component
const ConversationItem = memo<{
  conversation: StoredConversation
  onSelect: (id: string) => void
}>(({ conversation, onSelect }) => {
  const handleClick = useCallback(() => {
    onSelect(conversation.id)
  }, [conversation.id, onSelect])

  return (
    <button onClick={handleClick} className="conversation-item">
      {conversation.title}
    </button>
  )
})
```

## 🎯 **Key Architectural Decisions**

### **State Layer Responsibilities**

1. **Component State**: UI-specific state (expanded/collapsed, input values)
2. **Hook State**: Business logic state (form validation, API loading states)
3. **Service State**: Shared data state (conversations, messages, user preferences)
4. **Storage State**: Persistent state (IndexedDB, localStorage)

### **When to Use Each Pattern**

| Pattern | Use Case | Example |
|---------|----------|---------|
| **useState** | Simple UI state | Loading indicators, form inputs |
| **useReducer** | Complex coordinated state | Multi-step forms, complex interactions |
| **useRef** | Performance-critical updates | Streaming content, animation values |
| **Service Layer** | Shared data across components | Message history, user preferences |
| **Error Boundaries** | Component isolation | Chat components, third-party widgets |

### **Performance Considerations**

- **Minimize re-renders**: Use refs for high-frequency updates
- **Memoize expensive calculations**: useMemo for derived state
- **Optimize component updates**: React.memo and useCallback
- **Batch state updates**: Combine related state changes
- **Lazy load state**: Only load data when needed

## 🎯 **Key Takeaways**

1. **Layer your state management** - Different layers for different concerns
2. **Use refs for performance** - Avoid re-renders during streaming
3. **Implement error boundaries** - Protect against component crashes
4. **Design for recovery** - Always have a way to recover from errors
5. **Test complex state logic** - State machines need thorough testing
6. **Optimize selectively** - Profile before optimizing
7. **Plan for scale** - Design patterns that work with large datasets

---

**Next**: [03-component-composition-patterns.md](./03-component-composition-patterns.md) - Reusable Component Design

**Previous**: [01-component-architecture.md](./01-component-architecture.md)